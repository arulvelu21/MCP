# MCP Servers

Model Context Protocol (MCP) servers for various integrations.

## Available Servers

- **Weather**: National Weather Service API integration
- **Jira**: Jira Cloud API integration

## Setup

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Mac/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

## Running Servers

### Weather Server
```bash
python -m servers.weather
```

### Jira Server
```bash
python -m servers.jira
```

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

## Project Structure

```
MCP/
├── servers/          # MCP server implementations
├── utils/           # Shared utilities
├── config/          # Configuration management
├── tests/           # Test files
└── scripts/         # Helper scripts
```
