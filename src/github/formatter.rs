// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! Message formatting for GitHub events.

use crate::github::payload::{
    IssueCommentData, IssueData, PullRequestData, PushData, ReleaseData,
};
use crate::message::{Message, MessageSegment};

/// Format a push event message
pub fn format_push_message(data: &PushData) -> Message {
    let mut message = vec![
        MessageSegment::text("📢 GitHub 推送通知\n"),
        MessageSegment::text(format!("仓库：{}\n", data.repo_name)),
        MessageSegment::text(format!("分支：{}\n", data.branch)),
        MessageSegment::text(format!("推送者：{}\n", data.pusher)),
        MessageSegment::text(format!("提交数量：{}\n\n", data.commit_count)),
        MessageSegment::text("最新提交：\n"),
    ];

    // Show up to 3 recent commits
    for commit in data.commits.iter().take(3) {
        let short_id = &commit.id[..7.min(commit.id.len())];
        let commit_message = commit.message.lines().next().unwrap_or("");
        let author = commit
            .author
            .as_ref()
            .and_then(|a| a.name.as_deref())
            .unwrap_or("未知");

        message.push(MessageSegment::text(format!(
            "[{}] {} (by {})\n",
            short_id, commit_message, author
        )));
    }

    message
}

/// Format a pull request event message
pub fn format_pull_request_message(data: &PullRequestData) -> Message {
    let action_text = match data.action.as_str() {
        "opened" => "创建了",
        "closed" => {
            if data.pull_request.merged.unwrap_or(false) {
                "合并了"
            } else {
                "关闭了"
            }
        }
        "reopened" => "重新打开了",
        "assigned" => "被分配了",
        "unassigned" => "被取消分配了",
        "review_requested" => "请求审核",
        "review_request_removed" => "取消审核请求",
        "labeled" => "被添加了标签",
        "unlabeled" => "被移除了标签",
        "synchronize" => "同步了",
        other => other,
    };

    let mut message = vec![
        MessageSegment::text(format!("📢 GitHub Pull Request {}\n", action_text)),
        MessageSegment::text(format!("仓库：{}\n", data.repo_name)),
        MessageSegment::text(format!(
            "PR #{}: {}\n",
            data.pull_request.number, data.pull_request.title
        )),
        MessageSegment::text(format!("用户：{}\n", data.user)),
        MessageSegment::text(format!("状态：{}\n", data.pull_request.state)),
    ];

    // Add branch info
    if let (Some(base), Some(head)) = (&data.pull_request.base, &data.pull_request.head) {
        message.push(MessageSegment::text(format!(
            "目标分支：{} ← {}\n",
            base.branch_ref, head.branch_ref
        )));
    }

    // Add link
    if let Some(url) = &data.pull_request.html_url {
        message.push(MessageSegment::text(format!("链接：{}\n", url)));
    }

    message
}

/// Format an issue event message
pub fn format_issue_message(data: &IssueData) -> Message {
    let action_text = match data.action.as_str() {
        "opened" => "创建了",
        "closed" => "关闭了",
        "reopened" => "重新打开了",
        "assigned" => "被分配了",
        "unassigned" => "被取消分配了",
        "labeled" => "被添加了标签",
        "unlabeled" => "被移除了标签",
        other => other,
    };

    let mut message = vec![
        MessageSegment::text(format!("📢 GitHub Issue {}\n", action_text)),
        MessageSegment::text(format!("仓库：{}\n", data.repo_name)),
        MessageSegment::text(format!(
            "Issue #{}: {}\n",
            data.issue.number, data.issue.title
        )),
        MessageSegment::text(format!("用户：{}\n", data.user)),
        MessageSegment::text(format!("状态：{}\n", data.issue.state)),
    ];

    // Add labels
    if !data.issue.labels.is_empty() {
        let label_names: Vec<&str> = data.issue.labels.iter().map(|l| l.name.as_str()).collect();
        message.push(MessageSegment::text(format!(
            "标签：{}\n",
            label_names.join(", ")
        )));
    }

    // Add link
    if let Some(url) = &data.issue.html_url {
        message.push(MessageSegment::text(format!("链接：{}\n", url)));
    }

    message
}

/// Format a release event message
pub fn format_release_message(data: &ReleaseData) -> Message {
    let action_text = match data.action.as_str() {
        "published" => "发布了",
        "created" => "创建了",
        "edited" => "编辑了",
        "deleted" => "删除了",
        "prereleased" => "预发布了",
        "released" => "正式发布了",
        other => other,
    };

    let tag_name = data.release.tag_name.as_deref().unwrap_or("");
    let name = data
        .release
        .name
        .as_deref()
        .filter(|n| !n.is_empty())
        .unwrap_or(tag_name);

    let mut message = vec![
        MessageSegment::text(format!("📢 GitHub Release {}\n", action_text)),
        MessageSegment::text(format!("仓库：{}\n", data.repo_name)),
        MessageSegment::text(format!("版本：{} ({})\n", name, tag_name)),
        MessageSegment::text(format!("发布者：{}\n", data.user)),
    ];

    // Add prerelease info
    if data.release.prerelease.unwrap_or(false) {
        message.push(MessageSegment::text("类型：预发布\n"));
    }

    // Add publish time
    if let Some(published_at) = &data.release.published_at {
        message.push(MessageSegment::text(format!("发布时间：{}\n", published_at)));
    }

    // Add link
    if let Some(url) = &data.release.html_url {
        message.push(MessageSegment::text(format!("链接：{}\n", url)));
    }

    message
}

/// Format an issue comment event message
pub fn format_issue_comment_message(data: &IssueCommentData) -> Message {
    let action_text = match data.action.as_str() {
        "created" => "发表了",
        "edited" => "编辑了",
        "deleted" => "删除了",
        other => other,
    };

    // Determine if this is a PR or Issue comment
    let issue_type = if data.comment.pull_request.is_some() {
        "PR"
    } else {
        "Issue"
    };

    let mut message = vec![
        MessageSegment::text(format!("📢 GitHub {}评论 {}\n", issue_type, action_text)),
        MessageSegment::text(format!("仓库：{}\n", data.repo_name)),
        MessageSegment::text(format!("{} #{}\n", issue_type, data.issue_number)),
        MessageSegment::text(format!("用户：{}\n", data.user)),
    ];

    // Add comment preview
    if let Some(body) = &data.comment.body {
        if data.action != "deleted" && !body.is_empty() {
            let preview = if body.len() > 100 {
                format!("{}...", &body[..100])
            } else {
                body.clone()
            };
            let preview = preview.replace('\n', " ");
            message.push(MessageSegment::text(format!("内容：{}\n", preview)));
        }
    }

    // Add link
    if let Some(url) = &data.comment.html_url {
        message.push(MessageSegment::text(format!("链接：{}\n", url)));
    }

    message
}
