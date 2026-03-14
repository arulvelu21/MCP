# MCP Servers

Model Context Protocol (MCP) servers for various integrations.

---

## Available Servers

| Server | Description | API |
|--------|-------------|-----|
| **Weather** | National Weather Service integration | Free, no key needed |
| **Jira** | Jira Cloud integration | Requires API token |

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
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token-here
```
> **Get Jira API Token:** https://id.atlassian.com/manage-profile/security/api-tokens

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

---

## Claude Desktop Configuration

### Step 1: Find the Config File
```bash
# Open the folder on Mac
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
    }
  }
}
```

> Replace `/path/to/MCP` with your actual project path.  
> e.g. `/Users/yourname/Desktop/MCP`

### Step 3: Restart Claude Desktop
```
CMD + Q  →  Reopen Claude Desktop
```

### Step 4: Verify Connection
- Open Claude Desktop
- Go to **Connectors** section
- You should see ✅ `jira` and ✅ `weather` connected

### Step 5: Test with These Prompts
```
# Jira
List all projects in my Jira account
Show all issues in project TC
Create a task in project TC with summary "Test MCP"

# Weather
Get weather alerts for CA
Get weather forecast for San Francisco
```

---

## Monitoring Logs

```bash
# Watch Jira server logs
tail -f ~/Library/Logs/Claude/mcp-server-jira.log

# Watch Weather server logs
tail -f ~/Library/Logs/Claude/mcp-server-weather.log
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

---

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
ruff check .
```

### Type Checking
```bash
mypy servers/
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Server not in Claude connectors | Restart Claude Desktop (CMD+Q) |
| Authentication error | Check `JIRA_API_TOKEN` in `.env` |
| Tools not loading | Check `cwd` path in config |
| Import errors | Run `source .venv/bin/activate` |

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
│   └── jira.py
├── config/               # Configuration management
│   └── settings.py
├── utils/                # Shared utilities
├── tests/                # Test files
├── scripts/              # Helper scripts
└── learning/             # Learning notes
```
