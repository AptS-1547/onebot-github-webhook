// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! OneBot GitHub Webhook Server - Main entry point.

use std::sync::Arc;

use axum::{routing::post, Router};
use tower_http::trace::TraceLayer;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use onebot_github_webhook::{
    config::Config,
    onebot::create_client,
    routes::github_webhook,
    AppState,
};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize logging
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    tracing::info!("Starting OneBot GitHub Webhook Server...");

    // Load configuration
    let config = Config::from_yaml("config.yaml")?;
    tracing::info!("Configuration loaded: env={}", config.env);
    tracing::info!(
        "OneBot URL: {}, Protocol: {:?}",
        config.onebot_url,
        config.onebot_protocol_type
    );
    tracing::info!(
        "Configured {} webhook(s)",
        config.github_webhook.len()
    );

    // Initialize OneBot client
    let onebot_client = create_client(&config).await?;
    tracing::info!("OneBot client initialized");

    // Build application state
    let state = Arc::new(AppState {
        config,
        onebot_client,
    });

    // Build router
    let app = Router::new()
        .route("/github-webhook", post(github_webhook))
        .layer(TraceLayer::new_for_http())
        .with_state(state.clone());

    // Start server
    let listener = tokio::net::TcpListener::bind("0.0.0.0:8000").await?;
    tracing::info!("Server listening on 0.0.0.0:8000");

    // Run with graceful shutdown
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    // Cleanup
    tracing::info!("Shutting down...");
    state.onebot_client.shutdown().await?;
    tracing::info!("Goodbye!");

    Ok(())
}

async fn shutdown_signal() {
    let ctrl_c = async {
        tokio::signal::ctrl_c()
            .await
            .expect("Failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .expect("Failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        () = ctrl_c => {},
        () = terminate => {},
    }

    tracing::info!("Shutdown signal received");
}
