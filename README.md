# MCP Servers

Model Context Protocol (MCP) servers for various integrations.

---

## Available Servers

| Server | Description | API |
|--------|-------------|-----|
| **Weather** | National Weather Service integration | Free, no key needed |
| **Jira** | Jira Cloud integration | Requires API token |
| **Confluence** | Confluence Cloud integration | Requires API token |
| **Zendesk** | Zendesk Support integration | Requires API token |

---

## Setup

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Mac/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

Your `.env` file:
```
LOG_LEVEL=INFO

# Jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token-here

# Confluence (same credentials as Jira)
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token-here

# Zendesk
ZENDESK_URL=https://your-company.zendesk.com
ZENDESK_EMAIL=your-email@example.com
ZENDESK_API_TOKEN=your-zendesk-api-token
```

> **Atlassian API Token:** https://id.atlassian.com/manage-profile/security/api-tokens  
> **Zendesk API Token:** Admin Center → Apps & Integrations → APIs → Zendesk API → Add API Token

---

## Running Servers

### Weather Server
```bash
python -m servers.weather
```

### Jira Server
```bash
python -m servers.jira
```

### Confluence Server
```bash
python -m servers.confluence
```

### Zendesk Server
```bash
python -m servers.zendesk
```

---

## Claude Desktop Configuration

### Step 1: Find the Config File
```bash
open ~/Library/Application\ Support/Claude/
```

### Step 2: Edit `claude_desktop_config.json`
```json
{
  "mcpServers": {
    "jira": {
      "command": "/path/to/MCP/.venv/bin/python3",
      "args": ["-m", "servers.jira"],
      "cwd": "/path/to/MCP",
      "env": { "PYTHONPATH": "/path/to/MCP" }
    },
    "weather": {
      "command": "/path/to/MCP/.venv/bin/python3",
      "args": ["-m", "servers.weather"],
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

> Replace `/path/to/MCP` with your actual project path.  
> e.g. `/Users/yourname/Desktop/Arul Learning /MCP`

### Step 3: Restart Claude Desktop
```
CMD + Q  →  Reopen Claude Desktop
```

### Step 4: Verify Connection
- Open Claude Desktop → **Connectors** section
- You should see ✅ `jira` ✅ `weather` ✅ `confluence` ✅ `zendesk` connected

### Step 5: Test with These Prompts
```
# Jira
List all projects in my Jira account
Show all issues in project TC

# Weather
Get weather alerts for CA

# Confluence
List all spaces in my Confluence account
Search for pages about "MCP"

# Zendesk
Show all open tickets
Create a ticket about login issue with high priority
Attach a summary report to ticket #3
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
| `add_comment_to_ticket` | Add public comment or internal note |
| `search_tickets` | Search tickets by keyword or filter |
| `get_ticket_comments` | Get all comments on a ticket |
| `get_users` | List users by role (agent, admin, end-user) |
| `upload_text_as_attachment` | Upload text content as a file (get token) |
| `upload_attachment` | Upload a local file by path (get token) |
| `attach_file_to_ticket` | Attach an uploaded file to a ticket using token |
| `upload_and_attach_text` | Upload text + attach to ticket in one step ⭐ |
| `create_ticket_with_text_attachment` | Create ticket + attach file in one step ⭐ |

> ⭐ **Recommended**: Use `upload_and_attach_text` to attach any AI-generated content  
> (reports, summaries, analysis) directly to a ticket without needing a local file path.

---

## Monitoring Logs

```bash
# Watch server logs in real-time
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
| Confluence 404 error | Check CONFLUENCE_URL has no trailing slash |
| Zendesk 401 error | Ensure email format is `email/token:TOKEN` |
| New tools not appearing | Clear `__pycache__` and restart Claude Desktop |

---

## Project Structure

```
MCP/
├── .env                  # Credentials (never commit!)
├── .env.example          # Credentials template
├── .gitignore
├── README.md
├── requirements.txt
├── servers/              # MCP server implementations
│   ├── weather.py
│   ├── jira.py
│   ├── confluence.py
│   └── zendesk.py
├── config/               # Configuration management
│   └── settings.py
├── utils/                # Shared utilities
├── tests/                # Test files
├── scripts/              # Helper scripts
└── learning/             # Learning notes
```