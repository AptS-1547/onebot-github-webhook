# Copyright 2025 AptS-1547
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
GitHub Webhook 事件数据模型

本模块定义了各类 GitHub Webhook 事件的数据模型。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class CommitAuthor(BaseModel):
    """
    提交作者信息。

    Attributes:
        name: 作者名称
        email: 作者邮箱
        username: 作者用户名（可选）
    """
    name: str
    email: str
    username: Optional[str] = None


class Commit(BaseModel):
    """
    Git 提交信息。

    Attributes:
        id: 提交 SHA
        message: 提交消息
        author: 提交作者
        url: 提交 URL
    """
    id: str
    message: str
    author: CommitAuthor
    url: str


class PushEventData(BaseModel):
    """
    Push 事件数据。

    Attributes:
        repo_name: 仓库全名（如 "user/repo"）
        branch: 分支名
        pusher: 推送者名称
        commits: 提交列表
        commit_count: 提交数量
    """
    repo_name: str
    branch: str
    pusher: str
    commits: List[Commit] = Field(default_factory=list)
    commit_count: int

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "PushEventData":
        """
        从 GitHub Webhook payload 创建实例。

        Args:
            payload: GitHub Webhook payload 字典

        Returns:
            PushEventData: 解析后的事件数据
        """
        commits_raw = payload.get("commits", [])
        commits = [
            Commit(
                id=c.get("id", ""),
                message=c.get("message", ""),
                author=CommitAuthor(
                    name=c.get("author", {}).get("name", "未知"),
                    email=c.get("author", {}).get("email", ""),
                    username=c.get("author", {}).get("username")
                ),
                url=c.get("url", "")
            )
            for c in commits_raw
        ]

        return cls(
            repo_name=payload.get("repository", {}).get("full_name", ""),
            branch=payload.get("ref", "").replace("refs/heads/", ""),
            pusher=payload.get("pusher", {}).get("name", "未知"),
            commits=commits,
            commit_count=len(commits)
        )


class PullRequestInfo(BaseModel):
    """
    Pull Request 信息。

    Attributes:
        number: PR 编号
        title: PR 标题
        state: PR 状态
        merged: 是否已合并
        base_branch: 目标分支
        head_branch: 源分支
        html_url: PR URL
    """
    number: int
    title: str
    state: str
    merged: bool = False
    base_branch: str
    head_branch: str
    html_url: str


class PullRequestEventData(BaseModel):
    """
    Pull Request 事件数据。

    Attributes:
        repo_name: 仓库全名
        action: 操作类型（opened, closed, etc.）
        pull_request: PR 信息
        user: 操作用户
    """
    repo_name: str
    action: str
    pull_request: PullRequestInfo
    user: str

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "PullRequestEventData":
        """
        从 GitHub Webhook payload 创建实例。

        Args:
            payload: GitHub Webhook payload 字典

        Returns:
            PullRequestEventData: 解析后的事件数据
        """
        pr = payload.get("pull_request", {})
        return cls(
            repo_name=payload.get("repository", {}).get("full_name", ""),
            action=payload.get("action", ""),
            pull_request=PullRequestInfo(
                number=pr.get("number", 0),
                title=pr.get("title", ""),
                state=pr.get("state", ""),
                merged=pr.get("merged", False),
                base_branch=pr.get("base", {}).get("ref", ""),
                head_branch=pr.get("head", {}).get("ref", ""),
                html_url=pr.get("html_url", "")
            ),
            user=payload.get("sender", {}).get("login", "未知")
        )


class IssueInfo(BaseModel):
    """
    Issue 信息。

    Attributes:
        number: Issue 编号
        title: Issue 标题
        state: Issue 状态
        labels: 标签列表
        html_url: Issue URL
    """
    number: int
    title: str
    state: str
    labels: List[str] = Field(default_factory=list)
    html_url: str


class IssueEventData(BaseModel):
    """
    Issue 事件数据。

    Attributes:
        repo_name: 仓库全名
        action: 操作类型
        issue: Issue 信息
        user: 操作用户
    """
    repo_name: str
    action: str
    issue: IssueInfo
    user: str

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "IssueEventData":
        """
        从 GitHub Webhook payload 创建实例。

        Args:
            payload: GitHub Webhook payload 字典

        Returns:
            IssueEventData: 解析后的事件数据
        """
        issue = payload.get("issue", {})
        labels = [label.get("name", "") for label in issue.get("labels", [])]

        return cls(
            repo_name=payload.get("repository", {}).get("full_name", ""),
            action=payload.get("action", ""),
            issue=IssueInfo(
                number=issue.get("number", 0),
                title=issue.get("title", ""),
                state=issue.get("state", ""),
                labels=labels,
                html_url=issue.get("html_url", "")
            ),
            user=payload.get("sender", {}).get("login", "未知")
        )


class ReleaseInfo(BaseModel):
    """
    Release 信息。

    Attributes:
        tag_name: 标签名
        name: Release 名称
        prerelease: 是否为预发布
        published_at: 发布时间
        html_url: Release URL
    """
    tag_name: str
    name: str
    prerelease: bool = False
    published_at: Optional[str] = None
    html_url: str


class ReleaseEventData(BaseModel):
    """
    Release 事件数据。

    Attributes:
        repo_name: 仓库全名
        action: 操作类型
        release: Release 信息
        user: 操作用户
    """
    repo_name: str
    action: str
    release: ReleaseInfo
    user: str

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "ReleaseEventData":
        """
        从 GitHub Webhook payload 创建实例。

        Args:
            payload: GitHub Webhook payload 字典

        Returns:
            ReleaseEventData: 解析后的事件数据
        """
        release = payload.get("release", {})
        return cls(
            repo_name=payload.get("repository", {}).get("full_name", ""),
            action=payload.get("action", ""),
            release=ReleaseInfo(
                tag_name=release.get("tag_name", ""),
                name=release.get("name", release.get("tag_name", "")),
                prerelease=release.get("prerelease", False),
                published_at=release.get("published_at"),
                html_url=release.get("html_url", "")
            ),
            user=payload.get("sender", {}).get("login", "未知")
        )


class CommentInfo(BaseModel):
    """
    评论信息。

    Attributes:
        body: 评论内容
        html_url: 评论 URL
    """
    body: str
    html_url: str


class IssueCommentEventData(BaseModel):
    """
    Issue/PR 评论事件数据。

    Attributes:
        repo_name: 仓库全名
        action: 操作类型
        issue_number: Issue/PR 编号
        comment: 评论信息
        user: 操作用户
        is_pull_request: 是否为 PR 评论
    """
    repo_name: str
    action: str
    issue_number: int
    comment: CommentInfo
    user: str
    is_pull_request: bool = False

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "IssueCommentEventData":
        """
        从 GitHub Webhook payload 创建实例。

        Args:
            payload: GitHub Webhook payload 字典

        Returns:
            IssueCommentEventData: 解析后的事件数据
        """
        comment = payload.get("comment", {})
        issue = payload.get("issue", {})

        return cls(
            repo_name=payload.get("repository", {}).get("full_name", ""),
            action=payload.get("action", ""),
            issue_number=issue.get("number", 0),
            comment=CommentInfo(
                body=comment.get("body", ""),
                html_url=comment.get("html_url", "")
            ),
            user=payload.get("sender", {}).get("login", "未知"),
            is_pull_request="pull_request" in issue
        )
