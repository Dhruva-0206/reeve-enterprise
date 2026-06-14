"""
Jira data ingester - pulls tickets, comments, and state changes from Jira API
"""
from datetime import datetime
from typing import Optional
from jira import JIRA
from models import NormalizedEvent, Entity, StateChange, Relationship
from config import jira_config


class JiraIngester:
    """Fetch and normalize Jira data"""

    def __init__(self):
        if not jira_config.is_configured:
            raise ValueError("Jira configuration incomplete. Set JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN")

        self.client = JIRA(
            server=jira_config.url,
            basic_auth=(jira_config.username, jira_config.api_token),
        )
        self.projects = jira_config.projects

    def ingest_issues(self, project_key: str, limit: int = 100) -> list[NormalizedEvent]:
        """Fetch issues from a Jira project"""
        events = []
        try:
            jql = f"project = {project_key} ORDER BY updated DESC"
            issues = self.client.search_issues(jql, maxResults=limit)

            for issue in issues:
                event = self._normalize_issue(issue)
                events.append(event)
                # Also ingest comments as separate events
                events.extend(self._ingest_issue_comments(issue))
        except Exception as e:
            print(f"Error ingesting Jira issues from {project_key}: {e}")

        return events

    def ingest_board_transitions(self, project_key: str) -> list[NormalizedEvent]:
        """Track issue state transitions on Jira board"""
        events = []
        try:
            jql = f"project = {project_key} ORDER BY updated DESC"
            issues = self.client.search_issues(jql, maxResults=50)

            for issue in issues:
                # Get changelog to track state transitions
                issue_details = self.client.issue(issue.key, expand="changelog")
                for history in issue_details.changelog.histories:
                    for item in history.items:
                        if item.field == "status":
                            event = self._normalize_status_change(issue, history, item)
                            events.append(event)
        except Exception as e:
            print(f"Error ingesting Jira board transitions from {project_key}: {e}")

        return events

    def _normalize_issue(self, issue) -> NormalizedEvent:
        """Convert Jira Issue to NormalizedEvent"""
        issue_id = f"jira:issue:{issue.key}"

        # Track current state as a change (for initial ingest)
        changes = []
        if issue.fields.status:
            changes.append(StateChange(
                entity_id=issue_id,
                previous_state="created",
                new_state=issue.fields.status.name,
                timestamp=issue.fields.created if hasattr(issue.fields, "created") else datetime.utcnow(),
                reason=issue.fields.summary,
            ))

        # Track relationships to other issues
        relationships = []
        if issue.fields.issuelinks:
            for link in issue.fields.issuelinks:
                target_issue = link.outwardIssue if hasattr(link, "outwardIssue") else link.inwardIssue
                if target_issue:
                    relationships.append(Relationship(
                        source_id=issue_id,
                        target_id=f"jira:issue:{target_issue.key}",
                        relationship_type=link.type.name.lower(),
                        context=f"Jira link: {link.type.name}",
                        discovered_at=datetime.utcnow(),
                    ))

        entity = Entity(
            id=issue_id,
            type="ticket",
            title=issue.fields.summary,
            source="jira",
            url=f"{jira_config.url}/browse/{issue.key}",
            created_at=issue.fields.created,
            updated_at=issue.fields.updated,
        )

        return NormalizedEvent(
            id=issue_id,
            event_type="created",
            entity=entity,
            timestamp=issue.fields.updated,
            actor=issue.fields.reporter.name if issue.fields.reporter else None,
            content=issue.fields.description or "",
            changes=changes,
            relationships=relationships,
            metadata={
                "key": issue.key,
                "status": issue.fields.status.name if issue.fields.status else None,
                "priority": issue.fields.priority.name if issue.fields.priority else None,
                "assignee": issue.fields.assignee.name if issue.fields.assignee else None,
                "labels": issue.fields.labels,
                "components": [c.name for c in issue.fields.components] if issue.fields.components else [],
            },
        )

    def _ingest_issue_comments(self, issue) -> list[NormalizedEvent]:
        """Extract comments from Jira issue as separate events"""
        events = []
        if issue.fields.comment.comments:
            for comment in issue.fields.comment.comments:
                event_id = f"jira:comment:{issue.key}:{comment.id}"
                entity = Entity(
                    id=event_id,
                    type="comment",
                    title=f"Comment on {issue.key}",
                    source="jira",
                    url=f"{jira_config.url}/browse/{issue.key}?focusedCommentId={comment.id}",
                    created_at=comment.created,
                    updated_at=comment.updated,
                )

                # Link comment to its issue
                relationships = [Relationship(
                    source_id=event_id,
                    target_id=f"jira:issue:{issue.key}",
                    relationship_type="comment_on",
                    discovered_at=datetime.utcnow(),
                )]

                event = NormalizedEvent(
                    id=event_id,
                    event_type="commented",
                    entity=entity,
                    timestamp=comment.updated,
                    actor=comment.author.name if comment.author else None,
                    content=comment.body,
                    relationships=relationships,
                )
                events.append(event)

        return events

    def _normalize_status_change(self, issue, history, item) -> NormalizedEvent:
        """Convert Jira status change to NormalizedEvent"""
        change_id = f"jira:status_change:{issue.key}:{history.id}"

        entity = Entity(
            id=f"jira:issue:{issue.key}",
            type="ticket",
            title=f"Status changed: {issue.fields.summary}",
            source="jira",
            url=f"{jira_config.url}/browse/{issue.key}",
            created_at=issue.fields.created,
            updated_at=history.created,
        )

        change = StateChange(
            entity_id=f"jira:issue:{issue.key}",
            previous_state=item.fromString or "unknown",
            new_state=item.toString or "unknown",
            timestamp=history.created,
            changed_by=history.author.name if history.author else None,
        )

        event = NormalizedEvent(
            id=change_id,
            event_type="state_changed",
            entity=entity,
            timestamp=history.created,
            actor=history.author.name if history.author else None,
            changes=[change],
        )

        return event
