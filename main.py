"""
REST API for Enterprise Knowledge Investigator
Provides investigation query interface with presentable results
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from orchestrator import DataOrchestrator
from memory_manager import ReeveMemoryManager
from models import InvestigationResult


# Initialize FastAPI app
app = FastAPI(
    title="Enterprise Knowledge Investigator",
    description="AI-powered investigation system using Reeve temporal knowledge graphs",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
orchestrator = DataOrchestrator()
memory_manager = ReeveMemoryManager()


# Request/Response models
class IngestRequest(BaseModel):
    """Request to ingest data from sources"""
    github_repos: Optional[list[str]] = None
    jira_projects: Optional[list[str]] = None


class InvestigationRequest(BaseModel):
    """Investigation query request"""
    query: str
    entity_id: Optional[str] = None
    include_timeline: bool = True
    include_relationships: bool = True


class InvestigationQueryResponse(BaseModel):
    """Formatted investigation response"""
    query: str
    summary: str
    timeline: list = []
    related_entities: list = []
    state_changes: list = []
    evidence_count: int = 0
    discovery_time: str


# Health and Status endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/status")
async def get_status():
    """Get system status and configuration"""
    return orchestrator.get_status()


# Ingestion endpoints
@app.post("/ingest/all")
async def ingest_all(request: IngestRequest):
    """Ingest data from all configured sources"""
    try:
        result = orchestrator.ingest_all(
            github_repos=request.github_repos,
            jira_projects=request.jira_projects,
        )
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/github")
async def ingest_github(repos: Optional[list[str]] = Query(None)):
    """Ingest from GitHub only"""
    try:
        result = orchestrator.ingest_github(repos=repos)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/jira")
async def ingest_jira(projects: Optional[list[str]] = Query(None)):
    """Ingest from Jira only"""
    try:
        result = orchestrator.ingest_jira(projects=projects)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/slack")
async def ingest_slack():
    """Ingest from Slack only"""
    try:
        result = orchestrator.ingest_slack()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Investigation endpoints
@app.post("/investigate")
async def investigate(request: InvestigationRequest):
    """
    Main investigation endpoint - returns analysis of a query/entity
    
    Examples:
    - "Why was PR #123 reverted?"
    - "What caused the outage on 2024-01-15?"
    - "Trace the relationship between Issue-456 and PR-789"
    """
    try:
        result = memory_manager.investigate(
            query=request.query,
            entity_id=request.entity_id,
        )

        response = InvestigationQueryResponse(
            query=request.query,
            summary=result.summary,
            timeline=result.timeline,
            related_entities=[e.dict() for e in result.related_entities],
            state_changes=[s.dict() for s in result.state_changes],
            evidence_count=len(result.evidence),
            discovery_time=result.discovered_at.isoformat(),
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/investigate/entity/{entity_id}")
async def investigate_entity(entity_id: str):
    """
    Get full investigation history of an entity
    
    Entity ID format: source:type:identifier
    Examples:
    - github:pr:my-repo#123
    - jira:issue:PROJ-456
    - slack:message:C123456:1234567890
    """
    try:
        # Query about entity history
        query = f"Give me the complete history and all events related to {entity_id}"
        result = memory_manager.investigate(query, entity_id=entity_id)

        return {
            "entity_id": entity_id,
            "investigation": result.dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/investigate/entity/{entity_id}/relationships")
async def investigate_relationships(entity_id: str):
    """Find all entities related to a given entity"""
    try:
        result = memory_manager.trace_relationships(entity_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/investigate/entity/{entity_id}/state-changes")
async def investigate_state_changes(entity_id: str):
    """Get state change history for an entity"""
    try:
        query = (
            f"What are all the state changes for {entity_id}? "
            f"When did they happen and why?"
        )
        result = memory_manager.investigate(query, entity_id=entity_id)

        return {
            "entity_id": entity_id,
            "state_changes": result.state_changes,
            "summary": result.summary,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/investigate/why")
async def investigate_why(request: InvestigationRequest):
    """
    Explain WHY something happened
    Reframes query to find causal chain
    
    Examples:
    - "Why was the deployment rolled back?"
    - "Why didn't PR get approved?"
    """
    try:
        # Enhance query to be more causal
        enhanced_query = f"Why did {request.query}? Explain the chain of events that led to this."

        result = memory_manager.investigate(
            query=enhanced_query,
            entity_id=request.entity_id,
        )

        return {
            "original_query": request.query,
            "analysis": result.summary,
            "evidence": result.evidence,
            "confidence": result.confidence,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/investigate/timeline")
async def investigate_timeline(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
):
    """
    Get timeline of events in a date range
    
    Parameters:
    - start_date: ISO format (e.g., 2024-01-01)
    - end_date: ISO format (e.g., 2024-01-31)
    - entity_type: Filter by type (pr, issue, ticket, message, etc.)
    """
    try:
        filters = ""
        if entity_type:
            filters += f" of type {entity_type}"
        if start_date:
            filters += f" between {start_date}"
        if end_date:
            filters += f" and {end_date}"

        query = f"Show me all events{filters}. Order by timestamp."

        result = memory_manager.investigate(query)

        return {
            "query": query,
            "timeline": result.timeline,
            "event_count": len(result.timeline),
            "summary": result.summary,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint with API documentation
@app.get("/")
async def root():
    """Enterprise Knowledge Investigator API"""
    return {
        "name": "Enterprise Knowledge Investigator",
        "version": "1.0.0",
        "description": "AI-powered investigation using Reeve temporal knowledge graphs",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "ingestion": {
                "all": "POST /ingest/all",
                "github": "POST /ingest/github",
                "jira": "POST /ingest/jira",
                "slack": "POST /ingest/slack",
            },
            "investigation": {
                "query": "POST /investigate",
                "entity": "GET /investigate/entity/{entity_id}",
                "relationships": "GET /investigate/entity/{entity_id}/relationships",
                "state_changes": "GET /investigate/entity/{entity_id}/state-changes",
                "why": "POST /investigate/why",
                "timeline": "POST /investigate/timeline",
            },
        },
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    from config import app_config

    uvicorn.run(
        app,
        host=app_config.host,
        port=app_config.port,
        log_level="info",
    )
