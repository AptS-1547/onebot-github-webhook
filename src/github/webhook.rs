// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! GitHub webhook signature verification and configuration matching.

use hmac::{Hmac, Mac};
use sha2::Sha256;

use crate::config::WebhookConfig;
use crate::error::AppError;
use crate::matching::match_any_pattern;

type HmacSha256 = Hmac<Sha256>;

/// Verify the GitHub webhook signature.
///
/// Returns Ok(()) if signature is valid, or Err if invalid/missing.
/// If no secret is configured for the repo, signature verification is skipped.
pub fn verify_signature(
    body: &[u8],
    signature_header: Option<&str>,
    repo_name: &str,
    webhooks: &[WebhookConfig],
) -> Result<(), AppError> {
    // Find the secret for this repo
    let webhook_secret = webhooks
        .iter()
        .find(|w| match_any_pattern(repo_name, &w.repo))
        .map(|w| &w.secret);

    let secret = match webhook_secret {
        Some(s) if !s.is_empty() => s,
        _ => {
            tracing::warn!(
                "No webhook secret configured for repo {}, skipping signature verification",
                repo_name
            );
            return Ok(());
        }
    };

    let signature = signature_header.ok_or(AppError::MissingSignature)?;

    // Parse "sha256=xxx" format
    let signature = signature
        .strip_prefix("sha256=")
        .ok_or(AppError::InvalidSignature)?;

    // Calculate expected signature
    let mut mac = HmacSha256::new_from_slice(secret.as_bytes())
        .map_err(|_| AppError::InvalidSignature)?;
    mac.update(body);
    let expected = hex::encode(mac.finalize().into_bytes());

    // Constant-time comparison to prevent timing attacks
    if constant_time_eq::constant_time_eq(expected.as_bytes(), signature.as_bytes()) {
        Ok(())
    } else {
        Err(AppError::InvalidSignature)
    }
}

/// Find a matching webhook configuration for the given repo, branch, and event type.
pub fn find_matching_webhook<'a>(
    repo_name: &str,
    branch: &str,
    event_type: &str,
    webhooks: &'a [WebhookConfig],
) -> Option<&'a WebhookConfig> {
    tracing::debug!(
        "Finding matching webhook: repo={}, branch={}, event={}",
        repo_name,
        branch,
        event_type
    );

    for webhook in webhooks {
        // Check repo pattern
        if !match_any_pattern(repo_name, &webhook.repo) {
            continue;
        }

        // Check event type
        if !webhook.events.iter().any(|e| e == event_type) {
            continue;
        }

        // For push and pull_request events, check branch pattern
        if event_type == "push" || event_type == "pull_request" {
            if !match_any_pattern(branch, &webhook.branch) {
                continue;
            }
        }

        tracing::debug!("Found matching webhook: {}", webhook.name);
        return Some(webhook);
    }

    tracing::debug!("No matching webhook found");
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{OnebotTarget, TargetType};

    fn create_test_webhook(name: &str, repos: Vec<&str>, branches: Vec<&str>, events: Vec<&str>) -> WebhookConfig {
        WebhookConfig {
            name: name.to_string(),
            repo: repos.into_iter().map(String::from).collect(),
            branch: branches.into_iter().map(String::from).collect(),
            secret: "test_secret".to_string(),
            events: events.into_iter().map(String::from).collect(),
            onebot: vec![OnebotTarget {
                target_type: TargetType::Group,
                id: 123456,
            }],
        }
    }

    #[test]
    fn test_find_matching_webhook_exact() {
        let webhooks = vec![create_test_webhook(
            "test",
            vec!["user/repo"],
            vec!["main"],
            vec!["push"],
        )];

        let result = find_matching_webhook("user/repo", "main", "push", &webhooks);
        assert!(result.is_some());
        assert_eq!(result.unwrap().name, "test");
    }

    #[test]
    fn test_find_matching_webhook_wildcard() {
        let webhooks = vec![create_test_webhook(
            "test",
            vec!["user/*"],
            vec!["*"],
            vec!["push"],
        )];

        let result = find_matching_webhook("user/any-repo", "feature/xyz", "push", &webhooks);
        assert!(result.is_some());
    }

    #[test]
    fn test_find_matching_webhook_no_match() {
        let webhooks = vec![create_test_webhook(
            "test",
            vec!["user/repo"],
            vec!["main"],
            vec!["push"],
        )];

        // Wrong repo
        assert!(find_matching_webhook("other/repo", "main", "push", &webhooks).is_none());
        // Wrong branch
        assert!(find_matching_webhook("user/repo", "develop", "push", &webhooks).is_none());
        // Wrong event
        assert!(find_matching_webhook("user/repo", "main", "issues", &webhooks).is_none());
    }

    #[test]
    fn test_verify_signature_valid() {
        use hmac::Mac;

        let body = b"test payload";
        let secret = "test_secret";

        let mut mac = HmacSha256::new_from_slice(secret.as_bytes()).unwrap();
        mac.update(body);
        let signature = format!("sha256={}", hex::encode(mac.finalize().into_bytes()));

        let webhooks = vec![create_test_webhook("test", vec!["user/repo"], vec!["main"], vec!["push"])];

        let result = verify_signature(body, Some(&signature), "user/repo", &webhooks);
        assert!(result.is_ok());
    }

    #[test]
    fn test_verify_signature_invalid() {
        let body = b"test payload";
        let webhooks = vec![create_test_webhook("test", vec!["user/repo"], vec!["main"], vec!["push"])];

        let result = verify_signature(body, Some("sha256=invalid"), "user/repo", &webhooks);
        assert!(result.is_err());
    }
}
