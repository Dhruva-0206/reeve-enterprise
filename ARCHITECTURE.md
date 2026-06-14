# System Architecture & Design

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────┐
│           Enterprise Knowledge Investigator                 │
│              (Reeve-backed Investigation System)            │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ EXTERNAL DATA SOURCES                                    │
├──────────────────────────────────────────────────────────┤
│  GitHub API  │  Jira API  │  Slack API  │  Future: Docs │
│  (PRs, Issues, Commits)  │  (Tickets, State)  │         │
│  (Conversations)                                         │
└──────────────────────────────────────────────────────────┘
              │              │              │
              ▼              ▼              ▼
┌──────────────────────────────────────────────────────────┐
│ DATA INGESTION LAYER                                     │
├──────────────────────────────────────────────────────────┤
│  GitHubIngester  │  JiraIngester  │  SlackIngester      │
│  ├─ PR Events   │  ├─ Issues    │  ├─ Messages        │
│  ├─ Issues     │  ├─ Comments  │  ├─ Threads         │
│  └─ Commits    │  └─ Transitions│  └─ Mentions        │
└──────────────────────────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────┐
│ DATA NORMALIZATION                                       │
├──────────────────────────────────────────────────────────┤
│  NormalizedEvent {                                        │
│    • Entity (canonical ID, type, source)                │
│    • StateChange (previous → new, timestamp, reason)    │
│    • Relationships (source_id → target_id)              │
│    • Metadata (source-specific info)                    │
│  }                                                        │
└──────────────────────────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────┐
│ REEVE MEMORY INTEGRATION                                │
├──────────────────────────────────────────────────────────┤
│  ReeveMemoryManager {                                    │
│    • store_event() → [memory statements]               │
│    • investigate(query) → InvestigationResult          │
│    • get_entity_history()                              │
│    • trace_relationships()                             │
│    • explain_state_change()                            │
│  }                                                        │
└──────────────────────────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────┐
│ REEVE TEMPORAL KNOWLEDGE GRAPH                           │
├──────────────────────────────────────────────────────────┤
│  Neo4j-backed Graph {                                    │
│    • Entities (nodes)                                   │
│    • Relationships (edges)                              │
│    • State Changes (temporal tracking)                  │
│    • Entity Resolution (canonical nodes)                │
│  }                                                        │
│                                                          │
│  Supports:                                              │
│  • Temporal queries ("Was X true on date Y?")          │
│  • Relationship tracing ("Find all connected to X")    │
│  • Causality analysis ("Why did state change?")        │
│  • Importance scoring (≥0.75 bypass recency decay)     │
└──────────────────────────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────┐
│ QUERY INTERFACE LAYER                                   │
├──────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐               │
│  │ REST API       │  │ CLI            │               │
│  │ (main.py)      │  │ (cli.py)       │               │
│  ├────────────────┤  ├────────────────┤               │
│  │ /investigate   │  │ investigate    │               │
│  │ /entity/{id}   │  │ entity         │               │
│  │ /relationships │  │ relationships  │               │
│  │ /why           │  │ why            │               │
│  │ /timeline      │  │ status         │               │
│  └────────────────┘  └────────────────┘               │
└──────────────────────────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────┐
│ INVESTIGATION RESULTS                                    │
├──────────────────────────────────────────────────────────┤
│  InvestigationResult {                                  │
│    • summary: "Evidence and explanation"               │
│    • timeline: [events in order]                       │
│    • related_entities: [connected items]               │
│    • state_changes: [transitions with reasons]         │
│    • evidence: [supporting data with sources]          │
│    • confidence: 0-1 score                             │
│  }                                                        │
└──────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Ingestion Layer

**Purpose**: Extract data from external sources

**Components**:
- `ingester_github.py`: GitHub API v3 integration
  - Fetch PRs with state changes, relationships
  - Fetch issues with comment history
  - Fetch commits with metadata
  
- `ingester_jira.py`: Jira REST API integration
  - Fetch issues and ticket lifecycle
  - Track status transitions
  - Extract links and relationships
  
- `ingester_slack.py`: Slack API integration
  - Fetch channel messages and threads
  - Search for decision-related messages
  - Extract mentions and links

**Interface**:
```python
class GitHubIngester:
    def ingest_pull_requests(repo_name: str, limit: int) → list[NormalizedEvent]
    def ingest_issues(repo_name: str, limit: int) → list[NormalizedEvent]
    def ingest_commits(repo_name: str, limit: int) → list[NormalizedEvent]
```

### 2. Data Normalization

**Purpose**: Convert source-specific events to canonical format

**Key Models** (models.py):
```python
Entity                 # source:type:identifier
StateChange           # previous_state → new_state with reason
Relationship          # Links two entities
NormalizedEvent       # Canonical event representation
InvestigationResult   # Investigation result
```

**Why canonical format?**
- Enables cross-source relationship detection
- Allows unified querying across GitHub/Jira/Slack
- Makes Reeve storage consistent
- Simplifies downstream processing

### 3. Reeve Memory Integration

**Purpose**: Store events in temporal knowledge graph

**ReeveMemoryManager** (memory_manager.py):
```python
store_event(event: NormalizedEvent)          # Convert to statements, store in Reeve
investigate(query: str) → InvestigationResult # Query knowledge graph
get_entity_history(entity_id: str)           # Full timeline
trace_relationships(entity_id: str)          # Find connected entities
explain_state_change(entity_id, from, to)   # Why change happened
```

**How events become memory**:
1. NormalizedEvent → Memory statements (natural language)
2. Statements stored in Reeve with speaker="organization_memory"
3. Reeve parses statements into knowledge graph
4. Entity resolution creates canonical nodes
5. Relationships tracked with timestamps

**Example**:
```
Event: "PR#123 merged, fixed Issue#456"
↓
Memory statements:
- "PR#123 (github:pr:repo#123) was merged"
- "PR#123 fixed bug Issue#456 (github:issue:repo#456)"
- "State change: open → merged at 2024-01-15T10:30Z"
↓
Reeve Graph:
- Node: github:pr:repo#123 [type: PR]
- Node: github:issue:repo#456 [type: Issue]
- Edge: PR#123 --[fixes]--> Issue#456
- Property: state_change = {from: open, to: merged, timestamp: ...}
```

### 4. Orchestration

**Purpose**: Coordinate data ingestion and storage

**DataOrchestrator** (orchestrator.py):
```python
ingest_all()              # All sources
ingest_github(repos)      # GitHub only
ingest_jira(projects)     # Jira only
ingest_slack()            # Slack only
get_status()              # Configuration status
```

### 5. Query Interface

**Purpose**: Provide investigation capabilities

**REST API** (main.py):
- `/investigate` - General query
- `/investigate/entity/{id}` - Entity history
- `/investigate/entity/{id}/relationships` - Relationship tracing
- `/investigate/entity/{id}/state-changes` - State transitions
- `/investigate/why` - Causality analysis
- `/investigate/timeline` - Timeline view
- `/ingest/all`, `/ingest/github`, etc. - Control ingestion

**CLI** (cli.py):
```bash
python cli.py investigate query "Why was PR reverted?"
python cli.py investigate entity github:pr:repo#123
python cli.py investigate relationships github:pr:repo#123
python cli.py investigate why github:pr:repo#123 open merged
```

---

## Data Flow Examples

### Example 1: Investigating a Reverted PR

```
User Query: "Why was PR #123 reverted?"
    ↓
/investigate/why endpoint
    ↓
ReeveMemoryManager.investigate()
    ↓
Reeve query: "Why did github:pr:repo#123 change from merged to reverted?"
    ↓
Reeve Knowledge Graph returns:
    - PR#123 was merged at 10:00 (fixes Issue#456)
    - Issue#456 had race condition reported at 10:15
    - PR#123 was reverted at 10:45 (reason: race condition)
    - Slack message in #incidents at 10:16: "race condition on line 456"
    ↓
Result:
{
    "summary": "PR#123 was reverted due to race condition discovered 15min after merge. Issue#456 reported the problem, and it was confirmed in Slack discussions.",
    "evidence": [
        {"type": "state_change", "data": "merged→reverted", "reason": "race condition"},
        {"type": "issue", "data": "Issue#456: race condition"},
        {"type": "message", "data": "Slack: race condition on line 456"}
    ],
    "confidence": 0.92
}
```

### Example 2: Tracing a Service Outage

```
User Query: "What caused the outage at 14:00 on Jan 15?"
    ↓
/investigate endpoint with timeline filtering
    ↓
Reeve queries for events around that timestamp
    ↓
Connections traced:
    PR#789 (deployed 14:00) → feature code change → bug introduced
           → Issue#999 opened 14:15 → investigation in JIRA
           → Slack thread in #incidents discussing rollback
           → PR#800 reverts changes at 15:45
    ↓
Result includes:
    - Timeline of events
    - PR deployments
    - Error reports
    - Decisions made
    - Resolution actions
```

---

## Entity ID Scheme

**Format**: `source:type:identifier`

**Examples**:
```
github:pr:owner/repo#123              # PR
github:issue:owner/repo#456           # Issue
github:commit:owner/repo:abc123def    # Commit

jira:issue:PROJ-789                   # Jira ticket
jira:comment:PROJ-789:comment-id      # Comment

slack:message:C12345:1234567890       # Message
slack:user:U12345                     # User
slack:channel:C12345                  # Channel
```

**Benefits**:
- Globally unique across all sources
- Easy to parse and validate
- Contains source context
- Sortable and queryable

---

## Temporal Knowledge Graph Features

### 1. State Tracking
```
Entity Timeline:
github:pr:repo#123
├─ 2024-01-15 09:00: state=open (created)
├─ 2024-01-15 10:00: state=merged (by @alice, reason: fixes bug)
├─ 2024-01-15 10:45: state=reverted (by @bob, reason: race condition)
└─ 2024-01-15 11:00: state=closed (by @bob)
```

### 2. Relationship Resolution
```
github:pr:repo#123 --[fixes]--> github:issue:repo#456
                    --[mentions]--> jira:issue:PROJ-789
                    --[relates-to]--> slack:message:C123:timestamp
```

### 3. Entity Resolution
```
"PR 123" = "PR#123" = "Pull Request 123" = "that PR" = "it"
           → All resolve to: github:pr:repo#123
```

### 4. Importance-Based Retrieval
```
Memories with importance ≥ 0.75 (promotions, major changes, incidents):
    - Bypass recency decay
    - Always surface in results
    - Examples: deployments, rollbacks, incidents
```

---

## Investigation Types

### 1. Historical Reconstruction
"Give me the complete history of Issue#456"
- Timeline of all events
- Who changed what and when
- Context for each change

### 2. Causality Analysis
"Why did the deployment fail?"
- Root cause identification
- Chain of events leading to failure
- Contributing factors

### 3. Relationship Tracing
"Find everything connected to PR#123"
- Related issues
- Dependent PRs
- Discussions and decisions
- People involved

### 4. State Change Explanation
"Why did Ticket X move from 'In Progress' to 'Blocked'?"
- Decision context
- Blocker identification
- Timeline

### 5. Timeline Navigation
"What happened between Jan 15 10:00 and 11:00?"
- Events in time range
- State changes
- Relationships formed
- Decisions made

---

## Configuration Management

**Hierarchy** (config.py):
```
Environment Variables (.env)
        ↓
Config Classes
├─ ReveConfig (API key, namespace)
├─ GitHubConfig (token, owner, repos)
├─ JiraConfig (URL, credentials, projects)
├─ SlackConfig (tokens, channels)
└─ AppConfig (host, port, debug)
        ↓
Validation Functions
├─ validate_configuration() → Dict[source: bool]
└─ is_configured checks
```

---

## Error Handling Strategy

### Ingestion Errors
- Log detailed errors
- Continue with other sources
- Return partial results with error details
- Retry with exponential backoff for transient errors

### API Errors
- Rate limit: Pause and retry
- Authentication: Fail fast, alert user
- Network: Retry with exponential backoff
- Invalid data: Log and skip

### Reeve Errors
- Connection issues: Fail with message
- Query failures: Return error in result
- Storage failures: Log and alert

---

## Security Considerations

1. **API Key Management**
   - Store in environment variables only
   - Never commit to version control
   - Use secret management in production

2. **Data Access Control**
   - Single namespace (not multi-tenant in v1)
   - Future: Per-user namespaces

3. **Audit Trail**
   - Reeve maintains access history
   - Query logging
   - Investigation tracking

4. **Data Privacy**
   - GDPR compliance considerations
   - Slack personal data
   - GitHub user information
   - Jira user information

---

## Performance Characteristics

### Ingestion
- GitHub: ~5-10 seconds (100 PRs, 100 issues, 50 commits)
- Jira: ~3-5 seconds (100 issues + transitions)
- Slack: ~10-20 seconds (100 messages per channel)
- Total for full ingest: ~30-50 seconds with all sources

### Investigation
- Simple query: ~500ms
- Complex relationship trace: ~1-2 seconds
- Timeline construction: ~1-3 seconds

### Memory Graph
- Entities: Scales to 100k+ without performance degradation
- Relationships: 1M+ relationships maintained
- Queries: Sub-second for typical investigations

---

## Future Enhancements

1. **Real-time Webhooks**
   - GitHub push events
   - Jira webhook events
   - Slack Event API integration

2. **Additional Sources**
   - Meeting transcript ingestion
   - Postmortem document parsing
   - Deployment log analysis
   - Email threading

3. **Advanced Features**
   - Multi-tenant support
   - Role-based access control
   - Investigation sharing
   - Report generation
   - Anomaly detection

4. **Interface Improvements**
   - Interactive web dashboard
   - Visual graph exploration
   - Timeline visualization
   - Investigation export (PDF/HTML)
