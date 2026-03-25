// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! OneBot client trait and factory.

use async_trait::async_trait;
use std::sync::Arc;

use crate::config::{Config, ProtocolType};
use crate::error::AppError;
use crate::message::Message;

use super::{OneBotHttpClient, OneBotWebSocketClient};

/// Response from OneBot API
#[derive(Debug, Clone, serde::Deserialize, serde::Serialize)]
pub struct OneBotResponse {
    pub status: String,
    pub retcode: i32,
    #[serde(default)]
    pub message: Option<String>,
    #[serde(default)]
    pub data: Option<serde_json::Value>,
    #[serde(default)]
    pub echo: Option<String>,
}

/// Trait for OneBot client implementations
#[async_trait]
pub trait OneBotClient: Send + Sync {
    /// Send a message to a group or private chat
    async fn send_message(
        &self,
        message_type: &str,
        target_id: i64,
        message: Message,
        auto_escape: bool,
    ) -> Result<OneBotResponse, AppError>;

    /// Start the client (for WebSocket, this establishes the connection)
    async fn start(&self) -> Result<(), AppError>;

    /// Shutdown the client
    async fn shutdown(&self) -> Result<(), AppError>;
}

/// Create an OneBot client based on configuration
pub async fn create_client(config: &Config) -> Result<Arc<dyn OneBotClient>, AppError> {
    let client: Arc<dyn OneBotClient> = match config.onebot_protocol_type {
        ProtocolType::Http => Arc::new(OneBotHttpClient::new(
            &config.onebot_url,
            &config.onebot_access_token,
        )),
        ProtocolType::Ws => {
            let ws_client = OneBotWebSocketClient::new(
                &config.onebot_url,
                &config.onebot_access_token,
            );
            ws_client.start().await?;
            Arc::new(ws_client)
        }
    };

    Ok(client)
}
