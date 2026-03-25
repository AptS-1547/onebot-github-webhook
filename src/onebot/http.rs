// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! HTTP-based OneBot client implementation.

use async_trait::async_trait;
use reqwest::Client;

use crate::error::AppError;
use crate::message::Message;

use super::client::{OneBotClient, OneBotResponse};

/// HTTP-based OneBot V11 client
pub struct OneBotHttpClient {
    url: String,
    access_token: String,
    client: Client,
}

impl OneBotHttpClient {
    /// Create a new HTTP client
    pub fn new(url: &str, access_token: &str) -> Self {
        Self {
            url: url.to_string(),
            access_token: access_token.to_string(),
            client: Client::new(),
        }
    }

    fn build_headers(&self) -> reqwest::header::HeaderMap {
        let mut headers = reqwest::header::HeaderMap::new();
        headers.insert(
            reqwest::header::CONTENT_TYPE,
            "application/json".parse().unwrap(),
        );
        if !self.access_token.is_empty() {
            headers.insert(
                reqwest::header::AUTHORIZATION,
                format!("Bearer {}", self.access_token).parse().unwrap(),
            );
        }
        headers
    }
}

#[async_trait]
impl OneBotClient for OneBotHttpClient {
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

        let mut request = serde_json::json!({
            "message_type": message_type,
            "message": message,
            "auto_escape": auto_escape,
        });

        if message_type == "group" {
            request["group_id"] = serde_json::json!(target_id);
        } else {
            request["user_id"] = serde_json::json!(target_id);
        }

        let response = self
            .client
            .post(format!("{}/send_msg", self.url))
            .headers(self.build_headers())
            .json(&request)
            .send()
            .await?;

        if response.status() != reqwest::StatusCode::OK {
            tracing::error!("HTTP request failed with status: {}", response.status());
            return Ok(OneBotResponse {
                status: "error".to_string(),
                retcode: -1,
                message: Some(format!("HTTP error: {}", response.status())),
                data: None,
                echo: None,
            });
        }

        let data: OneBotResponse = response.json().await?;
        Ok(data)
    }

    async fn start(&self) -> Result<(), AppError> {
        // HTTP client doesn't need explicit start
        Ok(())
    }

    async fn shutdown(&self) -> Result<(), AppError> {
        // HTTP client doesn't need explicit shutdown
        Ok(())
    }
}
