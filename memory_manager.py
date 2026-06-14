"""
Reeve memory integration - handles storing and querying organizational knowledge
"""
import os
from typing import Optional
from datetime import datetime
from reeve import store_memory, query_memory, retrieve_memory_context
from models import NormalizedEvent, InvestigationResult, Entity, StateChange


class ReeveMemoryManager:
    """Manages interaction with Reeve for temporal knowledge graph"""

    def __init__(self, namespace: str = "organization_memory"):
        self.namespace = namespace
        os.environ["REEVE_API_KEY"] = os.getenv("REEVE_API_KEY", "")
        if not os.getenv("REEVE_API_KEY"):
            raise ValueError(
                "REEVE_API_KEY not set. Please configure your Reeve API key in .env"
            )

    def store_event(self, event: NormalizedEvent) -> bool:
        """
        Store a normalized event in Reeve's knowledge graph.
        Converts structured data into natural language memory statements.
        """
        try:
            # Build memory statements from the event
            statements = self._event_to_statements(event)

            for statement in statements:
                store_memory(
                    statement,
                    speaker=self.namespace
                )

            return True
        except Exception as e:
            print(f"Error storing event in Reeve: {e}")
            return False

    def _event_to_statements(self, event: NormalizedEvent) -> list[str]:
        """Convert normalized event into Reeve memory statements"""
        statements = []

        # Main event statement
        main_stmt = (
            f"[{event.entity.source.upper()}] {event.entity.title} "
            f"({event.entity.id}) - {event.event_type} at {event.timestamp.isoformat()}"
        )
        if event.content:
            main_stmt += f"\nContent: {event.content[:500]}"
        if event.actor:
            main_stmt += f"\nBy: {event.actor}"
        statements.append(main_stmt)

        # Store state changes
        for change in event.changes:
            state_stmt = (
                f"State change for {event.entity.id}: "
                f"{change.previous_state} → {change.new_state}"
            )
            if change.reason:
                state_stmt += f" (Reason: {change.reason})"
            statements.append(state_stmt)

        # Store relationships
        for rel in event.relationships:
            rel_stmt = (
                f"Relationship: {event.entity.id} {rel.relationship_type} {rel.target_id}"
            )
            if rel.context:
                rel_stmt += f" ({rel.context})"
            statements.append(rel_stmt)

        return statements

    def investigate(self, query: str, entity_id: Optional[str] = None) -> InvestigationResult:
        """
        Investigate a question using Reeve's query engine.
        Returns structured investigation result with evidence and connections.
        """
        try:
            # Automatically instruct Reeve to cross-reference all available systems
            enhanced_query = (
                f"Search across all ingested Jira tickets, GitHub issues, and codebase files to answer the following question. "
                f"Cross-reference any relevant bugs with the source code implementations. "
                f"Question: {query}"
            )
            
            # Query Reeve for relevant context using the enhanced prompt
            answer = query_memory(enhanced_query, speaker=self.namespace)

            # Retrieve contextual information
            context = retrieve_memory_context(
                query,
                speaker=self.namespace
            )

            # Build investigation result
            investigation = InvestigationResult(
                query=query,
                entity_id=entity_id or "unknown",
                summary=answer,
                evidence=[{"type": "reeve_context", "data": context}],
                discovered_at=datetime.utcnow(),
            )

            return investigation

        except Exception as e:
            print(f"Error investigating with Reeve: {e}")
            return InvestigationResult(
                query=query,
                entity_id=entity_id or "unknown",
                summary=f"Investigation failed: {str(e)}",
            )

    def get_entity_history(self, entity_id: str) -> list[dict]:
        """Retrieve full temporal history of an entity"""
        query = f"What is the complete history of {entity_id}?"
        result = self.investigate(query, entity_id)
        return result.timeline

    def trace_relationships(self, entity_id: str) -> dict:
        """Find all entities connected to a given entity"""
        query = f"What is connected to {entity_id}? List all related entities and relationships."
        result = self.investigate(query, entity_id)
        return {
            "entity": entity_id,
            "related": result.related_entities,
            "summary": result.summary,
        }

    def explain_state_change(self, entity_id: str, from_state: str, to_state: str) -> str:
        """Explain why an entity changed state"""
        query = (
            f"Why did {entity_id} change from {from_state} to {to_state}? "
            f"What was the decision or event that caused this?"
        )
        result = self.investigate(query, entity_id)
        return result.summary
