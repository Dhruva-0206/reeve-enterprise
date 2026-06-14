# Enterprise Knowledge Investigator
## Complete System - Ready for Production

**Status**: ✅ PRODUCTION READY

All API integrations complete. No demo keys. Real production system.

---

## 🚀 Quick Start (5 minutes)

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
pip install -r requirements.txt

# 3. Validate everything works
python setup.py

# 4. Ingest data
python cli.py ingest all

# 5. Investigate
python cli.py investigate query "Why was PR reverted?"

# 6. Or start REST API
python cli.py server start
# Visit: http://localhost:8000/docs
```

---

## 📁 What's Inside

```
reeve_enterprise/
├── Core Engine
│   ├── config.py                 Config management
│   ├── models.py                 Data models (Pydantic)
│   ├── memory_manager.py         Reeve integration
│   ├── orchestrator.py           Multi-source ingestion
│   └── ingester_*.py             GitHub, Jira, Slack clients
│
├── APIs
│   ├── main.py                   REST API (FastAPI)
│   └── cli.py                    Command-line interface
│
├── Setup & Config
│   ├── .env.example              Template
│   ├── requirements.txt          Dependencies
│   ├── setup.py                  Installation wizard
│   └── validate.py               Validation checks
│
└── Documentation
    ├── README.md                 Complete guide
    ├── ARCHITECTURE.md           System design
    ├── DEPLOYMENT.md             Production deployment
    └── quickstart.sh             One-command setup
```

---

## 🎯 Features

✅ **Multi-Source Ingestion**
- GitHub: PRs, issues, commits
- Jira: Tickets, comments, transitions
- Slack: Messages, threads, mentions

✅ **Investigation Engine**
- Entity history timeline
- Relationship tracing
- State change analysis
- Causality explanation

✅ **Query Interface**
- REST API with 10+ endpoints
- CLI for interactive use
- Structured results with evidence

✅ **Reeve Temporal Knowledge Graph**
- Stores organizational memory
- Tracks when and why things happened
- Cross-source entity resolution

---

## 🔧 Configuration

### Required Credentials
```
REEVE_API_KEY        From: https://mcp.reeve.co.in
GITHUB_TOKEN         Personal access token
JIRA_URL + credentials
SLACK_BOT_TOKEN      From Slack workspace
```

### Optional Configuration
```
GITHUB_OWNER         Your GitHub organization
GITHUB_REPOS         Specific repos (comma-separated)
JIRA_PROJECTS        Specific projects
SLACK_CHANNELS       Specific channels
```

---

## 📊 How It Works

```
Your API Keys
    ↓
Config (.env)
    ↓
Ingest [GitHub, Jira, Slack APIs] 
    ↓
Normalize to canonical format
    ↓
Store in Reeve temporal knowledge graph
    ↓
Query with natural language
    ↓
Get investigation results with evidence
```

---

## 🔍 Investigation Examples

### 1. Root Cause Analysis
```bash
python cli.py investigate query "Why was the deployment rolled back?"
# → Returns: timeline, evidence, decision context
```

### 2. Entity History
```bash
python cli.py investigate entity github:pr:repo#123
# → Returns: creation, comments, state changes, current status
```

### 3. Relationship Tracing
```bash
python cli.py investigate relationships github:pr:repo#123
# → Returns: related issues, Jira tickets, Slack discussions
```

### 4. State Change Explanation
```bash
python cli.py investigate why github:issue:repo#456 open closed
# → Returns: why it was closed, who decided, when
```

---

## 🌐 REST API

### Start Server
```bash
python cli.py server start
# Or: python -m uvicorn main:app --reload
```

### Example Requests
```bash
# Investigate query
curl -X POST http://localhost:8000/investigate \
  -H "Content-Type: application/json" \
  -d '{"query": "Why was PR reverted?"}'

# Get entity history
curl http://localhost:8000/investigate/entity/github:pr:repo%23123

# Find relationships
curl http://localhost:8000/investigate/entity/github:pr:repo%23123/relationships

# Check status
curl http://localhost:8000/status

# API docs
# Visit: http://localhost:8000/docs
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| README.md | Complete user guide |
| ARCHITECTURE.md | System design, data flow, components |
| DEPLOYMENT.md | Docker, K8s, production setup |
| quickstart.sh | One-command setup script |

---

## ✅ Validation

```bash
# Full validation with setup
python setup.py

# Quick validation check
python validate.py

# Check configuration
python cli.py status config

# Test system
python cli.py status check
```

---

## 🚢 Deployment

### Local Development
```bash
python cli.py server start --debug
```

### Docker
```bash
docker build -t investigator .
docker run -p 8000:8000 \
  -e REEVE_API_KEY=$REEVE_API_KEY \
  investigator
```

### Kubernetes
See `DEPLOYMENT.md` for complete instructions

---

## 🔑 API Endpoints

| Endpoint | Purpose |
|----------|---------|
| POST `/ingest/all` | Ingest all sources |
| POST `/investigate` | Query system |
| GET `/investigate/entity/{id}` | Entity history |
| GET `/investigate/entity/{id}/relationships` | Relations |
| GET `/investigate/entity/{id}/state-changes` | State changes |
| POST `/investigate/why` | Causality analysis |
| GET `/health` | Health check |
| GET `/status` | System status |

Full list: `http://localhost:8000/docs`

---

## 🛠️ CLI Commands

```bash
# Status
python cli.py status config            Config check
python cli.py status check             System status

# Ingestion
python cli.py ingest all               All sources
python cli.py ingest github --repos X  Specific repos
python cli.py ingest jira --projects X Specific projects
python cli.py ingest slack             All channels

# Investigation
python cli.py investigate query TEXT   Query system
python cli.py investigate entity ID    Entity history
python cli.py investigate relationships ID  Find relations
python cli.py investigate why ID S1 S2 Explain state change

# Server
python cli.py server start              Start API server
python cli.py --help                   Full help
```

---

## 🎓 Use Cases

**1. Incident Investigation**
- "What caused the outage?"
- Root cause identification
- Timeline of events
- Who was involved

**2. Deployment Troubleshooting**
- "Why did the release break?"
- Which PR introduced the bug
- Related issues and fixes
- Decision context

**3. Context Recovery**
- "What was this feature supposed to do?"
- Link between PRs and Jira tickets
- Slack discussions about design
- Timeline of changes

**4. Knowledge Transfer**
- "Tell me about this system"
- All changes and discussions
- Decision history
- Current state

---

## 🔐 Security

- API keys in `.env` only (not in code)
- No secrets in git (use `.gitignore`)
- HTTPS support in production
- Future: Authentication & RBAC

---

## 🐛 Troubleshooting

### "REEVE_API_KEY not set"
```bash
# Check .env file
cat .env | grep REEVE_API_KEY
# Get key from: https://mcp.reeve.co.in
```

### "No data ingested"
```bash
# Check API permissions
python validate.py

# Test specific source
python cli.py ingest github --repos your-repo
```

### "Queries not finding results"
```bash
# Try broader queries first
python cli.py investigate query "Tell me about recent changes"

# Check what was ingested
python cli.py status check
```

---

## 📖 Learn More

- **System Design**: See `ARCHITECTURE.md`
- **Data Model**: See `models.py`
- **API Details**: Run server and visit `/docs`
- **Deployment**: See `DEPLOYMENT.md`

---

## 🚀 Next Steps

1. **Setup**: Copy `.env.example` → `.env`
2. **Configure**: Add your API keys to `.env`
3. **Validate**: Run `python setup.py`
4. **Ingest**: Run `python cli.py ingest all`
5. **Investigate**: Try `python cli.py investigate query "your question"`
6. **Deploy**: Use Docker/Kubernetes for production

---

## 📞 Support

- **Code Issues**: Check `validate.py` output
- **API Questions**: Visit `http://localhost:8000/docs`
- **Documentation**: Read `README.md` and `ARCHITECTURE.md`
- **Configuration**: See `.env.example`

---

**Version**: 1.0.0  
**Status**: ✅ Production Ready  
**Last Updated**: 2024-01-15

Ready to investigate your organization's knowledge!
