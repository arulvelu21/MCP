# MCP Servers

Model Context Protocol (MCP) servers for various integrations.

---

## Available Servers

| Server | Description | API |
|--------|-------------|-----|
| **Weather** | National Weather Service integration | Free, no key needed |
| **Jira** | Jira Cloud integration | Requires API token |
| **Confluence** | Confluence Cloud integration | Requires API token |

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

# Confluence (usually same credentials as Jira)
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token-here
```
> **Get API Token:** https://id.atlassian.com/manage-profile/security/api-tokens

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
      "env": {
        "PYTHONPATH": "/path/to/MCP"
      }
    },
    "weather": {
      "command": "/path/to/MCP/.venv/bin/python3",
      "args": ["-m", "servers.weather"],
      "cwd": "/path/to/MCP",
      "env": {
        "PYTHONPATH": "/path/to/MCP"
      }
    },
    "confluence": {
      "command": "/path/to/MCP/.venv/bin/python3",
      "args": ["-m", "servers.confluence"],
      "cwd": "/path/to/MCP",
      "env": {
        "PYTHONPATH": "/path/to/MCP"
      }
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
- Open Claude Desktop
- Go to **Connectors** section
- You should see ✅ `jira` ✅ `weather` ✅ `confluence` connected

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
Create a page in space DEV with title "MCP Integration"
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

---

## Monitoring Logs

```bash
# Watch Jira server logs
tail -f ~/Library/Logs/Claude/mcp-server-jira.log

# Watch Weather server logs
tail -f ~/Library/Logs/Claude/mcp-server-weather.log

# Watch Confluence server logs
tail -f ~/Library/Logs/Claude/mcp-server-confluence.log
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Server not in Claude connectors | Restart Claude Desktop (CMD+Q) |
| Authentication error | Check API token in `.env` |
| Tools not loading | Check `cwd` path in config |
| Import errors | Run `source .venv/bin/activate` |
| Confluence 404 error | Check CONFLUENCE_URL format |

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
│   └── confluence.py     ← New!
├── config/               # Configuration management
│   └── settings.py
├── utils/                # Shared utilities
├── tests/                # Test files
├── scripts/              # Helper scripts
└── learning/             # Learning notes
```