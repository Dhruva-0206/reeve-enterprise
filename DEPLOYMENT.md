# Deployment Guide

## Development Deployment

### Local Setup

1. **Clone and enter project**
   ```bash
   cd reeve_enterprise
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Validate setup**
   ```bash
   python setup.py
   ```

6. **Start development server**
   ```bash
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

Access API at: http://localhost:8000/docs

---

## Production Deployment

### Prerequisites
- Python 3.10+
- PostgreSQL or similar for persistence (optional, Reeve handles graph storage)
- Nginx or similar reverse proxy
- SSL certificate

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t knowledge-investigator .
docker run -p 8000:8000 \
  -e REEVE_API_KEY=$REEVE_API_KEY \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -e JIRA_URL=$JIRA_URL \
  knowledge-investigator
```

### Docker Compose Deployment

```yaml
version: '3.8'

services:
  investigator:
    build: .
    ports:
      - "8000:8000"
    environment:
      REEVE_API_KEY: ${REEVE_API_KEY}
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      GITHUB_OWNER: ${GITHUB_OWNER}
      GITHUB_REPOS: ${GITHUB_REPOS}
      JIRA_URL: ${JIRA_URL}
      JIRA_USERNAME: ${JIRA_USERNAME}
      JIRA_API_TOKEN: ${JIRA_API_TOKEN}
      JIRA_PROJECTS: ${JIRA_PROJECTS}
      SLACK_BOT_TOKEN: ${SLACK_BOT_TOKEN}
      SLACK_SIGNING_SECRET: ${SLACK_SIGNING_SECRET}
      SLACK_CHANNELS: ${SLACK_CHANNELS}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - investigator
```

Run with:
```bash
docker-compose up -d
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: knowledge-investigator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: knowledge-investigator
  template:
    metadata:
      labels:
        app: knowledge-investigator
    spec:
      containers:
      - name: investigator
        image: knowledge-investigator:latest
        ports:
        - containerPort: 8000
        env:
        - name: REEVE_API_KEY
          valueFrom:
            secretKeyRef:
              name: investigator-secrets
              key: reeve-api-key
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: investigator-secrets
              key: github-token
        # ... other env vars
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: knowledge-investigator-service
spec:
  selector:
    app: knowledge-investigator
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy with:
```bash
kubectl apply -f k8s-deployment.yaml
```

---

## Ingestion Strategies

### Strategy 1: Full Ingestion (One-Time)
```bash
python cli.py ingest all
```
- Pulls all data from all sources
- Stores in Reeve knowledge graph
- Use for initial setup

### Strategy 2: Incremental Ingestion
```bash
# Ingest specific repository
python cli.py ingest github --repos my-repo other-repo

# Ingest specific project
python cli.py ingest jira --projects PROJ1 PROJ2
```
- More targeted and faster
- Use for regular updates

### Strategy 3: Scheduled Ingestion (Cron)
```bash
# /etc/cron.d/knowledge-investigator
0 */6 * * * cd /opt/knowledge-investigator && python cli.py ingest all >> logs/cron.log 2>&1
```
- Runs every 6 hours
- Keeps memory graph up-to-date

### Strategy 4: Real-Time Webhooks (Future)
```bash
# GitHub Webhook → /webhooks/github
# Jira Webhook → /webhooks/jira
# Slack Events → /webhooks/slack
```
- Immediate data ingestion
- Requires webhook listener implementation

---

## Monitoring

### Health Checks

```bash
# Check service health
curl http://localhost:8000/health

# Get system status
curl http://localhost:8000/status

# Validate configuration
python cli.py status config
```

### Logging

```bash
# View application logs
tail -f logs/investigator.log

# View ingestion logs
tail -f logs/ingestion.log

# View API access logs
tail -f logs/access.log
```

### Metrics

```bash
# Check Reeve memory status
python cli.py status check

# Get configuration details
python cli.py status config
```

---

## Backup & Recovery

### Backup Reeve Knowledge Graph

```bash
# CLI command
python cli.py backup

# Exports full knowledge graph as JSON
# Output: backups/knowledge_graph_TIMESTAMP.json
```

### Restore from Backup

```python
# Manual restore (Python script)
import json
from reeve import store_memory

with open("backups/knowledge_graph_TIMESTAMP.json") as f:
    data = json.load(f)
    for fact in data["facts"]:
        store_memory(fact)
```

---

## Performance Tuning

### API Performance

1. **Rate Limiting** (add to main.py)
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/investigate")
@limiter.limit("10/minute")
async def investigate(request):
    ...
```

2. **Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_investigation(query: str):
    return memory_manager.investigate(query)
```

3. **Async Ingestion**
```python
import asyncio

async def ingest_all_async():
    await asyncio.gather(
        asyncio.to_thread(orchestrator.ingest_github),
        asyncio.to_thread(orchestrator.ingest_jira),
        asyncio.to_thread(orchestrator.ingest_slack),
    )
```

### Database Performance (Reeve)

1. **Consolidation** - Clean up old low-importance memories
```bash
# Reeve CLI
reeve consolidate
```

2. **Deduplication** - Remove redundant facts
```bash
reeve dedup
```

---

## Security

### API Security

1. **Authentication**
```python
from fastapi.security import HTTPBearer, HTTPAuthCredential

security = HTTPBearer()

@app.post("/investigate")
async def investigate(request: InvestigationRequest, credentials: HTTPAuthCredential = Depends(security)):
    # Verify token
    ...
```

2. **HTTPS/TLS**
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Run with SSL
uvicorn main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

### API Key Management

- Store API keys in environment variables (not in code)
- Use secret management (AWS Secrets Manager, HashiCorp Vault)
- Rotate keys regularly
- Monitor API key usage

```bash
# Use aws-vault or similar
aws-vault exec production -- python main.py
```

### Data Privacy

- Implement data retention policies
- Redact sensitive information
- Audit access logs
- GDPR compliance for Slack/personal data

---

## Troubleshooting

### Common Issues

**Issue: "Connection refused" when connecting to Reeve**
```bash
# Check Reeve API key
echo $REEVE_API_KEY

# Test connection
curl -H "Authorization: Bearer $REEVE_API_KEY" https://mcp.reeve.co.in/health
```

**Issue: GitHub API rate limit exceeded**
```bash
# Check rate limit
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit

# Solution: Use personal access token with appropriate scope
```

**Issue: Slow investigations**
```bash
# Check Reeve consolidation
python cli.py consolidate

# Increase API timeout
# Edit config.py: REEVE_TIMEOUT = 60  # seconds
```

---

## Maintenance

### Regular Tasks

- **Weekly**: Review logs, monitor API performance
- **Monthly**: Backup knowledge graph, check storage usage
- **Quarterly**: Update dependencies, security patches
- **Annually**: Full system audit, performance review

### Update Dependencies

```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade reeve

# Update all
pip install -r requirements.txt --upgrade
```

---

## Disaster Recovery Plan

1. **Data Loss**
   - Restore from latest backup: `python cli.py restore backups/latest.json`
   - Re-ingest from sources: `python cli.py ingest all`

2. **Service Outage**
   - Monitor health: `curl /health`
   - Restart container: `docker restart knowledge-investigator`
   - Check logs: `docker logs knowledge-investigator`

3. **Corruption**
   - Verify data: `python cli.py validate`
   - Rollback to previous version
   - Restore from backup
