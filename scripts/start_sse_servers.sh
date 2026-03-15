#!/bin/bash
# Start all MCP SSE servers (used by LangChain agent)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment if it exists
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
fi

cd "$PROJECT_DIR"

echo "🚀 Starting MCP SSE Servers..."
echo ""

python -m sse_servers.weather_sse &
PID_WEATHER=$!
echo "✅ Weather    SSE → http://localhost:8001/sse  (PID $PID_WEATHER)"

python -m sse_servers.jira_sse &
PID_JIRA=$!
echo "✅ Jira       SSE → http://localhost:8002/sse  (PID $PID_JIRA)"

python -m sse_servers.confluence_sse &
PID_CONFLUENCE=$!
echo "✅ Confluence SSE → http://localhost:8003/sse  (PID $PID_CONFLUENCE)"

python -m sse_servers.zendesk_sse &
PID_ZENDESK=$!
echo "✅ Zendesk    SSE → http://localhost:8004/sse  (PID $PID_ZENDESK)"

echo ""
echo "All SSE servers running. Press CTRL+C to stop all."
echo ""

# Stop all background processes on exit
trap "echo ''; echo 'Stopping all SSE servers...'; kill $PID_WEATHER $PID_JIRA $PID_CONFLUENCE $PID_ZENDESK 2>/dev/null; exit 0" INT TERM

wait
