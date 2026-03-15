# MCP Servers

Model Context Protocol (MCP) servers for various integrations — usable by **Claude Desktop** via `stdio` and by a **LangChain Agent** (with Streamlit UI) via HTTP-SSE.

---

## Architecture Overview

```
Claude Desktop  ──── stdio ────►  servers/weather.py
                                  servers/jira.py
                                  servers/confluence.py
                                  servers/zendesk.py
                                        ▲
                                  (same server code, reused)
                                        │
LangChain Agent ──── HTTP-SSE ──► sse_servers/weather_sse.py  :8001
  (Streamlit UI)                  sse_servers/jira_sse.py     :8002
                                  sse_servers/confluence_sse.py :8003
                                  sse_servers/zendesk_sse.py  :8004
```

> ✅ Claude Desktop and the LangChain Agent run **completely independently** — no conflicts, no shared ports.

---

## Available Servers

| Server | Description | API |
|--------|-------------|-----|
| **Weather** | National Weather Service integration | Free, no key needed |
| **Jira** | Jira Cloud integration | Requires API token |
| **Confluence** | Confluence Cloud integration | Requires API token |
| **Zendesk** | Zendesk Support integration | Requires API token |

---

## Project Structure

```
MCP/
├── .env                      # Credentials (never commit!)
├── .env.example              # Credentials template
├── .gitignore
├── README.md
├── requirements.txt
├── servers/                  # MCP server implementations (Claude Desktop / stdio)
│   ├── weather.py
│   ├── jira.py
│   ├── confluence.py
│   └── zendesk.py
├── sse_servers/              # SSE wrappers (LangChain / HTTP-SSE)
│   ├── weather_sse.py        # → port 8001
│   ├── jira_sse.py           # → port 8002
│   ├── confluence_sse.py     # → port 8003
│   └── zendesk_sse.py        # → port 8004
├── agents/
│   └── mcp_agent.py          # LangChain agent (Azure OpenAI)
├── ui/
│   └── app.py                # Streamlit chat UI
├── config/
│   └── settings.py           # Centralised config (reads from .env)
├── scripts/
│   ├── start_sse_servers.sh  # Starts all 4 SSE servers
│   └── start_ui.sh           # Starts Streamlit UI
├── utils/                    # Shared utilities
├── tests/                    # Test files
└── learning/                 # Learning notes
```

---

## Setup

### 1. Clone & Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
LOG_LEVEL=INFO

# Jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token-here

# Confluence (usually same credentials as Jira)
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token-here

# Zendesk
ZENDESK_URL=https://your-company.zendesk.com
ZENDESK_EMAIL=your-email@example.com
ZENDESK_API_TOKEN=your-zendesk-api-token

# Azure OpenAI (used by LangChain agent)
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

> **Atlassian API Token:** https://id.atlassian.com/manage-profile/security/api-tokens  
> **Zendesk API Token:** Admin Center → Apps & Integrations → APIs → Zendesk API  
> **Azure OpenAI:** Azure Portal → Your OpenAI Resource → Keys and Endpoint  
> ⚠️ `AZURE_OPENAI_ENDPOINT` must be the **base URL only** (e.g. `https://xxx.cognitiveservices.azure.com/`) — do not include the deployment path.

---

## Option A — Claude Desktop (stdio)

### Step 1: Find the Config File
```bash
open ~/Library/Application\ Support/Claude/
```

### Step 2: Edit `claude_desktop_config.json`
```json
{
  "mcpServers": {
    "weather": {
      "command": "/path/to/MCP/.venv/bin/python3",
      "args": ["-m", "servers.weather"],
      "cwd": "/path/to/MCP",
      "env": { "PYTHONPATH": "/path/to/MCP" }
    },
    "jira": {
      "command": "/path/to/MCP/.venv/bin/python3",
      "args": ["-m", "servers.jira"],
      "cwd": "/path/to/MCP",
      "env": { "PYTHONPATH": "/path/to/MCP" }
    },
    "confluence": {
      "command": "/path/to/MCP/.venv/bin/python3",
      "args": ["-m", "servers.confluence"],
      "cwd": "/path/to/MCP",
      "env": { "PYTHONPATH": "/path/to/MCP" }
    },
    "zendesk": {
      "command": "/path/to/MCP/.venv/bin/python3",
      "args": ["-m", "servers.zendesk"],
      "cwd": "/path/to/MCP",
      "env": { "PYTHONPATH": "/path/to/MCP" }
    }
  }
}
```
> Replace `/path/to/MCP` with your actual project path, e.g. `/Users/yourname/Desktop/Arul Learning /MCP`

### Step 3: Restart Claude Desktop
```
CMD + Q  →  Reopen Claude Desktop
```

### Step 4: Verify
- Open Claude Desktop → **Connectors** section
- You should see ✅ `weather` ✅ `jira` ✅ `confluence` ✅ `zendesk`

---

## Option B — LangChain Agent + Streamlit UI (HTTP-SSE)

### Step 1: Start SSE Servers (Terminal 1)
```bash
./scripts/start_sse_servers.sh
```
This starts all 4 MCP servers as HTTP-SSE endpoints:
```
✅ Weather    SSE → http://localhost:8001/sse
✅ Jira       SSE → http://localhost:8002/sse
✅ Confluence SSE → http://localhost:8003/sse
✅ Zendesk    SSE → http://localhost:8004/sse
```

### Step 2: Start Streamlit UI (Terminal 2)
```bash
./scripts/start_ui.sh
```

### Step 3: Open the UI
Go to 👉 **http://localhost:8501**

1. Click **"🔌 Connect to MCP Servers"** in the sidebar
2. Wait for ✅ Connected — all tools will be listed
3. Start chatting or use the **Quick Prompts**

---

## Sample Prompts

```
# Weather
Get weather alerts for CA
Get the forecast for San Francisco

# Jira
List all projects in my Jira account
Show all open issues in project TC
Create a new bug ticket with high priority

# Confluence
List all spaces in my Confluence account
Search for pages about "API"
Create a new page in the Engineering space

# Zendesk
Show all open tickets
Create a ticket about login issue with high priority
Add a comment to ticket #5
```

---

## Available Tools

### Weather Server
| Tool | Description |
|------|-------------|
| `get_alerts` | Get weather alerts for a US state |
| `get_forecast` | Get forecast by latitude/longitude |

### Jira Server
| Tool | Description |
|------|-------------|
| `get_projects` | List all Jira projects |
| `create_issue` | Create a new issue |
| `get_issue` | Get issue details |
| `search_issues` | Search using JQL |
| `update_issue` | Update issue fields |
| `add_comment` | Add comment to issue |
| `transition_issue` | Move issue through workflow |
| `get_project_issues` | Get all issues in a project |
| `get_issue_types` | Get available issue types |

### Confluence Server
| Tool | Description |
|------|-------------|
| `get_spaces` | List all Confluence spaces |
| `get_page` | Get page details and content |
| `search_pages` | Search pages using CQL |
| `create_page` | Create a new page |
| `update_page` | Update existing page |
| `add_comment_to_page` | Add comment to a page |
| `get_space_pages` | Get all pages in a space |

### Zendesk Server
| Tool | Description |
|------|-------------|
| `get_tickets` | Get tickets by status (open, pending, solved, all) |
| `get_ticket` | Get full ticket details |
| `create_ticket` | Create a new support ticket |
| `update_ticket` | Update ticket status or priority |
| `add_comment_to_ticket` | Add public or internal comment |
| `search_tickets` | Search tickets by keyword or filter |
| `get_ticket_comments` | Get all comments on a ticket |
| `get_users` | List users by role |
| `upload_text_as_attachment` | Upload text content as a file (get token) |
| `upload_attachment` | Upload a local file by path (get token) |
| `attach_file_to_ticket` | Attach an uploaded file to a ticket using token |
| `upload_and_attach_text` | Upload text + attach to ticket in one step ⭐ |
| `create_ticket_with_text_attachment` | Create ticket + attach file in one step ⭐ |

> ⭐ **Recommended**: Use `upload_and_attach_text` to attach AI-generated content directly to a ticket.

---

## Transport Comparison

| | Claude Desktop | LangChain + Streamlit |
|--|--|--|
| **Transport** | `stdio` | `HTTP-SSE` |
| **Server files** | `servers/*.py` | `sse_servers/*.py` (thin wrappers) |
| **LLM** | Claude (managed by Anthropic) | Azure OpenAI via LangChain |
| **Start** | Auto (Claude manages) | `./scripts/start_sse_servers.sh` |
| **UI** | Claude Desktop app | Browser at `localhost:8501` |
| **Multi-client** | ❌ Single session | ✅ Multiple users |

---

## Monitoring Logs

```bash
# Claude Desktop server logs
tail -f ~/Library/Logs/Claude/mcp-server-jira.log
tail -f ~/Library/Logs/Claude/mcp-server-weather.log
tail -f ~/Library/Logs/Claude/mcp-server-confluence.log
tail -f ~/Library/Logs/Claude/mcp-server-zendesk.log
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Server not in Claude connectors | Restart Claude Desktop (CMD+Q) |
| Authentication error | Check API token in `.env` |
| Tools not loading | Check `cwd` and `PYTHONPATH` in config |
| Import errors | Run `source .venv/bin/activate` |
| Confluence 404 error | Check `CONFLUENCE_URL` has no trailing slash |
| Zendesk 401 error | Ensure email format is `email/token:TOKEN` |
| New tools not appearing | Clear `__pycache__` and restart Claude Desktop |
| SSE connection refused | Make sure `start_sse_servers.sh` is running |
| Azure OpenAI 404 error | Check `AZURE_OPENAI_ENDPOINT` is base URL only (no `/openai/deployments/...`) |
| Azure OpenAI 401 error | Check `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_DEPLOYMENT_NAME` in `.env` |
| Streamlit event loop error | Agent uses background threading — no `asyncio` changes needed |
