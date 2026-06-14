"""
Data normalization: Convert source-specific events to canonical format
"""
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Entity(BaseModel):
    """Canonical entity representation"""
    id: str  # Format: source:type:identifier (e.g., github:pr:123, jira:issue:PROJ-456)
    type: str  # pr, issue, commit, ticket, slack_message, etc.
    title: str
    source: str  # github, jira, slack, etc.
    url: str = ""
    created_at: datetime
    updated_at: datetime


class StateChange(BaseModel):
    """Represents a state transition for an entity"""
    entity_id: str
    previous_state: str
    new_state: str
    timestamp: datetime
    changed_by: Optional[str] = None
    reason: Optional[str] = None  # Why the change happened


class Relationship(BaseModel):
    """Connects two entities"""
    source_id: str  # First entity
    target_id: str  # Second entity
    relationship_type: str  # related_to, depends_on, blocks, fixes, etc.
    context: str = ""  # Why they're related
    discovered_at: datetime


class NormalizedEvent(BaseModel):
    """Canonical representation of a data source event"""
    id: str = Field(description="Unique identifier across all sources")
    event_type: str  # created, updated, commented, state_changed, mentioned
    entity: Entity
    timestamp: datetime
    actor: Optional[str] = None  # Who caused this event
    content: str = ""  # Full text/message content
    changes: list[StateChange] = []
    relationships: list[Relationship] = []
    metadata: dict[str, Any] = {}  # Source-specific metadata

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class InvestigationResult(BaseModel):
    """Result of an investigation query"""
    query: str
    entity_id: str
    summary: str
    timeline: list[NormalizedEvent] = []
    related_entities: list[Entity] = []
    state_changes: list[StateChange] = []
    evidence: list[dict[str, Any]] = []  # Supporting data with sources
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
