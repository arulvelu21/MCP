# MCP (Model Context Protocol) Learning Journey
**Date:** March 14, 2026  
**Author:** Arul Velu

---

## 1. What is MCP?

MCP (Model Context Protocol) is an open protocol developed by Anthropic that allows AI models (like Claude) to connect with external tools and services.

```
AI Model (Claude)
      │
      │ MCP Protocol
      ▼
MCP Server (Your Tools)
      │
      │ API Calls
      ▼
External Services (Jira, Weather, GitHub, etc.)
```

---

## 2. Project Structure

We built a **production-ready** MCP project structure:

```
MCP/
├── .env                    # Actual credentials (never commit!)
├── .env.example            # Template for credentials
├── .gitignore              # Git ignore file
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── servers/                # MCP server implementations
│   ├── __init__.py
│   ├── weather.py          # Weather MCP server
│   └── jira.py             # Jira MCP server
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py         # Centralized settings
├── utils/                  # Shared utilities
│   └── __init__.py
├── tests/                  # Test files
│   └── __init__.py
├── clients/                # LangChain/LangGraph clients
│   ├── langchain_client.py
│   └── langgraph_client.py
├── scripts/                # Helper scripts
└── learning/               # Learning notes (this folder!)
    └── 2026-03-14-mcp-learning.md
```

---

## 3. Key Components Learned

### 3.1 FastMCP Framework
```python
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("server-name")

# Define a tool
@mcp.tool()
async def my_tool(param: str) -> str:
    """Tool description - Claude reads this!"""
    return "result"

# Start server
mcp.run(transport="stdio")
```

### 3.2 MCP Transport Types

| Transport | Use Case | Port |
|-----------|----------|------|
| `stdio` | Local (Claude Desktop, same machine) | No port |
| `sse` | Remote (Cloud, Docker, different machine) | Yes (e.g., 8000) |

### 3.3 Configuration Management
```python
# config/settings.py
@dataclass
class JiraConfig:
    url: str = os.getenv("JIRA_URL")
    email: str = os.getenv("JIRA_EMAIL")
    api_token: str = os.getenv("JIRA_API_TOKEN")
    timeout: float = 30.0
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
```

---

## 4. Weather MCP Server

### Tools Built:
| Tool | Description |
|------|-------------|
| `get_alerts` | Get weather alerts for a US state |
| `get_forecast` | Get weather forecast by latitude/longitude |

### Key Learnings:
- Use `NWS (National Weather Service) API` - free, no API key needed
- Always validate input (state code must be 2 letters)
- Use `async/await` for HTTP calls with `httpx`

---

## 5. Jira MCP Server

### Tools Built:
| Tool | Description |
|------|-------------|
| `create_issue` | Create a new Jira issue |
| `get_issue` | Get details of an issue |
| `search_issues` | Search using JQL |
| `update_issue` | Update issue fields |
| `add_comment` | Add comment to issue |
| `transition_issue` | Move issue through workflow |
| `get_projects` | List all Jira projects |
| `get_issue_types` | Get issue types for a project |
| `get_project_issues` | Get all issues for a project |

### Jira API Authentication:
```python
# Basic Auth with Base64 encoding
credentials = f"{email}:{api_token}"
encoded = base64.b64encode(credentials.encode()).decode()
headers = {"Authorization": f"Basic {encoded}"}
```

### Important API Fix:
```python
# ❌ Old deprecated endpoint (returns 410 Gone)
GET /rest/api/3/search?jql=...

# ✅ New correct endpoint
POST /rest/api/3/search/jql
{
    "jql": "project = TC",
    "maxResults": 10,
    "fields": ["summary", "status", "assignee"]
}
```

### Jira Credentials Setup:
1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Create API token
3. Add to `.env` file:
```
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-token-here
```

---

## 6. Production Best Practices

### 6.1 Separate Servers (Industry Standard)
```
✅ One server per integration (Jira, Weather, GitHub)
✅ Each server runs as independent process
✅ If one fails, others keep working
✅ Teams can own and deploy independently
✅ Scale each server based on its own load
```

### 6.2 Error Handling Pattern
```python
async def make_request(url: str):
    try:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error {e.response.status_code}")
        return None
    except httpx.TimeoutException:
        logging.error("Request timeout")
        return None
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return None
```

### 6.3 Input Validation
```python
# Always validate before making API calls
state = state.upper().strip()
if len(state) != 2 or not state.isalpha():
    return "Error: State must be a 2-letter code"
```

### 6.4 Logging
```python
# Log every tool call for debugging
logging.info(f"MCP TOOL CALLED -> create_issue({project_key})")
```

---

## 7. MCP Clients

| Client | Type | Config Location |
|--------|------|----------------|
| **Claude Desktop** | Desktop App | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **VS Code Copilot** | IDE Extension | `.vscode/mcp.json` |
| **Cursor** | IDE | `~/.cursor/mcp.json` |
| **Windsurf** | IDE | `~/.codeium/windsurf/mcp_config.json` |
| **LangChain** | Python Library | Code configuration |
| **LangGraph** | Python Library | Code configuration |

### Claude Desktop Configuration:
```json
{
  "mcpServers": {
    "jira": {
      "command": "python3",
      "args": ["-m", "servers.jira"],
      "cwd": "/path/to/MCP"
    },
    "weather": {
      "command": "python3",
      "args": ["-m", "servers.weather"],
      "cwd": "/path/to/MCP"
    }
  }
}
```

---

## 8. LangChain & LangGraph Integration

### How it works:
```
LangChain/LangGraph
      │
      │ spawns subprocess (same machine for stdio)
      ▼
Your MCP Servers (jira.py, weather.py)
      │
      │ API calls
      ▼
External APIs (Jira Cloud, Weather API)
```

### Key Points:
- `stdio` transport → LangChain and MCP servers **must be on same machine**
- `sse` transport → LangChain can connect to **remote MCP servers**
- LangChain loads MCP tools using `load_mcp_tools(session)`
- LangGraph can connect to **multiple MCP servers simultaneously**

---

## 9. Monitoring & Debugging

### Log Files Location (Claude Desktop on Mac):
```bash
# View logs in real-time
tail -f ~/Library/Logs/Claude/mcp-server-jira.log
tail -f ~/Library/Logs/Claude/mcp-server-weather.log
tail -f ~/Library/Logs/Claude/mcp.log
```

### Test Configuration:
```bash
# Test environment variables are loaded
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('JIRA_URL:', os.getenv('JIRA_URL'))
print('Token exists:', bool(os.getenv('JIRA_API_TOKEN')))
"
```

---

## 10. Production Deployment Options

| Pattern | Technology | Best For |
|---------|-----------|---------|
| **Local** | stdio | Development, Claude Desktop |
| **Containerized** | Docker Compose | Team deployment |
| **Serverless** | AWS Lambda | Auto-scaling |
| **Kubernetes** | K8s Deployments | Enterprise |

---

## 11. What's Next?

- [ ] Add more Jira tools (sprints, boards, attachments)
- [ ] Create GitHub MCP server
- [ ] Add retry logic with `tenacity`
- [ ] Write unit tests with `pytest`
- [ ] Create Docker containers
- [ ] Deploy to cloud (AWS/GCP/Azure)
- [ ] Add monitoring/metrics
- [ ] Create LangGraph workflows for automation

---

## 12. Key Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Jira MCP server
python -m servers.jira

# Run Weather MCP server
python -m servers.weather

# Check logs
tail -f ~/Library/Logs/Claude/mcp-server-jira.log
```

---

## Summary

| What | How |
|------|-----|
| **Protocol** | MCP (Model Context Protocol) |
| **Framework** | FastMCP |
| **Language** | Python (async/await) |
| **Transport** | stdio (local), sse (remote) |
| **Auth** | Basic Auth (Base64) for Jira |
| **Config** | Environment variables + dataclasses |
| **Clients** | Claude Desktop, VS Code, LangChain, LangGraph |