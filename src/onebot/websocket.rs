// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! WebSocket-based OneBot client implementation.

use async_trait::async_trait;
use futures_util::{
    stream::{SplitSink, SplitStream},
    SinkExt, StreamExt,
};
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;
use tokio::net::TcpStream;
use tokio::sync::{mpsc, oneshot, RwLock};
use tokio_tungstenite::{
    connect_async,
    tungstenite::{client::IntoClientRequest, Message as WsMessage},
    MaybeTlsStream, WebSocketStream,
};
use uuid::Uuid;

use crate::error::AppError;
use crate::message::Message;

use super::client::{OneBotClient, OneBotResponse};

type WsStream = WebSocketStream<MaybeTlsStream<TcpStream>>;
type WsWriter = SplitSink<WsStream, WsMessage>;
type WsReader = SplitStream<WsStream>;

/// WebSocket-based OneBot V11 client
pub struct OneBotWebSocketClient {
    url: String,
    access_token: String,
    /// Pending request futures, keyed by echo ID
    pending_requests: Arc<RwLock<HashMap<String, oneshot::Sender<serde_json::Value>>>>,
    /// Channel to send messages to the WebSocket writer task
    write_tx: Arc<RwLock<Option<mpsc::Sender<String>>>>,
    /// Whether the connection is running
    running: Arc<AtomicBool>,
}

impl OneBotWebSocketClient {
    /// Create a new WebSocket client
    pub fn new(url: &str, access_token: &str) -> Self {
        Self {
            url: url.to_string(),
            access_token: access_token.to_string(),
            pending_requests: Arc::new(RwLock::new(HashMap::new())),
            write_tx: Arc::new(RwLock::new(None)),
            running: Arc::new(AtomicBool::new(false)),
        }
    }

    /// Connect to the WebSocket server with retry logic
    async fn connect(&self, max_retries: usize, retry_delay: Duration) -> Result<(), AppError> {
        let mut retries = 0;
        let mut current_delay = retry_delay;
        let max_delay = Duration::from_secs(30);

        while retries <= max_retries {
            if retries > 0 {
                tracing::info!("Attempting to reconnect WebSocket (attempt {})...", retries);
            }

            match self.try_connect().await {
                Ok(()) => {
                    tracing::info!("WebSocket connection established");
                    return Ok(());
                }
                Err(e) => {
                    retries += 1;
                    if retries > max_retries {
                        tracing::error!(
                            "WebSocket connection failed after {} retries",
                            max_retries
                        );
                        return Err(e);
                    }
                    tracing::warn!(
                        "WebSocket connection failed, retrying in {:?}: {}",
                        current_delay,
                        e
                    );
                    tokio::time::sleep(current_delay).await;
                    current_delay = std::cmp::min(
                        Duration::from_secs_f64(current_delay.as_secs_f64() * 1.5),
                        max_delay,
                    );
                }
            }
        }

        Err(AppError::Initialization(
            "Failed to establish WebSocket connection".to_string(),
        ))
    }

    /// Try to establish a WebSocket connection
    async fn try_connect(&self) -> Result<(), AppError> {
        // Build the request with authorization header
        let mut request = self
            .url
            .clone()
            .into_client_request()
            .map_err(|e| AppError::Config(format!("Failed to create request: {}", e)))?;

        if !self.access_token.is_empty() {
            request.headers_mut().insert(
                "Authorization",
                format!("Bearer {}", self.access_token)
                    .parse()
                    .map_err(|e| AppError::Config(format!("Invalid access token: {}", e)))?,
            );
        }

        let (ws_stream, _): (WsStream, _) = connect_async(request).await?;
        let (mut write, mut read): (WsWriter, WsReader) = ws_stream.split();

        // Create channel for sending messages
        let (write_tx, mut write_rx) = mpsc::channel::<String>(100);
        {
            let mut tx_guard = self.write_tx.write().await;
            *tx_guard = Some(write_tx);
        }

        self.running.store(true, Ordering::SeqCst);

        let pending = Arc::clone(&self.pending_requests);
        let running = Arc::clone(&self.running);

        // Spawn reader task
        tokio::spawn(async move {
            while running.load(Ordering::Relaxed) {
                match read.next().await {
                    Some(Ok(WsMessage::Text(text))) => {
                        if let Ok(data) = serde_json::from_str::<serde_json::Value>(&text) {
                            if let Some(echo) = data.get("echo").and_then(|e| e.as_str()) {
                                let mut pending = pending.write().await;
                                if let Some(tx) = pending.remove(echo) {
                                    let _ = tx.send(data);
                                }
                            } else {
                                tracing::debug!(
                                    "Received message without echo or unmatched echo: {}",
                                    text
                                );
                            }
                        }
                    }
                    Some(Ok(WsMessage::Close(_))) => {
                        tracing::warn!("WebSocket connection closed by server");
                        break;
                    }
                    Some(Err(e)) => {
                        tracing::error!("WebSocket read error: {}", e);
                        break;
                    }
                    None => break,
                    _ => {}
                }
            }
            running.store(false, Ordering::SeqCst);
            tracing::info!("WebSocket reader task ended");
        });

        // Spawn writer task
        let running_writer = Arc::clone(&self.running);
        tokio::spawn(async move {
            while let Some(msg) = write_rx.recv().await {
                if let Err(e) = write.send(WsMessage::Text(msg.into())).await {
                    tracing::error!("WebSocket write error: {}", e);
                    running_writer.store(false, Ordering::SeqCst);
                    break;
                }
            }
            tracing::info!("WebSocket writer task ended");
        });

        Ok(())
    }

    /// Send a request and wait for response
    async fn send_request(
        &self,
        mut request: serde_json::Value,
        timeout: Duration,
    ) -> Result<OneBotResponse, AppError> {
        if !self.running.load(Ordering::Relaxed) {
            return Err(AppError::ConnectionNotAvailable);
        }

        let echo_id = Uuid::new_v4().to_string();
        request["echo"] = serde_json::Value::String(echo_id.clone());

        let (tx, rx) = oneshot::channel();

        // Register the pending request
        {
            let mut pending = self.pending_requests.write().await;
            pending.insert(echo_id.clone(), tx);
        }

        // Send the request
        let write_tx = {
            let guard = self.write_tx.read().await;
            guard.clone()
        };

        let write_tx = write_tx.ok_or(AppError::ConnectionNotAvailable)?;
        let json_str = serde_json::to_string(&request)?;

        write_tx
            .send(json_str)
            .await
            .map_err(|_| AppError::Channel("Failed to send to writer".to_string()))?;

        // Wait for response with timeout
        match tokio::time::timeout(timeout, rx).await {
            Ok(Ok(response)) => {
                let resp: OneBotResponse = serde_json::from_value(response)?;
                Ok(resp)
            }
            Ok(Err(_)) => {
                // Channel closed
                let mut pending = self.pending_requests.write().await;
                pending.remove(&echo_id);
                Err(AppError::Channel("Response channel closed".to_string()))
            }
            Err(_) => {
                // Timeout
                let mut pending = self.pending_requests.write().await;
                pending.remove(&echo_id);
                tracing::error!("Request timeout: {}", echo_id);
                Ok(OneBotResponse {
                    status: "error".to_string(),
                    retcode: -1,
                    message: Some("Request timeout".to_string()),
                    data: None,
                    echo: Some(echo_id),
                })
            }
        }
    }
}

#[async_trait]
impl OneBotClient for OneBotWebSocketClient {
    async fn send_message(
        &self,
        message_type: &str,
        target_id: i64,
        message: Message,
        auto_escape: bool,
    ) -> Result<OneBotResponse, AppError> {
        if message_type != "group" && message_type != "private" {
            return Ok(OneBotResponse {
                status: "error".to_string(),
                retcode: -1,
                message: Some(format!("Unsupported message type: {}", message_type)),
                data: None,
                echo: None,
            });
        }

        let mut params = serde_json::json!({
            "message_type": message_type,
            "message": message,
            "auto_escape": auto_escape,
        });

        if message_type == "group" {
            params["group_id"] = serde_json::json!(target_id);
        } else {
            params["user_id"] = serde_json::json!(target_id);
        }

        let request = serde_json::json!({
            "action": "send_msg",
            "params": params,
        });

        self.send_request(request, Duration::from_secs(30)).await
    }

    async fn start(&self) -> Result<(), AppError> {
        self.connect(5, Duration::from_secs(2)).await
    }

    async fn shutdown(&self) -> Result<(), AppError> {
        self.running.store(false, Ordering::SeqCst);

        // Clear pending requests
        let mut pending = self.pending_requests.write().await;
        pending.clear();

        // Clear write channel
        let mut write_tx = self.write_tx.write().await;
        *write_tx = None;

        tracing::info!("WebSocket connection closed");
        Ok(())
    }
}
