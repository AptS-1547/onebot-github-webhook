// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! OneBot GitHub Webhook - A bridge service from GitHub webhooks to OneBot.

pub mod config;
pub mod error;
pub mod feishu;
pub mod github;
pub mod matching;
pub mod message;
pub mod onebot;
pub mod routes;

use std::sync::Arc;

use config::Config;
use onebot::OneBotClient;

/// Application state shared across handlers
pub struct AppState {
    pub config: Config,
    pub onebot_client: Arc<dyn OneBotClient>,
}
