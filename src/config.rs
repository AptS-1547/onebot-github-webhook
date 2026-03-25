// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! Configuration models and loading logic.

use serde::{Deserialize, Serialize};
use std::path::Path;

use crate::error::AppError;

/// OneBot target type (group or private chat)
#[derive(Debug, Clone, Copy, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum TargetType {
    Private,
    Group,
}

/// OneBot message target
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct OnebotTarget {
    #[serde(rename = "type")]
    pub target_type: TargetType,
    pub id: i64,
}

/// Protocol type for OneBot connection
#[derive(Debug, Clone, Copy, Deserialize, Serialize, Default, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum ProtocolType {
    #[default]
    Ws,
    Http,
}

/// Webhook configuration for a specific repository/branch pattern
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "UPPERCASE")]
pub struct WebhookConfig {
    pub name: String,
    pub repo: Vec<String>,
    pub branch: Vec<String>,
    pub secret: String,
    pub events: Vec<String>,
    pub onebot: Vec<OnebotTarget>,
}

/// Main application configuration
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "UPPERCASE")]
pub struct Config {
    #[serde(default = "default_env")]
    pub env: String,

    #[serde(default)]
    pub onebot_url: String,

    #[serde(default, alias = "ONEBOT_TYPE")]
    pub onebot_protocol_type: ProtocolType,

    #[serde(default)]
    pub onebot_access_token: String,

    #[serde(default)]
    pub github_webhook: Vec<WebhookConfig>,
}

fn default_env() -> String {
    "production".to_string()
}

impl Config {
    /// Load configuration from a TOML file
    pub fn from_toml<P: AsRef<Path>>(path: P) -> Result<Self, AppError> {
        let path = path.as_ref();

        if !path.exists() {
            tracing::warn!("Config file {:?} does not exist, using defaults", path);
            return Ok(Self::default());
        }

        let content = std::fs::read_to_string(path)?;
        let config: Config = toml::from_str(&content)?;

        // Validate URL format
        config.validate()?;

        Ok(config)
    }

    /// Validate configuration
    fn validate(&self) -> Result<(), AppError> {
        if !self.onebot_url.is_empty() {
            match self.onebot_protocol_type {
                ProtocolType::Ws => {
                    if !self.onebot_url.starts_with("ws://")
                        && !self.onebot_url.starts_with("wss://")
                    {
                        return Err(AppError::Config(
                            "ONEBOT_URL must start with 'ws://' or 'wss://' when protocol is ws"
                                .to_string(),
                        ));
                    }
                }
                ProtocolType::Http => {
                    if !self.onebot_url.starts_with("http://")
                        && !self.onebot_url.starts_with("https://")
                    {
                        return Err(AppError::Config(
                            "ONEBOT_URL must start with 'http://' or 'https://' when protocol is http"
                                .to_string(),
                        ));
                    }
                }
            }
        }

        Ok(())
    }
}

impl Default for Config {
    fn default() -> Self {
        Self {
            env: default_env(),
            onebot_url: String::new(),
            onebot_protocol_type: ProtocolType::Ws,
            onebot_access_token: String::new(),
            github_webhook: vec![],
        }
    }
}
