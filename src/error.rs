// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! Error types for the application.

use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use thiserror::Error;

/// Application error types
#[derive(Error, Debug)]
pub enum AppError {
    #[error("Configuration error: {0}")]
    Config(String),

    #[error("WebSocket error: {0}")]
    WebSocket(#[from] tokio_tungstenite::tungstenite::Error),

    #[error("HTTP client error: {0}")]
    Http(#[from] reqwest::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("TOML error: {0}")]
    Toml(#[from] toml::de::Error),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Invalid signature")]
    InvalidSignature,

    #[error("Missing signature header")]
    MissingSignature,

    #[error("Initialization failed: {0}")]
    Initialization(String),

    #[error("Connection timeout")]
    Timeout,

    #[error("No matching webhook configuration")]
    NoMatchingWebhook,

    #[error("WebSocket connection not available")]
    ConnectionNotAvailable,

    #[error("Channel error: {0}")]
    Channel(String),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message) = match &self {
            AppError::InvalidSignature => (StatusCode::UNAUTHORIZED, self.to_string()),
            AppError::MissingSignature => (StatusCode::UNAUTHORIZED, self.to_string()),
            AppError::NoMatchingWebhook => (StatusCode::OK, self.to_string()),
            _ => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
        };

        (
            status,
            Json(serde_json::json!({
                "status": "error",
                "message": message
            })),
        )
            .into_response()
    }
}
