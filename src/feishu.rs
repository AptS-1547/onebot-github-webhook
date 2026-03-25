// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! Feishu (Lark) webhook bot client.

use base64::{engine::general_purpose::STANDARD, Engine};
use hmac::{Hmac, Mac};
use reqwest::Client;
use serde_json::{json, Value};
use sha2::Sha256;
use std::time::{SystemTime, UNIX_EPOCH};

use crate::config::FeishuConfig;
use crate::error::AppError;

type HmacSha256 = Hmac<Sha256>;

pub struct FeishuClient {
    config: FeishuConfig,
    client: Client,
}

impl FeishuClient {
    pub fn new(config: FeishuConfig) -> Self {
        Self {
            config,
            client: Client::new(),
        }
    }

    pub fn name(&self) -> &str {
        &self.config.name
    }

    /// Build an interactive card payload from plain text.
    fn build_card_payload(&self, text: &str, timestamp: i64, sign: Option<String>) -> Value {
        let mut payload = json!({
            "msg_type": "interactive",
            "card": {
                "schema": "2.0",
                "body": {
                    "elements": [
                        {
                            "tag": "markdown",
                            "content": text
                        }
                    ]
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "GitHub 事件通知"
                    },
                    "template": "blue"
                }
            }
        });

        if let Some(sig) = sign {
            payload["timestamp"] = json!(timestamp.to_string());
            payload["sign"] = json!(sig);
        }

        payload
    }

    /// Compute Feishu webhook signature: HMAC-SHA256(timestamp + "\n" + secret), base64 encoded.
    fn compute_sign(&self, timestamp: i64) -> Option<String> {
        if self.config.secret.is_empty() {
            return None;
        }
        let data = format!("{}\n{}", timestamp, self.config.secret);
        let mut mac = HmacSha256::new_from_slice(self.config.secret.as_bytes())
            .expect("HMAC accepts any key length");
        mac.update(data.as_bytes());
        let result = mac.finalize().into_bytes();
        Some(STANDARD.encode(result))
    }

    pub async fn send(&self, text: &str) -> Result<(), AppError> {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs() as i64;

        let sign = self.compute_sign(timestamp);
        let payload = self.build_card_payload(text, timestamp, sign);

        let resp = self
            .client
            .post(&self.config.webhook_url)
            .json(&payload)
            .send()
            .await
            .map_err(AppError::Http)?;

        if !resp.status().is_success() {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            return Err(AppError::Config(format!(
                "Feishu webhook returned {}: {}",
                status, body
            )));
        }

        let body: Value = resp.json().await.map_err(AppError::Http)?;
        if body["code"].as_i64().unwrap_or(0) != 0 {
            return Err(AppError::Config(format!(
                "Feishu webhook error: {}",
                body["msg"].as_str().unwrap_or("unknown")
            )));
        }

        tracing::info!("Feishu message sent via '{}'", self.config.name);
        Ok(())
    }
}
