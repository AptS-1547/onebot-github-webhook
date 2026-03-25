// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! GitHub webhook payload data structures.

use serde::{Deserialize, Serialize};

/// Common repository information
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Repository {
    pub full_name: String,
    #[serde(default)]
    pub html_url: Option<String>,
}

/// Common sender information
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Sender {
    pub login: String,
}

/// Commit author information
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct CommitAuthor {
    #[serde(default)]
    pub name: Option<String>,
}

/// Commit information for push events
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Commit {
    pub id: String,
    pub message: String,
    #[serde(default)]
    pub author: Option<CommitAuthor>,
}

/// Pusher information
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Pusher {
    pub name: String,
}

/// Branch reference
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct BranchRef {
    #[serde(rename = "ref")]
    pub branch_ref: String,
}

/// Pull request information
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct PullRequest {
    pub number: i64,
    pub title: String,
    pub state: String,
    #[serde(default)]
    pub html_url: Option<String>,
    #[serde(default)]
    pub merged: Option<bool>,
    #[serde(default)]
    pub base: Option<BranchRef>,
    #[serde(default)]
    pub head: Option<BranchRef>,
}

/// Issue label
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Label {
    pub name: String,
}

/// Issue information
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Issue {
    pub number: i64,
    pub title: String,
    pub state: String,
    #[serde(default)]
    pub html_url: Option<String>,
    #[serde(default)]
    pub labels: Vec<Label>,
}

/// Release information
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Release {
    #[serde(default)]
    pub tag_name: Option<String>,
    #[serde(default)]
    pub name: Option<String>,
    #[serde(default)]
    pub prerelease: Option<bool>,
    #[serde(default)]
    pub published_at: Option<String>,
    #[serde(default)]
    pub html_url: Option<String>,
}

/// Comment information
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Comment {
    #[serde(default)]
    pub body: Option<String>,
    #[serde(default)]
    pub html_url: Option<String>,
    #[serde(default)]
    pub pull_request: Option<serde_json::Value>,
}

/// Extracted push event data
#[derive(Debug, Clone)]
pub struct PushData {
    pub repo_name: String,
    pub branch: String,
    pub pusher: String,
    pub commits: Vec<Commit>,
    pub commit_count: usize,
}

/// Extracted pull request event data
#[derive(Debug, Clone)]
pub struct PullRequestData {
    pub repo_name: String,
    pub action: String,
    pub pull_request: PullRequest,
    pub user: String,
}

/// Extracted issue event data
#[derive(Debug, Clone)]
pub struct IssueData {
    pub repo_name: String,
    pub action: String,
    pub issue: Issue,
    pub user: String,
}

/// Extracted release event data
#[derive(Debug, Clone)]
pub struct ReleaseData {
    pub repo_name: String,
    pub action: String,
    pub release: Release,
    pub user: String,
}

/// Extracted issue comment event data
#[derive(Debug, Clone)]
pub struct IssueCommentData {
    pub repo_name: String,
    pub action: String,
    pub issue_number: i64,
    pub comment: Comment,
    pub user: String,
}

/// Extract push event data from payload
pub fn extract_push_data(payload: &serde_json::Value) -> PushData {
    let repo_name = payload
        .get("repository")
        .and_then(|r| r.get("full_name"))
        .and_then(|n| n.as_str())
        .unwrap_or("")
        .to_string();

    let branch = payload
        .get("ref")
        .and_then(|r| r.as_str())
        .unwrap_or("")
        .replace("refs/heads/", "");

    let pusher = payload
        .get("pusher")
        .and_then(|p| p.get("name"))
        .and_then(|n| n.as_str())
        .unwrap_or("")
        .to_string();

    let commits: Vec<Commit> = payload
        .get("commits")
        .and_then(|c| serde_json::from_value(c.clone()).ok())
        .unwrap_or_default();

    let commit_count = commits.len();

    PushData {
        repo_name,
        branch,
        pusher,
        commits,
        commit_count,
    }
}

/// Extract pull request event data from payload
pub fn extract_pull_request_data(payload: &serde_json::Value) -> PullRequestData {
    let repo_name = payload
        .get("repository")
        .and_then(|r| r.get("full_name"))
        .and_then(|n| n.as_str())
        .unwrap_or("")
        .to_string();

    let action = payload
        .get("action")
        .and_then(|a| a.as_str())
        .unwrap_or("")
        .to_string();

    let pull_request: PullRequest = payload
        .get("pull_request")
        .and_then(|pr| serde_json::from_value(pr.clone()).ok())
        .unwrap_or(PullRequest {
            number: 0,
            title: String::new(),
            state: String::new(),
            html_url: None,
            merged: None,
            base: None,
            head: None,
        });

    let user = payload
        .get("sender")
        .and_then(|s| s.get("login"))
        .and_then(|l| l.as_str())
        .unwrap_or("")
        .to_string();

    PullRequestData {
        repo_name,
        action,
        pull_request,
        user,
    }
}

/// Extract issue event data from payload
pub fn extract_issue_data(payload: &serde_json::Value) -> IssueData {
    let repo_name = payload
        .get("repository")
        .and_then(|r| r.get("full_name"))
        .and_then(|n| n.as_str())
        .unwrap_or("")
        .to_string();

    let action = payload
        .get("action")
        .and_then(|a| a.as_str())
        .unwrap_or("")
        .to_string();

    let issue: Issue = payload
        .get("issue")
        .and_then(|i| serde_json::from_value(i.clone()).ok())
        .unwrap_or(Issue {
            number: 0,
            title: String::new(),
            state: String::new(),
            html_url: None,
            labels: vec![],
        });

    let user = payload
        .get("sender")
        .and_then(|s| s.get("login"))
        .and_then(|l| l.as_str())
        .unwrap_or("")
        .to_string();

    IssueData {
        repo_name,
        action,
        issue,
        user,
    }
}

/// Extract release event data from payload
pub fn extract_release_data(payload: &serde_json::Value) -> ReleaseData {
    let repo_name = payload
        .get("repository")
        .and_then(|r| r.get("full_name"))
        .and_then(|n| n.as_str())
        .unwrap_or("")
        .to_string();

    let action = payload
        .get("action")
        .and_then(|a| a.as_str())
        .unwrap_or("")
        .to_string();

    let release: Release = payload
        .get("release")
        .and_then(|r| serde_json::from_value(r.clone()).ok())
        .unwrap_or(Release {
            tag_name: None,
            name: None,
            prerelease: None,
            published_at: None,
            html_url: None,
        });

    let user = payload
        .get("sender")
        .and_then(|s| s.get("login"))
        .and_then(|l| l.as_str())
        .unwrap_or("")
        .to_string();

    ReleaseData {
        repo_name,
        action,
        release,
        user,
    }
}

/// Extract issue comment event data from payload
pub fn extract_issue_comment_data(payload: &serde_json::Value) -> IssueCommentData {
    let repo_name = payload
        .get("repository")
        .and_then(|r| r.get("full_name"))
        .and_then(|n| n.as_str())
        .unwrap_or("")
        .to_string();

    let action = payload
        .get("action")
        .and_then(|a| a.as_str())
        .unwrap_or("")
        .to_string();

    let issue_number = payload
        .get("issue")
        .and_then(|i| i.get("number"))
        .and_then(|n| n.as_i64())
        .unwrap_or(0);

    let comment: Comment = payload
        .get("comment")
        .and_then(|c| serde_json::from_value(c.clone()).ok())
        .unwrap_or(Comment {
            body: None,
            html_url: None,
            pull_request: None,
        });

    let user = payload
        .get("sender")
        .and_then(|s| s.get("login"))
        .and_then(|l| l.as_str())
        .unwrap_or("")
        .to_string();

    IssueCommentData {
        repo_name,
        action,
        issue_number,
        comment,
        user,
    }
}
