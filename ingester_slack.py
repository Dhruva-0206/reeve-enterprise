"""
Slack data ingester - pulls messages, threads, and conversations from Slack API
"""
from datetime import datetime
from typing import Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from models import NormalizedEvent, Entity, Relationship
from config import slack_config


class SlackIngester:
    """Fetch and normalize Slack data"""

    def __init__(self):
        if not slack_config.is_configured:
            raise ValueError("Slack configuration incomplete. Set SLACK_BOT_TOKEN")

        self.client = WebClient(token=slack_config.bot_token)
        self.channels = slack_config.channels

    def ingest_channel_messages(self, channel_id: str, limit: int = 100) -> list[NormalizedEvent]:
        """Fetch messages from a Slack channel"""
        events = []
        try:
            # Get channel history
            result = self.client.conversations_history(
                channel=channel_id,
                limit=limit,
            )

            for message in result.get("messages", []):
                event = self._normalize_message(channel_id, message)
                events.append(event)

                # Also ingest thread replies if message has threads
                if message.get("thread_ts"):
                    events.extend(self._ingest_thread(channel_id, message.get("thread_ts")))

        except SlackApiError as e:
            print(f"Error ingesting Slack channel {channel_id}: {e}")

        return events

    def ingest_user_mentions(self, channel_id: str, limit: int = 50) -> list[NormalizedEvent]:
        """Fetch messages mentioning important keywords/decisions"""
        events = []
        try:
            # Search for decision-related messages
            search_queries = ["decision", "approved", "blocked", "failed", "deployed", "incident"]

            for query in search_queries:
                result = self.client.search_messages(
                    query=f"{query} in:{channel_id}",
                    count=limit,
                )

                for message in result.get("messages", []):
                    event = self._normalize_message(channel_id, message["message"])
                    events.append(event)

        except SlackApiError as e:
            print(f"Error searching Slack messages: {e}")

        return events

    def _normalize_message(self, channel_id: str, message: dict) -> NormalizedEvent:
        """Convert Slack message to NormalizedEvent"""
        ts = message.get("ts", "0")
        message_id = f"slack:message:{channel_id}:{ts.replace('.', '_')}"

        # Extract mentions and links
        relationships = []
        if "blocks" in message:
            for block in message["blocks"]:
                if block.get("type") == "rich_text":
                    # Extract mentioned users/channels
                    for element in block.get("elements", []):
                        if element.get("type") == "user":
                            relationships.append(Relationship(
                                source_id=message_id,
                                target_id=f"slack:user:{element.get('user_id')}",
                                relationship_type="mentions",
                                discovered_at=datetime.utcnow(),
                            ))

        # Parse timestamps
        try:
            timestamp = datetime.fromtimestamp(float(ts))
        except (ValueError, TypeError):
            timestamp = datetime.utcnow()

        entity = Entity(
            id=message_id,
            type="message",
            title=f"Slack message in #{channel_id}",
            source="slack",
            url=self._get_message_url(channel_id, ts),
            created_at=timestamp,
            updated_at=timestamp,
        )

        return NormalizedEvent(
            id=message_id,
            event_type="created",
            entity=entity,
            timestamp=timestamp,
            actor=message.get("user") or message.get("username"),
            content=message.get("text", ""),
            relationships=relationships,
            metadata={
                "channel_id": channel_id,
                "thread_ts": message.get("thread_ts"),
                "reply_count": message.get("reply_count", 0),
                "reactions": message.get("reactions", []),
                "attachments": len(message.get("attachments", [])),
            },
        )

    def _ingest_thread(self, channel_id: str, thread_ts: str) -> list[NormalizedEvent]:
        """Fetch replies in a thread"""
        events = []
        try:
            result = self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                limit=100,
            )

            for message in result.get("messages", []):
                # Skip the parent message
                if message.get("ts") == thread_ts:
                    continue

                event = self._normalize_message(channel_id, message)
                # Link reply to parent
                parent_id = f"slack:message:{channel_id}:{thread_ts.replace('.', '_')}"
                event.relationships.append(Relationship(
                    source_id=event.id,
                    target_id=parent_id,
                    relationship_type="reply_to",
                    discovered_at=datetime.utcnow(),
                ))
                events.append(event)

        except SlackApiError as e:
            print(f"Error ingesting thread {thread_ts}: {e}")

        return events

    def get_all_channels(self) -> list[dict]:
        """Get list of all accessible channels"""
        try:
            result = self.client.conversations_list(
                types="public_channel,private_channel",
                limit=100,
            )
            return result.get("channels", [])
        except SlackApiError as e:
            print(f"Error listing channels: {e}")
            return []

    def _get_message_url(self, channel_id: str, ts: str) -> str:
        """Generate Slack message URL"""
        ts_link = ts.replace(".", "")
        return f"https://slack.com/archives/{channel_id}/p{ts_link}"
