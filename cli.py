"""
CLI interface for Enterprise Knowledge Investigator
Provides command-line access to investigation and ingestion
"""
import click
import json
from datetime import datetime
from orchestrator import DataOrchestrator
from memory_manager import ReeveMemoryManager
from config import validate_configuration


@click.group()
def cli():
    """Enterprise Knowledge Investigator - AI-powered investigation system"""
    pass


# Status commands
@cli.group()
def status():
    """Check system status and configuration"""
    pass


@status.command()
def check():
    """Check system status"""
    orchestrator = DataOrchestrator()
    status_info = orchestrator.get_status()
    click.echo(json.dumps(status_info, indent=2))


@status.command()
def config():
    """Check which data sources are configured"""
    config_status = validate_configuration()
    for source, is_configured in config_status.items():
        status_str = "✓ CONFIGURED" if is_configured else "✗ NOT CONFIGURED"
        click.echo(f"{source.upper()}: {status_str}")


# Ingestion commands
@cli.group()
def ingest():
    """Ingest data from sources"""
    pass


@ingest.command()
@click.option("--repos", multiple=True, help="GitHub repos to ingest")
@click.option("--projects", multiple=True, help="Jira projects to ingest")
def all(repos, projects):
    """Ingest from all configured sources"""
    orchestrator = DataOrchestrator()
    click.echo("Starting full ingestion...")
    result = orchestrator.ingest_all(
        github_repos=list(repos) if repos else None,
        jira_projects=list(projects) if projects else None,
    )
    click.echo(json.dumps(result, indent=2, default=str))


@ingest.command()
@click.option("--repos", multiple=True, help="Repos to ingest (default: all configured)")
def github(repos):
    """Ingest from GitHub"""
    orchestrator = DataOrchestrator()
    click.echo("Starting GitHub ingestion...")
    result = orchestrator.ingest_github(repos=list(repos) if repos else None)
    click.echo(json.dumps(result, indent=2, default=str))


@ingest.command()
@click.option("--projects", multiple=True, help="Projects to ingest (default: all configured)")
def jira(projects):
    """Ingest from Jira"""
    orchestrator = DataOrchestrator()
    click.echo("Starting Jira ingestion...")
    result = orchestrator.ingest_jira(projects=list(projects) if projects else None)
    click.echo(json.dumps(result, indent=2, default=str))


@ingest.command()
def slack():
    """Ingest from Slack"""
    orchestrator = DataOrchestrator()
    click.echo("Starting Slack ingestion...")
    result = orchestrator.ingest_slack()
    click.echo(json.dumps(result, indent=2, default=str))


@ingest.command()
def codebase():
    """Ingest from local codebase"""
    orchestrator = DataOrchestrator()
    click.echo("Starting codebase ingestion...")
    result = orchestrator.ingest_codebase()
    click.echo(json.dumps(result, indent=2, default=str))


# Investigation commands
@cli.group()
def investigate():
    """Investigate organizational events"""
    pass


@investigate.command()
@click.argument("query")
@click.option("--entity-id", help="Filter by entity ID")
def query(query, entity_id):
    """Query investigation system"""
    memory_manager = ReeveMemoryManager()
    click.echo(f"Investigating: {query}")
    result = memory_manager.investigate(query, entity_id=entity_id)
    
    click.echo("\n" + "="*60)
    click.echo("INVESTIGATION RESULT")
    click.echo("="*60)
    click.echo(f"Query: {result.query}")
    click.echo(f"\nSummary:\n{result.summary}")
    
    if result.state_changes:
        click.echo(f"\nState Changes ({len(result.state_changes)}):")
        for change in result.state_changes:
            click.echo(
                f"  - {change.previous_state} → {change.new_state} "
                f"(by {change.changed_by} at {change.timestamp})"
            )
    
    if result.related_entities:
        click.echo(f"\nRelated Entities ({len(result.related_entities)}):")
        for entity in result.related_entities:
            click.echo(f"  - {entity.id}: {entity.title}")
    
    click.echo(f"\nConfidence: {result.confidence * 100:.0f}%")
    click.echo(f"Discovered: {result.discovered_at}")


@investigate.command()
@click.argument("entity_id")
def entity(entity_id):
    """Get full history of an entity"""
    memory_manager = ReeveMemoryManager()
    click.echo(f"Retrieving history for: {entity_id}")
    history = memory_manager.get_entity_history(entity_id)
    
    click.echo(f"\n{'='*60}")
    click.echo(f"ENTITY HISTORY: {entity_id}")
    click.echo(f"{'='*60}")
    
    if history:
        for i, event in enumerate(history, 1):
            click.echo(f"\n{i}. {event}")
    else:
        click.echo("No history found.")


@investigate.command()
@click.argument("entity_id")
def relationships(entity_id):
    """Find entities related to a given entity"""
    memory_manager = ReeveMemoryManager()
    click.echo(f"Finding relationships for: {entity_id}")
    result = memory_manager.trace_relationships(entity_id)
    
    click.echo(f"\n{'='*60}")
    click.echo(f"RELATIONSHIPS: {entity_id}")
    click.echo(f"{'='*60}")
    click.echo(f"\nSummary:\n{result['summary']}")
    
    if result['related']:
        click.echo(f"\nRelated Entities ({len(result['related'])}):")
        for entity in result['related']:
            click.echo(f"  - {entity.id}: {entity.title}")
    else:
        click.echo("No related entities found.")


@investigate.command()
@click.argument("entity_id")
@click.argument("from_state")
@click.argument("to_state")
def why(entity_id, from_state, to_state):
    """Explain why an entity changed state"""
    memory_manager = ReeveMemoryManager()
    click.echo(f"Explaining: {entity_id} changed from {from_state} to {to_state}")
    explanation = memory_manager.explain_state_change(entity_id, from_state, to_state)
    
    click.echo(f"\n{'='*60}")
    click.echo("EXPLANATION")
    click.echo(f"{'='*60}")
    click.echo(f"\n{explanation}")


# Server commands
@cli.group()
def server():
    """Start the API server"""
    pass


@server.command()
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--port", default=8000, type=int, help="Server port")
@click.option("--debug", is_flag=True, help="Run in debug mode")
def start(host, port, debug):
    """Start the FastAPI server"""
    import uvicorn
    from main import app

    click.echo(f"Starting server on {host}:{port}")
    click.echo("API docs available at http://localhost:{port}/docs")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="debug" if debug else "info",
    )


if __name__ == "__main__":
    cli()
