"""
Orchestrator - manages data ingestion from all sources and stores in Reeve
"""
import asyncio
from datetime import datetime
from typing import Optional
from ingester_github import GitHubIngester
from ingester_jira import JiraIngester
from ingester_slack import SlackIngester
from memory_manager import ReeveMemoryManager
from models import NormalizedEvent
from config import validate_configuration


class DataOrchestrator:
    """Orchestrates data ingestion from multiple sources into Reeve"""

    def __init__(self):
        self.memory_manager = ReeveMemoryManager()
        self.github_ingester: Optional[GitHubIngester] = None
        self.jira_ingester: Optional[JiraIngester] = None
        self.slack_ingester: Optional[SlackIngester] = None
        self._init_ingesters()

    def _init_ingesters(self):
        """Initialize available ingesters based on configuration"""
        config_status = validate_configuration()

        if config_status.get("github"):
            try:
                self.github_ingester = GitHubIngester()
                print("✓ GitHub ingester initialized")
            except Exception as e:
                print(f"✗ GitHub ingester failed: {e}")

        if config_status.get("jira"):
            try:
                self.jira_ingester = JiraIngester()
                print("✓ Jira ingester initialized")
            except Exception as e:
                print(f"✗ Jira ingester failed: {e}")

        if config_status.get("slack"):
            try:
                self.slack_ingester = SlackIngester()
                print("✓ Slack ingester initialized")
            except Exception as e:
                print(f"✗ Slack ingester failed: {e}")

    def ingest_all(self, github_repos: Optional[list] = None, jira_projects: Optional[list] = None) -> dict:
        """
        Full ingestion from all configured sources.
        Returns summary of ingested events.
        """
        from config import github_config, jira_config
        
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "github": {"events": 0, "status": "not_configured"},
            "jira": {"events": 0, "status": "not_configured"},
            "slack": {"events": 0, "status": "not_configured"},
            "total_stored": 0,
            "errors": [],
        }

        # GitHub ingestion
        if self.github_ingester:
            try:
                repos = github_repos or github_config.repos or ["main"]  # Use config repos
                gh_events = []
                for repo in repos:
                    gh_events.extend(self.github_ingester.ingest_pull_requests(repo))
                    gh_events.extend(self.github_ingester.ingest_issues(repo))
                    gh_events.extend(self.github_ingester.ingest_commits(repo))

                stored = sum(1 for e in gh_events if self.memory_manager.store_event(e))
                summary["github"] = {
                    "events": len(gh_events),
                    "stored": stored,
                    "status": "success",
                }
                summary["total_stored"] += stored
            except Exception as e:
                summary["github"]["status"] = "error"
                summary["errors"].append(f"GitHub: {str(e)}")

        # Jira ingestion
        if self.jira_ingester:
            try:
                projects = jira_projects or jira_config.projects or ["MAIN"]  # Use config projects
                jira_events = []
                for project in projects:
                    jira_events.extend(self.jira_ingester.ingest_issues(project))
                    jira_events.extend(self.jira_ingester.ingest_board_transitions(project))

                stored = sum(1 for e in jira_events if self.memory_manager.store_event(e))
                summary["jira"] = {
                    "events": len(jira_events),
                    "stored": stored,
                    "status": "success",
                }
                summary["total_stored"] += stored
            except Exception as e:
                summary["jira"]["status"] = "error"
                summary["errors"].append(f"Jira: {str(e)}")

        # Slack ingestion
        if self.slack_ingester:
            try:
                channels = self.slack_ingester.get_all_channels()
                slack_events = []
                for channel in channels:
                    slack_events.extend(self.slack_ingester.ingest_channel_messages(channel["id"]))
                    slack_events.extend(self.slack_ingester.ingest_user_mentions(channel["id"]))

                stored = sum(1 for e in slack_events if self.memory_manager.store_event(e))
                summary["slack"] = {
                    "events": len(slack_events),
                    "stored": stored,
                    "status": "success",
                }
                summary["total_stored"] += stored
            except Exception as e:
                summary["slack"]["status"] = "error"
                summary["errors"].append(f"Slack: {str(e)}")

        return summary

    def ingest_github(self, repos: Optional[list] = None) -> dict:
        """Ingest from GitHub only"""
        if not self.github_ingester:
            return {"status": "error", "message": "GitHub not configured"}

        repos = repos or ["main"]
        events = []
        for repo in repos:
            events.extend(self.github_ingester.ingest_pull_requests(repo))
            events.extend(self.github_ingester.ingest_issues(repo))
            events.extend(self.github_ingester.ingest_commits(repo))

        stored = sum(1 for e in events if self.memory_manager.store_event(e))
        return {
            "status": "success",
            "total_events": len(events),
            "stored": stored,
        }

    def ingest_jira(self, projects: Optional[list] = None) -> dict:
        """Ingest from Jira only"""
        if not self.jira_ingester:
            return {"status": "error", "message": "Jira not configured"}

        projects = projects or ["MAIN"]
        events = []
        for project in projects:
            events.extend(self.jira_ingester.ingest_issues(project))
            events.extend(self.jira_ingester.ingest_board_transitions(project))

        stored = sum(1 for e in events if self.memory_manager.store_event(e))
        return {
            "status": "success",
            "total_events": len(events),
            "stored": stored,
        }

    def ingest_slack(self) -> dict:
        """Ingest from Slack only"""
        if not self.slack_ingester:
            return {"status": "error", "message": "Slack not configured"}

        channels = self.slack_ingester.get_all_channels()
        events = []
        for channel in channels:
            events.extend(self.slack_ingester.ingest_channel_messages(channel["id"]))
            events.extend(self.slack_ingester.ingest_user_mentions(channel["id"]))

        stored = sum(1 for e in events if self.memory_manager.store_event(e))
        return {
            "status": "success",
            "total_channels": len(channels),
            "total_events": len(events),
            "stored": stored,
        }

    def get_status(self) -> dict:
        """Get current configuration and ingester status"""
        config_status = validate_configuration()
        return {
            "configured_sources": {k: v for k, v in config_status.items() if v},
            "memory_namespace": "organization_memory",
            "timestamp": datetime.utcnow().isoformat(),
        }
