"""
Configuration management for Enterprise Knowledge Investigator
"""
import os
from typing import Optional
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

load_dotenv()


class ReveConfig(BaseModel):
    api_key: str = os.getenv("REEVE_API_KEY", "")
    namespace: str = os.getenv("REEVE_NAMESPACE", "organization_memory")


class GitHubConfig(BaseModel):
    token: str = os.getenv("GITHUB_TOKEN", "")
    owner: str = os.getenv("GITHUB_OWNER", "")
    repos: list[str] = os.getenv("GITHUB_REPOS", "").split(",")

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.owner)


class JiraConfig(BaseModel):
    url: str = os.getenv("JIRA_URL", "")
    username: str = os.getenv("JIRA_USERNAME", "")
    api_token: str = os.getenv("JIRA_API_TOKEN", "")
    projects: list[str] = os.getenv("JIRA_PROJECTS", "").split(",")

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.username and self.api_token)


class SlackConfig(BaseModel):
    bot_token: str = os.getenv("SLACK_BOT_TOKEN", "")
    signing_secret: str = os.getenv("SLACK_SIGNING_SECRET", "")
    channels: list[str] = os.getenv("SLACK_CHANNELS", "").split(",")

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.signing_secret)


class AppConfig(BaseModel):
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8000"))
    debug: bool = False

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return bool(v)


# Initialize all configs
reeve_config = ReveConfig()
github_config = GitHubConfig()
jira_config = JiraConfig()
slack_config = SlackConfig()
app_config = AppConfig()


def validate_configuration() -> dict[str, bool]:
    """Check which data sources are properly configured"""
    return {
        "github": github_config.is_configured,
        "jira": jira_config.is_configured,
        "slack": slack_config.is_configured,
        "reeve": bool(reeve_config.api_key),
    }
