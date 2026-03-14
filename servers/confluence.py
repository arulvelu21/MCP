from typing import Any
import httpx
import logging
import base64
from fastmcp import FastMCP
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

# Configure logging
logging.basicConfig(level=getattr(logging, config.confluence.log_level))

mcp = FastMCP("confluence")

# Confluence configuration from config
CONFLUENCE_URL = config.confluence.url
CONFLUENCE_EMAIL = config.confluence.email
CONFLUENCE_API_TOKEN = config.confluence.api_token


def get_auth_header() -> dict[str, str]:
    """Generate Basic Auth header for Confluence API."""
    if not all([CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN]):
        raise ValueError("Missing Confluence credentials in environment variables")

    credentials = f"{CONFLUENCE_EMAIL}:{CONFLUENCE_API_TOKEN}"
    encoded = base64.b64encode(credentials.encode()).decode()

    return {
        "Authorization": f"Basic {encoded}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


async def make_confluence_request(
    endpoint: str,
    method: str = "GET",
    json_data: dict = None,
    params: dict = None
) -> dict[str, Any] | None:
    """Make a request to the Confluence API with proper error handling."""
    url = f"{CONFLUENCE_URL}/wiki/rest/api/{endpoint}"

    try:
        headers = get_auth_header()
    except ValueError as e:
        logging.error(f"Authentication error: {e}")
        return None

    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params, timeout=config.confluence.timeout)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=json_data, timeout=config.confluence.timeout)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=json_data, timeout=config.confluence.timeout)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers, timeout=config.confluence.timeout)
            else:
                logging.error(f"Unsupported HTTP method: {method}")
                return None

            response.raise_for_status()

            # DELETE and some PUT requests return 204 No Content
            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.TimeoutException:
            logging.error(f"Request timeout for {url}")
            return None
        except Exception as e:
            logging.error(f"Confluence request failed: {e}")
            return None


@mcp.tool()
async def get_spaces() -> str:
    """Get all Confluence spaces available in your account."""
    logging.info("MCP TOOL CALLED -> get_spaces()")

    data = await make_confluence_request("space", params={"limit": 50})

    if not data:
        return "Unable to fetch spaces. Check your credentials."

    spaces = data.get("results", [])

    if not spaces:
        return "No spaces found in your Confluence account."

    results = []
    for space in spaces:
        key = space.get("key", "N/A")
        name = space.get("name", "N/A")
        space_type = space.get("type", "N/A")
        results.append(f"• [{key}] {name} (Type: {space_type})")

    return f"Found {len(spaces)} space(s):\n\n" + "\n".join(results)


@mcp.tool()
async def get_page(page_id: str) -> str:
    """Get details and content of a Confluence page.

    Args:
        page_id: The ID of the Confluence page
    """
    logging.info(f"MCP TOOL CALLED -> get_page({page_id})")

    if not page_id:
        return "Error: Page ID is required"

    data = await make_confluence_request(
        f"content/{page_id}",
        params={"expand": "body.storage,version,space,ancestors"}
    )

    if not data:
        return f"Unable to fetch page {page_id}. Check if the page ID is correct."

    title = data.get("title", "N/A")
    space = data.get("space", {}).get("name", "N/A")
    version = data.get("version", {}).get("number", "N/A")
    created_by = data.get("version", {}).get("by", {}).get("displayName", "N/A")
    page_url = f"{CONFLUENCE_URL}/wiki{data.get('_links', {}).get('webui', '')}"

    # Extract text content (strip HTML tags for readability)
    body = data.get("body", {}).get("storage", {}).get("value", "No content")

    result = f"""
Page ID: {page_id}
Title: {title}
Space: {space}
Version: {version}
Last Modified By: {created_by}
URL: {page_url}

Content (HTML):
{body[:1000]}{"..." if len(body) > 1000 else ""}
"""
    return result


@mcp.tool()
async def search_pages(query: str, space_key: str = None, max_results: int = 10) -> str:
    """Search for Confluence pages using CQL (Confluence Query Language).

    Args:
        query: Search query text
        space_key: Optional space key to limit search (e.g., 'DEV', 'HR')
        max_results: Maximum number of results (default: 10)
    """
    logging.info(f"MCP TOOL CALLED -> search_pages({query})")

    if not query:
        return "Error: Search query is required"

    # Build CQL query
    cql = f'type=page AND text~"{query}"'
    if space_key:
        cql += f' AND space="{space_key.upper()}"'

    params = {
        "cql": cql,
        "limit": min(max_results, 50),
        "expand": "space,version"
    }

    data = await make_confluence_request("content/search", params=params)

    if not data:
        return "Search failed. Check your query."

    pages = data.get("results", [])
    total = data.get("totalSize", 0)

    if not pages:
        return "No pages found matching your search criteria."

    results = []
    for page in pages:
        page_id = page.get("id", "N/A")
        title = page.get("title", "N/A")
        space = page.get("space", {}).get("name", "N/A")
        page_url = f"{CONFLUENCE_URL}/wiki{page.get('_links', {}).get('webui', '')}"
        results.append(f"• [{page_id}] {title}\n  Space: {space}\n  URL: {page_url}")

    header = f"Found {total} page(s) (showing {len(pages)}):\n"
    return header + "\n\n".join(results)


@mcp.tool()
async def create_page(
    space_key: str,
    title: str,
    content: str,
    parent_id: str = None
) -> str:
    """Create a new Confluence page.

    Args:
        space_key: The space key where the page will be created (e.g., 'DEV')
        title: Title of the page
        content: Page content in plain text (will be converted to Confluence format)
        parent_id: Optional parent page ID to create as a child page
    """
    logging.info(f"MCP TOOL CALLED -> create_page({space_key}, {title})")

    # Validate input
    if not space_key or not title or not content:
        return "Error: Space key, title, and content are required"

    # Build payload
    payload = {
        "type": "page",
        "title": title,
        "space": {
            "key": space_key.upper()
        },
        "body": {
            "storage": {
                "value": f"<p>{content}</p>",
                "representation": "storage"
            }
        }
    }

    # Add parent page if specified
    if parent_id:
        payload["ancestors"] = [{"id": parent_id}]

    data = await make_confluence_request("content", method="POST", json_data=payload)

    if not data:
        return "Failed to create page. Check logs for details."

    page_id = data.get("id")
    page_url = f"{CONFLUENCE_URL}/wiki{data.get('_links', {}).get('webui', '')}"

    return f"✅ Page created successfully!\nID: {page_id}\nTitle: {title}\nURL: {page_url}"


@mcp.tool()
async def update_page(
    page_id: str,
    title: str,
    content: str
) -> str:
    """Update an existing Confluence page.

    Args:
        page_id: The ID of the page to update
        title: New title for the page
        content: New content for the page
    """
    logging.info(f"MCP TOOL CALLED -> update_page({page_id})")

    if not page_id or not title or not content:
        return "Error: Page ID, title, and content are required"

    # First get current version number (required for update)
    current = await make_confluence_request(f"content/{page_id}", params={"expand": "version"})

    if not current:
        return f"Unable to fetch page {page_id} for update."

    current_version = current.get("version", {}).get("number", 1)
    new_version = current_version + 1

    payload = {
        "type": "page",
        "title": title,
        "version": {
            "number": new_version
        },
        "body": {
            "storage": {
                "value": f"<p>{content}</p>",
                "representation": "storage"
            }
        }
    }

    data = await make_confluence_request(f"content/{page_id}", method="PUT", json_data=payload)

    if not data:
        return f"❌ Failed to update page {page_id}. Check logs for details."

    page_url = f"{CONFLUENCE_URL}/wiki{data.get('_links', {}).get('webui', '')}"

    return f"✅ Page updated successfully!\nID: {page_id}\nVersion: {new_version}\nURL: {page_url}"


@mcp.tool()
async def add_comment_to_page(page_id: str, comment: str) -> str:
    """Add a comment to a Confluence page.

    Args:
        page_id: The ID of the page
        comment: Comment text to add
    """
    logging.info(f"MCP TOOL CALLED -> add_comment_to_page({page_id})")

    if not page_id or not comment:
        return "Error: Page ID and comment text are required"

    payload = {
        "type": "comment",
        "container": {
            "id": page_id,
            "type": "page"
        },
        "body": {
            "storage": {
                "value": f"<p>{comment}</p>",
                "representation": "storage"
            }
        }
    }

    data = await make_confluence_request("content", method="POST", json_data=payload)

    if not data:
        return f"❌ Failed to add comment to page {page_id}"

    return f"✅ Comment added successfully to page {page_id}"


@mcp.tool()
async def get_space_pages(space_key: str, max_results: int = 10) -> str:
    """Get all pages in a Confluence space.

    Args:
        space_key: The space key (e.g., 'DEV', 'HR')
        max_results: Maximum number of pages to return (default: 10)
    """
    logging.info(f"MCP TOOL CALLED -> get_space_pages({space_key})")

    if not space_key:
        return "Error: Space key is required"

    params = {
        "spaceKey": space_key.upper(),
        "type": "page",
        "limit": min(max_results, 50),
        "expand": "version"
    }

    data = await make_confluence_request("content", params=params)

    if not data:
        return f"Unable to fetch pages for space {space_key}"

    pages = data.get("results", [])
    total = data.get("size", 0)

    if not pages:
        return f"No pages found in space {space_key}"

    results = []
    for page in pages:
        page_id = page.get("id", "N/A")
        title = page.get("title", "N/A")
        version = page.get("version", {}).get("number", "N/A")
        page_url = f"{CONFLUENCE_URL}/wiki{page.get('_links', {}).get('webui', '')}"
        results.append(f"• [{page_id}] {title} (v{version})\n  URL: {page_url}")

    header = f"Found {total} page(s) in space [{space_key}]:\n"
    return header + "\n\n".join(results)


def main():
    """Start MCP server."""
    logging.info("Starting Confluence MCP Server...")

    # Check if credentials are set
    if not all([CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN]):
        logging.error("Missing Confluence credentials! Set CONFLUENCE_URL, CONFLUENCE_EMAIL, and CONFLUENCE_API_TOKEN.")
        return

    logging.info(f"Confluence URL: {CONFLUENCE_URL}")
    logging.info(f"Confluence Email: {CONFLUENCE_EMAIL}")

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()