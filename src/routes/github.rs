// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! GitHub webhook route handler.

use axum::{
    body::Bytes,
    extract::State,
    http::{HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use std::sync::Arc;

use crate::config::TargetType;
use crate::github::formatter::{
    format_issue_comment_message, format_issue_message, format_pull_request_message,
    format_push_message, format_release_message,
};
use crate::github::payload::{
    extract_issue_comment_data, extract_issue_data, extract_pull_request_data, extract_push_data,
    extract_release_data,
};
use crate::github::webhook::{find_matching_webhook, verify_signature};
use crate::AppState;

/// Handle GitHub webhook requests
pub async fn github_webhook(
    State(state): State<Arc<AppState>>,
    headers: HeaderMap,
    body: Bytes,
) -> impl IntoResponse {
    // Check Content-Type
    let content_type = headers
        .get("content-type")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("");

    if !content_type.contains("application/json") {
        return (
            StatusCode::OK,
            Json(serde_json::json!({
                "status": "ignored",
                "message": "只处理 application/json 格式的请求"
            })),
        );
    }

    // Get event type
    let event_type = match headers.get("x-github-event").and_then(|v| v.to_str().ok()) {
        Some(e) => e.to_string(),
        None => {
            return (
                StatusCode::OK,
                Json(serde_json::json!({
                    "status": "ignored",
                    "message": "缺少 X-GitHub-Event 头"
                })),
            );
        }
    };

    // Parse payload
    let payload: serde_json::Value = match serde_json::from_slice(&body) {
        Ok(p) => p,
        Err(e) => {
            tracing::error!("Failed to parse JSON payload: {}", e);
            return (
                StatusCode::BAD_REQUEST,
                Json(serde_json::json!({
                    "status": "error",
                    "message": "Invalid JSON payload"
                })),
            );
        }
    };

    // Get repo name
    let repo_name = payload
        .get("repository")
        .and_then(|r| r.get("full_name"))
        .and_then(|n| n.as_str())
        .unwrap_or("");

    // Verify signature
    let signature = headers
        .get("x-hub-signature-256")
        .and_then(|v| v.to_str().ok());

    if let Err(e) = verify_signature(&body, signature, repo_name, &state.config.github_webhook) {
        tracing::warn!("Signature verification failed: {}", e);
        return (
            StatusCode::OK,
            Json(serde_json::json!({
                "status": "ignored",
                "message": format!("签名验证失败: {}", e)
            })),
        );
    }

    // Get branch for matching
    let branch = if event_type == "push" {
        payload
            .get("ref")
            .and_then(|r| r.as_str())
            .unwrap_or("")
            .replace("refs/heads/", "")
    } else if event_type == "pull_request" {
        payload
            .get("pull_request")
            .and_then(|pr| pr.get("base"))
            .and_then(|base| base.get("ref"))
            .and_then(|r| r.as_str())
            .unwrap_or("")
            .to_string()
    } else {
        String::new()
    };

    // Find matching webhook
    let matched_webhook = match find_matching_webhook(
        repo_name,
        &branch,
        &event_type,
        &state.config.github_webhook,
    ) {
        Some(w) => w,
        None => {
            tracing::info!(
                "No matching webhook config for repo={}, event={}",
                repo_name,
                event_type
            );
            return (
                StatusCode::OK,
                Json(serde_json::json!({
                    "status": "ignored",
                    "message": "找不到匹配的 webhook 配置"
                })),
            );
        }
    };

    // Process different event types
    let message = match event_type.as_str() {
        "push" => {
            let data = extract_push_data(&payload);
            tracing::info!(
                "Push event: repo={}, branch={}, pusher={}, commits={}",
                data.repo_name,
                data.branch,
                data.pusher,
                data.commit_count
            );
            Some(format_push_message(&data))
        }
        "pull_request" => {
            let data = extract_pull_request_data(&payload);
            tracing::info!(
                "PR event: repo={}, PR #{}, action={}, user={}",
                data.repo_name,
                data.pull_request.number,
                data.action,
                data.user
            );
            Some(format_pull_request_message(&data))
        }
        "issues" => {
            let data = extract_issue_data(&payload);
            tracing::info!(
                "Issue event: repo={}, Issue #{}, action={}, user={}",
                data.repo_name,
                data.issue.number,
                data.action,
                data.user
            );
            Some(format_issue_message(&data))
        }
        "release" => {
            let data = extract_release_data(&payload);
            tracing::info!(
                "Release event: repo={}, tag={:?}, action={}, user={}",
                data.repo_name,
                data.release.tag_name,
                data.action,
                data.user
            );
            Some(format_release_message(&data))
        }
        "issue_comment" => {
            let data = extract_issue_comment_data(&payload);
            tracing::info!(
                "Issue comment event: repo={}, Issue #{}, action={}, user={}",
                data.repo_name,
                data.issue_number,
                data.action,
                data.user
            );
            Some(format_issue_comment_message(&data))
        }
        _ => {
            tracing::info!("Unsupported event type: {}", event_type);
            return (
                StatusCode::OK,
                Json(serde_json::json!({
                    "status": "ignored",
                    "message": format!("暂不处理 {} 类型的事件", event_type)
                })),
            );
        }
    };

    // Send messages to all targets
    if let Some(msg) = message {
        for target in &matched_webhook.onebot {
            let message_type = match target.target_type {
                TargetType::Group => "group",
                TargetType::Private => "private",
            };

            tracing::info!(
                "Sending message to {} {}",
                message_type,
                target.id
            );

            match state
                .onebot_client
                .send_message(message_type, target.id, msg.clone(), false)
                .await
            {
                Ok(resp) => {
                    if resp.retcode != 0 {
                        tracing::warn!(
                            "OneBot API returned error: {:?}",
                            resp.message
                        );
                    }
                }
                Err(e) => {
                    tracing::error!("Failed to send message: {}", e);
                }
            }
        }

        return (
            StatusCode::OK,
            Json(serde_json::json!({
                "status": "success",
                "message": format!("处理 {} 事件成功", event_type)
            })),
        );
    }

    (
        StatusCode::OK,
        Json(serde_json::json!({
            "status": "failed",
            "message": "处理事件时发生错误"
        })),
    )
}
