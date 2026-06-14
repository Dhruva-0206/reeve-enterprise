"""
GitHub data ingester - pulls PRs, issues, commits, and state changes from GitHub API
"""
from datetime import datetime
from typing import Optional
from github import Github
from models import NormalizedEvent, Entity, StateChange, Relationship
from config import github_config


class GitHubIngester:
    """Fetch and normalize GitHub data"""

    def __init__(self):
        if not github_config.is_configured:
            raise ValueError("GitHub configuration incomplete. Set GITHUB_TOKEN and GITHUB_OWNER")
        self.client = Github(github_config.token)
        self.owner = github_config.owner
        self.repos = github_config.repos

    def ingest_pull_requests(self, repo_name: str, limit: int = 100) -> list[NormalizedEvent]:
        """Fetch PR events from repository"""
        events = []
        try:
            repo = self.client.get_user(self.owner).get_repo(repo_name)
            prs = repo.get_pulls(state="all", sort="updated", direction="desc")

            for i, pr in enumerate(prs):
                if i >= limit:
                    break
                event = self._normalize_pr(repo_name, pr)
                events.append(event)
        except Exception as e:
            print(f"Error ingesting PRs from {repo_name}: {e}")

        return events

    def ingest_issues(self, repo_name: str, limit: int = 100) -> list[NormalizedEvent]:
        """Fetch issue events from repository"""
        events = []
        try:
            repo = self.client.get_user(self.owner).get_repo(repo_name)
            issues = repo.get_issues(state="all", sort="updated", direction="desc")

            for i, issue in enumerate(issues):
                if i >= limit:
                    break
                event = self._normalize_issue(repo_name, issue)
                events.append(event)
        except Exception as e:
            print(f"Error ingesting issues from {repo_name}: {e}")

        return events

    def ingest_commits(self, repo_name: str, limit: int = 50) -> list[NormalizedEvent]:
        """Fetch commit events from repository"""
        events = []
        try:
            repo = self.client.get_user(self.owner).get_repo(repo_name)
            commits = repo.get_commits()

            for i, commit in enumerate(commits):
                if i >= limit:
                    break
                event = self._normalize_commit(repo_name, commit)
                events.append(event)
        except Exception as e:
            print(f"Error ingesting commits from {repo_name}: {e}")

        return events

    def _normalize_pr(self, repo_name: str, pr) -> NormalizedEvent:
        """Convert GitHub PR to NormalizedEvent"""
        pr_id = f"github:pr:{repo_name}#{pr.number}"

        # Track state change if PR is merged/closed
        changes = []
        if pr.merged:
            changes.append(StateChange(
                entity_id=pr_id,
                previous_state="open",
                new_state="merged",
                timestamp=pr.merged_at or datetime.utcnow(),
                changed_by=pr.merged_by.login if pr.merged_by else None,
                reason=pr.title,
            ))
        elif pr.state == "closed":
            changes.append(StateChange(
                entity_id=pr_id,
                previous_state="open",
                new_state="closed",
                timestamp=pr.updated_at,
                reason="Not merged",
            ))

        # Track relationships to issues
        relationships = []
        if pr.body and "#" in pr.body:
            # Simple extraction of issue references
            import re
            issue_refs = re.findall(r"#(\d+)", pr.body)
            for issue_num in issue_refs:
                relationships.append(Relationship(
                    source_id=pr_id,
                    target_id=f"github:issue:{repo_name}#{issue_num}",
                    relationship_type="fixes" if "fix" in pr.body.lower() else "related_to",
                    context=f"PR body mentions this issue",
                    discovered_at=datetime.utcnow(),
                ))

        entity = Entity(
            id=pr_id,
            type="pr",
            title=pr.title,
            source="github",
            url=pr.html_url,
            created_at=pr.created_at,
            updated_at=pr.updated_at,
        )

        return NormalizedEvent(
            id=pr_id,
            event_type="created" if pr.created_at == pr.updated_at else "updated",
            entity=entity,
            timestamp=pr.updated_at,
            actor=pr.user.login if pr.user else None,
            content=pr.body or "",
            changes=changes,
            relationships=relationships,
            metadata={
                "pr_number": pr.number,
                "merged": pr.merged,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "comments": pr.comments,
                "labels": [label.name for label in pr.labels],
            },
        )

    def _normalize_issue(self, repo_name: str, issue) -> NormalizedEvent:
        """Convert GitHub Issue to NormalizedEvent"""
        issue_id = f"github:issue:{repo_name}#{issue.number}"

        # Track state change
        changes = []
        if issue.state == "closed":
            changes.append(StateChange(
                entity_id=issue_id,
                previous_state="open",
                new_state="closed",
                timestamp=issue.updated_at,
                reason=issue.title,
            ))

        entity = Entity(
            id=issue_id,
            type="issue",
            title=issue.title,
            source="github",
            url=issue.html_url,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
        )

        return NormalizedEvent(
            id=issue_id,
            event_type="created" if issue.created_at == issue.updated_at else "updated",
            entity=entity,
            timestamp=issue.updated_at,
            actor=issue.user.login if issue.user else None,
            content=issue.body or "",
            changes=changes,
            metadata={
                "issue_number": issue.number,
                "state": issue.state,
                "comments": issue.comments,
                "labels": [label.name for label in issue.labels],
                "assignees": [a.login for a in issue.assignees],
            },
        )

    def _normalize_commit(self, repo_name: str, commit) -> NormalizedEvent:
        """Convert GitHub Commit to NormalizedEvent"""
        commit_id = f"github:commit:{repo_name}:{commit.sha[:7]}"

        entity = Entity(
            id=commit_id,
            type="commit",
            title=commit.commit.message.split("\n")[0][:100],
            source="github",
            url=commit.html_url,
            created_at=commit.commit.author.date,
            updated_at=commit.commit.author.date,
        )

        return NormalizedEvent(
            id=commit_id,
            event_type="created",
            entity=entity,
            timestamp=commit.commit.author.date,
            actor=commit.author.login if commit.author else commit.commit.author.name,
            content=commit.commit.message,
            metadata={
                "sha": commit.sha,
                "additions": commit.stats.additions,
                "deletions": commit.stats.deletions,
                "files_changed": commit.stats.total,
            },
        )
