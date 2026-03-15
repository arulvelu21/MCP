#!/bin/bash
# Start the Streamlit UI
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment if it exists
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
fi

cd "$PROJECT_DIR"

echo "🎨 Starting Streamlit UI..."
echo "   Open → http://localhost:8501"
echo ""

streamlit run ui/app.py
