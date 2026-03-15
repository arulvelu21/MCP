import sys
import os
import asyncio
import threading
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
from config.settings import config

load_dotenv()


def _run_in_new_loop(coro):
    """
    Run an async coroutine in a brand-new event loop on a background thread.
    This avoids all conflicts with Streamlit's existing event loop.
    """
    result = None
    error  = None

    def runner():
        nonlocal result, error
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(coro)
        except Exception as e:
            error = e
        finally:
            loop.close()

    t = threading.Thread(target=runner)
    t.start()
    t.join()

    if error:
        raise error
    return result

# ── MCP SSE Server URLs ───────────────────────────────────────────────────────
MCP_SERVERS = {
    "weather": {
        "url": "http://localhost:8001/sse",
        "transport": "sse",
    },
    "jira": {
        "url": "http://localhost:8002/sse",
        "transport": "sse",
    },
    "confluence": {
        "url": "http://localhost:8003/sse",
        "transport": "sse",
    },
    "zendesk": {
        "url": "http://localhost:8004/sse",
        "transport": "sse",
    },
}


def get_azure_llm() -> AzureChatOpenAI:
    """Build AzureChatOpenAI client from config/settings.py."""
    cfg = config.azure_openai

    if not cfg.api_key:
        raise ValueError("AZURE_OPENAI_API_KEY is not set in .env")
    if not cfg.endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT is not set in .env")
    if not cfg.deployment_name:
        raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME is not set in .env")

    return AzureChatOpenAI(
        azure_endpoint=cfg.endpoint,
        azure_deployment=cfg.deployment_name,
        api_key=cfg.api_key,
        api_version=cfg.api_version,
        temperature=0,
        streaming=True,
    )


def get_agent():
    """
    Synchronously connect to all MCP SSE servers and return (agent, tools).
    Runs in a dedicated background thread with its own event loop to avoid
    conflicts with Streamlit's event loop.
    """
    async def _connect():
        client = MultiServerMCPClient(MCP_SERVERS)
        tools  = await client.get_tools()
        llm    = get_azure_llm()
        agent  = create_react_agent(llm, tools)
        return agent, tools

    return _run_in_new_loop(_connect())


def run_agent(agent, chat_history: list[dict], user_input: str) -> str:
    """
    Synchronously run the agent with chat history and return the response string.

    Args:
        agent:        The LangGraph react agent.
        chat_history: List of {"role": "user"|"assistant", "content": "..."} dicts.
        user_input:   The latest user message.

    Returns:
        The agent's response as a plain string.
    """
    messages = []
    for msg in chat_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_input))

    async def _invoke():
        response = await agent.ainvoke({"messages": messages})
        return response["messages"][-1].content

    return _run_in_new_loop(_invoke())
