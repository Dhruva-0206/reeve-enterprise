# Enterprise Knowledge Investigator

**AI-powered investigation system** using Reeve temporal knowledge graphs to trace organizational events, find evidence, and explain WHY something happened.

## Problem

Modern organizations produce massive amounts of data daily across scattered systems:
- Slack conversations
- Jira tickets
- GitHub PRs and issues
- Meeting notes
- Postmortems
- Deployment logs

**The Problem:** Over time, information stays but context is lost. When something breaks or decisions need explaining, you can't easily trace the chain of events or understand the reasoning behind what happened.

## Solution

This system wraps **Reeve** (temporal knowledge graph for AI) to build an "investigator" that:
- ✅ Ingests data directly from GitHub, Jira, Slack APIs
- ✅ Stores events in Reeve's temporal knowledge graph
- ✅ Finds relationships and connections across sources
- ✅ Tracks state changes with context
- ✅ Explains WHY something happened by tracing evidence

## Quick Start

### 1. Prerequisites

- Python 3.10+
- API keys for:
  - **Reeve**: https://mcp.reeve.co.in (get API key)
  - **GitHub**: Personal access token
  - **Jira**: API token + account email
  - **Slack**: Bot token

### 2. Installation

```bash
# Clone/setup project
cd reeve_enterprise

# Install dependencies
pip install -r requirements.txt

# Copy environment template and add your API keys
cp .env.example .env
# Edit .env with your credentials
```

### 3. Configure API Keys

Edit `.env` with your credentials:

```env
# Reeve
REEVE_API_KEY=sk-your-reeve-api-key

# GitHub
GITHUB_TOKEN=ghp_your-token
GITHUB_OWNER=your-org
GITHUB_REPOS=repo1,repo2

# Jira
JIRA_URL=https://your-org.atlassian.net
JIRA_USERNAME=email@company.com
JIRA_API_TOKEN=your-token
JIRA_PROJECTS=PROJ1,PROJ2

# Slack
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNELS=general,engineering
```

### 4. Start the Server

```bash
python -m uvicorn main:app --reload --port 8000
```

Visit: http://localhost:8000/docs for interactive API documentation

---

## Usage

### Via REST API

#### Ingest data from all sources
```bash
curl -X POST http://localhost:8000/ingest/all
```

#### Investigate a query
```bash
curl -X POST http://localhost:8000/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Why was PR #123 reverted?",
    "entity_id": "github:pr:repo#123"
  }'
```

#### Get entity history
```bash
curl http://localhost:8000/investigate/entity/github:pr:repo%23123
```

#### Find relationships
```bash
curl http://localhost:8000/investigate/entity/github:pr:repo%23123/relationships
```

#### Trace state changes
```bash
curl http://localhost:8000/investigate/entity/jira:issue:PROJ-456/state-changes
```

### Via CLI

```bash
# Check configuration
python cli.py status check
python cli.py status config

# Ingest data
python cli.py ingest all
python cli.py ingest github --repos my-repo
python cli.py ingest jira --projects PROJ1
python cli.py ingest slack

# Investigate
python cli.py investigate query "Why was the deployment rolled back?"
python cli.py investigate entity github:pr:repo#123
python cli.py investigate relationships github:pr:repo#123
python cli.py investigate why github:pr:repo#123 open merged

# Start server
python cli.py server start --host 0.0.0.0 --port 8000
```

---

## Architecture

### Data Flow

```
GitHub API ─┐
Jira API ───┼─> Ingesters ──> Normalizers ──> ReeveMemoryManager ──> Temporal Knowledge Graph
Slack API ──┘                                          │
                                                       ├─> store_memory()
                                                       └─> query_memory()
                                             
Query Interface (REST API / CLI) ──> investigate() ──> retrieve_memory_context()
```

### Key Components

1. **Ingesters** (ingester_*.py)
   - Pull data from GitHub, Jira, Slack APIs
   - Handle real-time updates (webhooks in future)

2. **Data Normalization** (models.py)
   - Convert source-specific data to canonical format
   - Track relationships and state changes

3. **Reeve Memory Manager** (memory_manager.py)
   - Store normalized events in Reeve
   - Query temporal knowledge graph
   - Find relationships and trace causality

4. **Orchestrator** (orchestrator.py)
   - Coordinates multi-source ingestion
   - Manages ingester initialization

5. **REST API** (main.py)
   - Investigation query endpoints
   - Ingestion controls
   - Presentable result formatting

6. **CLI** (cli.py)
   - Command-line interface
   - Admin operations
   - Interactive investigation

---

## Investigation Types

### Query Investigation
"Why did X happen?" - Find causes, decisions, events that led to outcome

```bash
curl -X POST http://localhost:8000/investigate/why \
  -H "Content-Type: application/json" \
  -d '{"query": "deployment failed"}'
```

### Entity History
Complete timeline of an entity from creation to current state

```bash
curl http://localhost:8000/investigate/entity/github:pr:repo%23123
```

### Relationship Tracing
Find all connected entities (PR → Issue → Jira Ticket → Slack discussion)

```bash
curl http://localhost:8000/investigate/entity/github:pr:repo%23123/relationships
```

### State Change Analysis
Track and explain why an entity changed states

```bash
curl http://localhost:8000/investigate/entity/jira:issue:PROJ-456/state-changes
```

### Timeline Investigation
Events in a specific date range or entity type

```bash
curl -X POST http://localhost:8000/investigate/timeline \
  ?start_date=2024-01-01&end_date=2024-01-31&entity_type=pr
```

---

## Entity ID Format

All entities use canonical IDs: `source:type:identifier`

**GitHub:**
- PR: `github:pr:owner/repo#123`
- Issue: `github:issue:owner/repo#456`
- Commit: `github:commit:owner/repo:abc123`

**Jira:**
- Issue: `jira:issue:PROJ-123`
- Comment: `jira:comment:PROJ-123:comment-id`

**Slack:**
- Message: `slack:message:C12345678:1234567890_000000`
- User: `slack:user:U12345678`

---

## Reeve Integration

Reeve stores relationships, state changes, and timeline as a temporal knowledge graph:

```python
from reeve import store_memory, query_memory

# Store event
store_memory(
    "PR#123 merged after being open for 2 days. It fixed bug reported in Issue#456",
    speaker="organization_memory"
)

# Query relationships
answer = query_memory(
    "What was PR#123 trying to fix?",
    speaker="organization_memory"
)
# → "PR#123 fixed bug reported in Issue#456"
```

**Key Features:**
- **Entity Resolution**: "PR123", "Pull Request 123", "that PR" all resolve to same entity
- **State Tracking**: Remembers state transitions (open → merged → reverted)
- **Temporal Awareness**: Knows when changes happened and who made them
- **Relationship Memory**: Maintains connections across all sources

---

## Configuration Validation

Before using the system, validate configurations:

```bash
python cli.py status config
```

Output:
```
GITHUB: ✓ CONFIGURED
JIRA: ✓ CONFIGURED
SLACK: ✗ NOT CONFIGURED
REEVE: ✓ CONFIGURED
```

Only configured sources will be ingested.

---

## Example Investigation

**Scenario:** A critical service was down for 2 hours. Investigate why.

```bash
# 1. Ingest recent data
python cli.py ingest all

# 2. Query about the incident
python cli.py investigate query "What happened around 14:00 on 2024-01-15?"

# 3. Find related entities
python cli.py investigate entity github:pr:repo#789

# 4. Understand state changes
python cli.py investigate state-changes jira:issue:INFRA-123

# 5. Trace why decision was made
python cli.py investigate why github:pr:repo#789 open merged
```

**Result:** Investigation reveals:
- PR#789 deployed new feature at 14:00 (merged commit)
- Feature had race condition in checkout logic
- Investigation ticket INFRA-123 opened at 14:15
- PR reverted at 15:45
- Root cause identified in Slack thread: "race condition on line 456"

---

## API Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| GET | `/status` | System status |
| POST | `/ingest/all` | Ingest all sources |
| POST | `/ingest/github` | Ingest GitHub only |
| POST | `/ingest/jira` | Ingest Jira only |
| POST | `/ingest/slack` | Ingest Slack only |
| POST | `/investigate` | General investigation query |
| GET | `/investigate/entity/{id}` | Entity history |
| GET | `/investigate/entity/{id}/relationships` | Find relationships |
| GET | `/investigate/entity/{id}/state-changes` | State changes |
| POST | `/investigate/why` | Explain causality |
| POST | `/investigate/timeline` | Timeline view |

---

## Limitations & Future Work

### Current Limitations
- Single organization only (not multi-tenant in v1)
- GitHub, Jira, Slack focus (others as secondary)
- No real-time webhooks yet
- No deduplication of cross-source entities yet

### Future Enhancements
- [ ] Real-time webhook listeners
- [ ] Cross-source entity deduplication
- [ ] Meeting transcript ingestion
- [ ] Postmortem document parsing
- [ ] Deployment log integration
- [ ] Multi-tenant support
- [ ] Interactive web dashboard
- [ ] Export investigations as reports

---

## Troubleshooting

### "REEVE_API_KEY not set"
```bash
# Make sure .env file exists and has REEVE_API_KEY
cat .env | grep REEVE_API_KEY
```

### "GitHub not configured"
```bash
# Verify GitHub configuration
echo "GITHUB_TOKEN: $GITHUB_TOKEN"
echo "GITHUB_OWNER: $GITHUB_OWNER"
```

### "No events ingested"
- Check API token permissions
- Verify repos/projects/channels exist and are accessible
- Check rate limits: `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit`

### Reeve memory not retrieving expected results
- Ensure data was successfully ingested: Check logs for "stored" count
- Wait for Reeve processing (may take a few seconds)
- Try broader queries first, then refine

---

## Development

### Add a new data source

1. Create `ingester_newsource.py` with normalizer
2. Update `config.py` with configuration
3. Update `orchestrator.py` to initialize and ingest
4. Add API endpoint in `main.py`
5. Add CLI command in `cli.py`

### Running tests

```bash
pytest tests/ -v
```

---

## License

MIT

---

## Support

For issues, questions, or contributions, please check the documentation or submit an issue.
