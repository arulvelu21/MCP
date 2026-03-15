import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from agents.mcp_agent import get_agent, run_agent

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MCP Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 MCP Agent — Powered by Azure OpenAI")
st.caption("Connected to Weather · Jira · Confluence · Zendesk via MCP")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Server Status")

    if st.button("🔌 Connect to MCP Servers", use_container_width=True):
        with st.spinner("Connecting to MCP SSE servers..."):
            try:
                agent, tools = get_agent()
                st.session_state.agent     = agent
                st.session_state.tools     = tools
                st.session_state.connected = True
            except Exception as e:
                st.error(f"❌ Connection failed:\n{e}")
                st.session_state.connected = False

    if st.session_state.get("connected"):
        st.success("✅ Connected")
        tools = st.session_state.get("tools", [])
        st.markdown(f"**{len(tools)} tools loaded:**")
        for tool in tools:
            st.markdown(f"  • `{tool.name}`")
    else:
        st.warning("⚠️ Not connected — click above to connect")

    st.divider()

    # Quick prompt buttons
    st.header("💡 Quick Prompts")
    quick_prompts = {
        "🌤️ Weather Alerts":         "Get weather alerts for CA",
        "📋 Jira Projects":           "List all projects in my Jira account",
        "📚 Confluence Spaces":       "List all spaces in Confluence",
        "🎫 Open Zendesk Tickets":    "Show all open Zendesk tickets",
        "📝 Create Jira Ticket":      "Create a new Jira ticket in the first project you find with summary 'Test from MCP Agent' and description 'Created via LangChain agent'",
    }
    for label, prompt in quick_prompts.items():
        if st.button(label, use_container_width=True):
            st.session_state.quick_prompt = prompt

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Chat History ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Helper: run agent and append messages ─────────────────────────────────────
def handle_prompt(prompt: str):
    if not st.session_state.get("connected"):
        st.error("⚠️ Please connect to MCP servers first using the sidebar!")
        return

    # Show user bubble
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Run agent
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                reply = run_agent(
                    st.session_state.agent,
                    st.session_state.messages[:-1],
                    prompt,
                )
            except Exception as e:
                reply = f"❌ Agent error: {e}"
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# ── Handle Quick Prompt ───────────────────────────────────────────────────────
if "quick_prompt" in st.session_state:
    prompt = st.session_state.pop("quick_prompt")
    handle_prompt(prompt)

# ── Chat Input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about Weather, Jira, Confluence, Zendesk..."):
    handle_prompt(prompt)
