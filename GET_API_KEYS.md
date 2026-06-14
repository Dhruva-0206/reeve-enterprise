# Getting API Keys - Step-by-Step Guide

## 1️⃣ REEVE API KEY

**URL**: https://mcp.reeve.co.in

**Steps**:
1. Go to https://mcp.reeve.co.in
2. Click "Sign In" or "Get Started"
3. Create account (email/password or GitHub login)
4. Go to dashboard
5. Click "Create API Key" or "Generate Key"
6. Copy the key (looks like: `sk-xxxxxxxxxxxx`)
7. Save in `.env`:
   ```
   REEVE_API_KEY=sk-xxxxxxxxxxxx
   ```

---

## 2️⃣ GITHUB PERSONAL ACCESS TOKEN

**URL**: https://github.com/settings/tokens

**Steps**:
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" (Classic)
3. Name it: `reeve-investigator` or similar
4. Set expiration: 90 days or 1 year
5. Select scopes (checkboxes):
   ```
   ✓ repo (full control of private repositories)
   ✓ read:org (read organization info)
   ✓ user:email (read user emails)
   ```
   For public repos only, use:
   ```
   ✓ public_repo (access public repos)
   ✓ read:org (read organization)
   ```
6. Click "Generate token"
7. **Copy the token immediately** (only shows once!)
   - Looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`
8. Save in `.env`:
   ```
   GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
   GITHUB_OWNER=your-organization-name
   GITHUB_REPOS=repo1,repo2,repo3
   ```

**Find your GITHUB_OWNER**:
- Go to https://github.com/settings/organizations
- Or https://github.com/your-username (click on org in sidebar)

---

## 3️⃣ JIRA API TOKEN

**URL**: https://id.atlassian.com/manage-profile/security/api-tokens

**Steps**:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Log in with your Atlassian account
3. Click "Create API token"
4. Name it: `reeve-investigator` or similar
5. **Copy the token immediately** (only shows once!)
   - Looks like: `ATATT3xxxxxxxxxxxxxxxxxxxxxxxxxxxx`
6. Save in `.env`:
   ```
   JIRA_URL=https://your-organization.atlassian.net
   JIRA_USERNAME=your-email@company.com
   JIRA_API_TOKEN=ATATT3xxxxxxxxxxxxxxxxxxxxxxxxxxxx
   JIRA_PROJECTS=PROJ1,PROJ2
   ```

**Find your JIRA_URL**:
- Go to https://www.atlassian.com/software/jira (if you use Cloud)
- Or your Jira instance URL (usually https://your-org.atlassian.net)

**Find your JIRA_USERNAME**:
- Your email address you use to log in to Jira

**Find your JIRA_PROJECTS**:
- Go to your Jira instance
- Click "Projects" in sidebar
- Each project has a key (e.g., PROJ, INFRA, ENGAGE)

---

## 4️⃣ SLACK BOT TOKEN

**URL**: https://api.slack.com/apps

**Steps**:

### Option A: Create New App (Recommended)

1. Go to https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. **App Name**: `reeve-investigator`
5. **Select workspace**: Choose your workspace
6. Click "Create App"

7. Go to "OAuth & Permissions" (left sidebar)

8. Under **Scopes → Bot Token Scopes**, add:
   ```
   ✓ channels:history (read channel history)
   ✓ channels:read (list channels)
   ✓ chat:write (send messages)
   ✓ users:read (read user info)
   ✓ team:read (read team info)
   ```

9. Scroll up to **OAuth Tokens for Your Workspace**
10. Click "Install to Workspace" (or "Reinstall to Workspace")
11. Click "Allow"
12. **Copy the Bot User OAuth Token**
    - Looks like: `xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxx`
13. Save in `.env`:
    ```
    SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxx
    SLACK_SIGNING_SECRET=your-signing-secret
    SLACK_CHANNELS=general,engineering,incidents
    ```

14. Get **Signing Secret**:
    - Go to "Basic Information" (left sidebar)
    - Scroll down to "App Credentials"
    - Copy "Signing Secret"
    - Save in `.env` as `SLACK_SIGNING_SECRET`

### Option B: Use Existing App

1. Go to https://api.slack.com/apps
2. Click your app
3. Go to "OAuth & Permissions"
4. Copy "Bot User OAuth Token"
5. Go to "Basic Information"
6. Copy "Signing Secret"

---

## 📝 Final .env File

```env
# Reeve Configuration
REEVE_API_KEY=sk-your-reeve-key
REEVE_NAMESPACE=organization_memory

# GitHub Configuration
GITHUB_TOKEN=ghp_your-github-token
GITHUB_OWNER=your-organization
GITHUB_REPOS=repo1,repo2,repo3

# Jira Configuration
JIRA_URL=https://your-org.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=ATATT3xxxxx
JIRA_PROJECTS=PROJ1,PROJ2

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-xxxxx
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_CHANNELS=general,engineering,incidents

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false
```

---

## ⚠️ IMPORTANT SECURITY NOTES

1. **NEVER commit `.env` to git** ✓ Already in `.gitignore`
2. **Keep tokens SECRET** - Don't share them
3. **Rotate tokens regularly** - Delete old ones from platforms
4. **Limit permissions** - Only grant what's needed
5. **Use different tokens** for different environments (dev, prod)

---

## ✅ Quick Checklist

- [ ] Created Reeve account & got API key
- [ ] Created GitHub token (public_repo scope minimum)
- [ ] Created Jira API token
- [ ] Created Slack bot token
- [ ] Added all tokens to `.env`
- [ ] Ran `python setup.py` to validate
- [ ] Ready to ingest data!

---

## 🚀 Next Steps

```bash
# 1. Validate configuration
python setup.py

# 2. If all green, ingest data
python cli.py ingest all

# 3. Start investigating
python cli.py investigate query "Why was PR reverted?"
```

**Stuck?** Run `python validate.py` to see which APIs are misconfigured.
