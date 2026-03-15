from typing import Any
import httpx
import logging
import base64
import mimetypes
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
logging.basicConfig(level=getattr(logging, config.zendesk.log_level))

mcp = FastMCP("zendesk")

# Zendesk configuration from config
ZENDESK_URL = config.zendesk.url
ZENDESK_EMAIL = config.zendesk.email
ZENDESK_API_TOKEN = config.zendesk.api_token


def get_auth_header() -> dict[str, str]:
    """Generate Basic Auth header for Zendesk API."""
    if not all([ZENDESK_URL, ZENDESK_EMAIL, ZENDESK_API_TOKEN]):
        raise ValueError("Missing Zendesk credentials in environment variables")

    # Zendesk uses email/token format: email@domain.com/token:api_token
    credentials = f"{ZENDESK_EMAIL}/token:{ZENDESK_API_TOKEN}"
    encoded = base64.b64encode(credentials.encode()).decode()

    return {
        "Authorization": f"Basic {encoded}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


async def make_zendesk_request(
    endpoint: str,
    method: str = "GET",
    json_data: dict = None,
    params: dict = None
) -> dict[str, Any] | None:
    """Make a request to the Zendesk API with proper error handling."""
    url = f"{ZENDESK_URL}/api/v2/{endpoint}"

    try:
        headers = get_auth_header()
    except ValueError as e:
        logging.error(f"Authentication error: {e}")
        return None

    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params, timeout=config.zendesk.timeout)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=json_data, timeout=config.zendesk.timeout)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=json_data, timeout=config.zendesk.timeout)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers, timeout=config.zendesk.timeout)
            else:
                logging.error(f"Unsupported HTTP method: {method}")
                return None

            response.raise_for_status()

            # DELETE requests return 204 No Content
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
            logging.error(f"Zendesk request failed: {e}")
            return None


@mcp.tool()
async def get_tickets(status: str = "open", max_results: int = 10) -> str:
    """Get Zendesk tickets filtered by status.

    Args:
        status: Ticket status (open, pending, solved, closed, new, all)
        max_results: Maximum number of tickets to return (default: 10)
    """
    logging.info(f"MCP TOOL CALLED -> get_tickets({status})")

    # Validate status
    valid_statuses = ["open", "pending", "solved", "closed", "new", "all"]
    status = status.lower().strip()
    if status not in valid_statuses:
        return f"Error: Invalid status. Must be one of: {', '.join(valid_statuses)}"

    # Build params
    if status == "all":
        params = {"per_page": min(max_results, 100)}
        endpoint = "tickets"
    else:
        params = {
            "query": f"type:ticket status:{status}",
            "per_page": min(max_results, 100)
        }
        endpoint = "search"

    data = await make_zendesk_request(endpoint, params=params)

    if not data:
        return f"Unable to fetch {status} tickets."

    # Handle both tickets and search results
    tickets = data.get("tickets", data.get("results", []))
    total = data.get("count", len(tickets))

    if not tickets:
        return f"No {status} tickets found."

    results = []
    for ticket in tickets[:max_results]:
        ticket_id = ticket.get("id", "N/A")
        subject = ticket.get("subject", "N/A")
        ticket_status = ticket.get("status", "N/A")
        priority = ticket.get("priority", "normal") or "normal"
        requester_id = ticket.get("requester_id", "N/A")
        created_at = ticket.get("created_at", "N/A")

        results.append(
            f"• [#{ticket_id}] {subject}\n"
            f"  Status: {ticket_status} | Priority: {priority}\n"
            f"  Created: {created_at}\n"
            f"  URL: {ZENDESK_URL}/agent/tickets/{ticket_id}"
        )

    header = f"Found {total} {status} ticket(s) (showing {len(tickets[:max_results])}):\n"
    return header + "\n\n".join(results)


@mcp.tool()
async def get_ticket(ticket_id: int | str) -> str:
    """Get details of a specific Zendesk ticket.

    Args:
        ticket_id: The ticket ID number (e.g., 123)
    """
    ticket_id = str(ticket_id)
    logging.info(f"MCP TOOL CALLED -> get_ticket({ticket_id})")

    if not ticket_id:
        return "Error: Ticket ID is required"

    data = await make_zendesk_request(f"tickets/{ticket_id}")

    if not data:
        return f"Unable to fetch ticket #{ticket_id}. Check if the ticket ID is correct."

    ticket = data.get("ticket", {})

    ticket_id = ticket.get("id", "N/A")
    subject = ticket.get("subject", "N/A")
    status = ticket.get("status", "N/A")
    priority = ticket.get("priority", "normal") or "normal"
    description = ticket.get("description", "No description")
    created_at = ticket.get("created_at", "N/A")
    updated_at = ticket.get("updated_at", "N/A")
    ticket_type = ticket.get("type", "N/A")
    tags = ", ".join(ticket.get("tags", [])) or "None"

    result = f"""
Ticket: #{ticket_id}
Subject: {subject}
Status: {status}
Priority: {priority}
Type: {ticket_type}
Tags: {tags}
Created: {created_at}
Updated: {updated_at}

Description:
{description[:1000]}{"..." if len(description) > 1000 else ""}

URL: {ZENDESK_URL}/agent/tickets/{ticket_id}
"""
    return result


@mcp.tool()
async def create_ticket(
    subject: str,
    description: str,
    priority: str = "normal",
    ticket_type: str = "question"
) -> str:
    """Create a new Zendesk ticket.

    Args:
        subject: Ticket subject/title
        description: Detailed description of the issue
        priority: Ticket priority (low, normal, high, urgent)
        ticket_type: Type of ticket (question, incident, problem, task)
    """
    logging.info(f"MCP TOOL CALLED -> create_ticket({subject})")

    # Validate inputs
    if not subject or not description:
        return "Error: Subject and description are required"

    valid_priorities = ["low", "normal", "high", "urgent"]
    valid_types = ["question", "incident", "problem", "task"]

    priority = priority.lower().strip()
    ticket_type = ticket_type.lower().strip()

    if priority not in valid_priorities:
        return f"Error: Invalid priority. Must be one of: {', '.join(valid_priorities)}"
    if ticket_type not in valid_types:
        return f"Error: Invalid type. Must be one of: {', '.join(valid_types)}"

    payload = {
        "ticket": {
            "subject": subject,
            "comment": {
                "body": description
            },
            "priority": priority,
            "type": ticket_type
        }
    }

    data = await make_zendesk_request("tickets", method="POST", json_data=payload)

    if not data:
        return "Failed to create ticket. Check logs for details."

    ticket = data.get("ticket", {})
    ticket_id = ticket.get("id")
    ticket_url = f"{ZENDESK_URL}/agent/tickets/{ticket_id}"

    return f"✅ Ticket created successfully!\nID: #{ticket_id}\nSubject: {subject}\nURL: {ticket_url}"


@mcp.tool()
async def update_ticket(
    ticket_id: str,
    status: str = None,
    priority: str = None,
    comment: str = None
) -> str:
    """Update a Zendesk ticket status, priority or add a comment.

    Args:
        ticket_id: The ticket ID to update
        status: New status (open, pending, solved, closed)
        priority: New priority (low, normal, high, urgent)
        comment: Optional comment to add with the update
    """
    logging.info(f"MCP TOOL CALLED -> update_ticket({ticket_id})")

    if not ticket_id:
        return "Error: Ticket ID is required"

    if not any([status, priority, comment]):
        return "Error: At least one of status, priority, or comment is required"

    # Build update payload
    ticket_update = {}

    if status:
        valid_statuses = ["open", "pending", "solved", "closed"]
        status = status.lower().strip()
        if status not in valid_statuses:
            return f"Error: Invalid status. Must be one of: {', '.join(valid_statuses)}"
        ticket_update["status"] = status

    if priority:
        valid_priorities = ["low", "normal", "high", "urgent"]
        priority = priority.lower().strip()
        if priority not in valid_priorities:
            return f"Error: Invalid priority. Must be one of: {', '.join(valid_priorities)}"
        ticket_update["priority"] = priority

    if comment:
        ticket_update["comment"] = {
            "body": comment,
            "public": True
        }

    payload = {"ticket": ticket_update}

    data = await make_zendesk_request(f"tickets/{ticket_id}", method="PUT", json_data=payload)

    if not data:
        return f"❌ Failed to update ticket #{ticket_id}. Check logs for details."

    updates = []
    if status:
        updates.append(f"Status → {status}")
    if priority:
        updates.append(f"Priority → {priority}")
    if comment:
        updates.append("Comment added")

    return f"✅ Ticket #{ticket_id} updated successfully!\n" + "\n".join(updates)


@mcp.tool()
async def add_comment_to_ticket(
    ticket_id: str,
    comment: str,
    public: bool = True
) -> str:
    """Add a comment to a Zendesk ticket.

    Args:
        ticket_id: The ticket ID
        comment: Comment text to add
        public: Whether comment is public (True) or internal note (False)
    """
    logging.info(f"MCP TOOL CALLED -> add_comment_to_ticket({ticket_id})")

    if not ticket_id or not comment:
        return "Error: Ticket ID and comment text are required"

    payload = {
        "ticket": {
            "comment": {
                "body": comment,
                "public": public
            }
        }
    }

    data = await make_zendesk_request(f"tickets/{ticket_id}", method="PUT", json_data=payload)

    if not data:
        return f"❌ Failed to add comment to ticket #{ticket_id}"

    comment_type = "public comment" if public else "internal note"
    return f"✅ Added {comment_type} to ticket #{ticket_id} successfully!"


@mcp.tool()
async def search_tickets(query: str, max_results: int = 10) -> str:
    """Search for Zendesk tickets using a search query.

    Args:
        query: Search query (e.g., 'login issue', 'status:open priority:urgent')
        max_results: Maximum number of results (default: 10)
    """
    logging.info(f"MCP TOOL CALLED -> search_tickets({query})")

    if not query:
        return "Error: Search query is required"

    params = {
        "query": f"type:ticket {query}",
        "per_page": min(max_results, 100)
    }

    data = await make_zendesk_request("search", params=params)

    if not data:
        return "Search failed. Check your query."

    tickets = data.get("results", [])
    total = data.get("count", 0)

    if not tickets:
        return "No tickets found matching your search criteria."

    results = []
    for ticket in tickets[:max_results]:
        ticket_id = ticket.get("id", "N/A")
        subject = ticket.get("subject", "N/A")
        status = ticket.get("status", "N/A")
        priority = ticket.get("priority", "normal") or "normal"

        results.append(
            f"• [#{ticket_id}] {subject}\n"
            f"  Status: {status} | Priority: {priority}\n"
            f"  URL: {ZENDESK_URL}/agent/tickets/{ticket_id}"
        )

    header = f"Found {total} ticket(s) (showing {len(tickets[:max_results])}):\n"
    return header + "\n\n".join(results)


@mcp.tool()
async def get_ticket_comments(ticket_id: int | str) -> str:
    """Get all comments for a Zendesk ticket.

    Args:
        ticket_id: The ticket ID
    """
    ticket_id = str(ticket_id)
    logging.info(f"MCP TOOL CALLED -> get_ticket_comments({ticket_id})")

    if not ticket_id:
        return "Error: Ticket ID is required"

    data = await make_zendesk_request(f"tickets/{ticket_id}/comments")

    if not data:
        return f"Unable to fetch comments for ticket #{ticket_id}"

    comments = data.get("comments", [])

    if not comments:
        return f"No comments found for ticket #{ticket_id}"

    results = []
    for comment in comments:
        author_id = comment.get("author_id", "N/A")
        body = comment.get("body", "No content")
        created_at = comment.get("created_at", "N/A")
        public = "Public" if comment.get("public") else "Internal Note"

        results.append(
            f"[{public}] - {created_at}\n"
            f"Author ID: {author_id}\n"
            f"{body[:500]}{'...' if len(body) > 500 else ''}"
        )

    return f"Comments for ticket #{ticket_id} ({len(comments)} total):\n\n" + "\n---\n".join(results)


@mcp.tool()
async def get_users(role: str = "end-user", max_results: int = 10) -> str:
    """Get Zendesk users filtered by role.

    Args:
        role: User role (end-user, agent, admin)
        max_results: Maximum number of users to return (default: 10)
    """
    logging.info(f"MCP TOOL CALLED -> get_users({role})")

    valid_roles = ["end-user", "agent", "admin"]
    role = role.lower().strip()

    if role not in valid_roles:
        return f"Error: Invalid role. Must be one of: {', '.join(valid_roles)}"

    params = {
        "role": role,
        "per_page": min(max_results, 100)
    }

    data = await make_zendesk_request("users", params=params)

    if not data:
        return f"Unable to fetch {role} users."

    users = data.get("users", [])

    if not users:
        return f"No {role} users found."

    results = []
    for user in users[:max_results]:
        user_id = user.get("id", "N/A")
        name = user.get("name", "N/A")
        email = user.get("email", "N/A")
        user_role = user.get("role", "N/A")
        active = "Active" if user.get("active") else "Inactive"

        results.append(
            f"• [{user_id}] {name}\n"
            f"  Email: {email} | Role: {user_role} | {active}"
        )

    return f"Found {len(users)} {role} user(s):\n\n" + "\n".join(results)


@mcp.tool()
async def upload_text_as_attachment(
    filename: str,
    content: str
) -> str:
    """Upload text content directly as a file attachment to Zendesk.

    Use this instead of upload_attachment when you want to attach text,
    notes, logs, summaries or any content generated in this conversation.
    No file path needed — just pass the content directly.

    Args:
        filename: Name for the file (e.g., 'summary.txt', 'report.md', 'notes.txt')
        content: The text content to upload as a file

    Returns:
        Upload token to use with attach_file_to_ticket tool
    """
    logging.info(f"MCP TOOL CALLED -> upload_text_as_attachment({filename})")

    if not filename or not content:
        return "Error: Filename and content are required"

    # Detect MIME type from filename
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "text/plain"

    url = f"{ZENDESK_URL}/api/v2/uploads"
    params = {"filename": filename}

    try:
        headers = get_auth_header()
    except ValueError as e:
        return f"Authentication error: {e}"

    headers["Content-Type"] = mime_type

    file_bytes = content.encode("utf-8")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                headers=headers,
                params=params,
                content=file_bytes,
                timeout=config.zendesk.timeout
            )
            response.raise_for_status()
            data = response.json()

            upload = data.get("upload", {})
            token = upload.get("token")
            attachment = upload.get("attachment", {})
            att_name = attachment.get("file_name", filename)
            att_size = attachment.get("size", len(file_bytes))

            return (
                f"✅ Content uploaded successfully as '{att_name}'!\n"
                f"Size: {att_size / 1024:.1f} KB\n"
                f"Upload Token: {token}\n\n"
                f"Use this token with attach_file_to_ticket tool to attach it to a ticket."
            )

        except httpx.HTTPStatusError as e:
            logging.error(f"Upload failed {e.response.status_code}: {e.response.text}")
            return f"❌ Upload failed: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            logging.error(f"Upload error: {e}")
            return f"❌ Upload error: {e}"


@mcp.tool()
async def upload_attachment(file_path: str) -> str:
    """Upload a local file to Zendesk by its absolute path on this machine.

    NOTE: This requires a file path on the LOCAL machine running this MCP server.
    If you want to attach content generated in this conversation, use
    upload_text_as_attachment instead — it accepts content directly as text.

    Args:
        file_path: Absolute path to the file on the local machine (e.g., /Users/you/docs/report.pdf)

    Returns:
        Upload token to use with attach_file_to_ticket tool
    """
    logging.info(f"MCP TOOL CALLED -> upload_attachment({file_path})")

    if not file_path:
        return "Error: File path is required"

    # Check file exists
    if not os.path.exists(file_path):
        return f"Error: File not found at path: {file_path}"

    # Check file size (Zendesk limit is 50MB)
    file_size = os.path.getsize(file_path)
    if file_size > 50 * 1024 * 1024:
        return "Error: File exceeds Zendesk's 50MB attachment limit"

    file_name = os.path.basename(file_path)

    # Detect MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    url = f"{ZENDESK_URL}/api/v2/uploads"
    params = {"filename": file_name}

    try:
        headers = get_auth_header()
    except ValueError as e:
        return f"Authentication error: {e}"

    # Upload requires Content-Type of the actual file, not application/json
    headers["Content-Type"] = mime_type

    async with httpx.AsyncClient() as client:
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()

            response = await client.post(
                url,
                headers=headers,
                params=params,
                content=file_content,
                timeout=config.zendesk.timeout
            )
            response.raise_for_status()
            data = response.json()

            upload = data.get("upload", {})
            token = upload.get("token")
            attachment = upload.get("attachment", {})
            att_name = attachment.get("file_name", file_name)
            att_size = attachment.get("size", file_size)
            att_type = attachment.get("content_type", mime_type)

            return (
                f"✅ File uploaded successfully!\n"
                f"File: {att_name}\n"
                f"Size: {att_size / 1024:.1f} KB\n"
                f"Type: {att_type}\n"
                f"Upload Token: {token}\n\n"
                f"Use this token with attach_file_to_ticket tool to attach it to a ticket."
            )

        except httpx.HTTPStatusError as e:
            logging.error(f"Upload failed {e.response.status_code}: {e.response.text}")
            return f"❌ Upload failed: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            logging.error(f"Upload error: {e}")
            return f"❌ Upload error: {e}"


@mcp.tool()
async def attach_file_to_ticket(
    ticket_id: str,
    upload_token: str,
    comment: str = "Attaching file to ticket."
) -> str:
    """Attach an uploaded file to a Zendesk ticket using an upload token.

    First use upload_attachment to get the token, then call this tool.

    Args:
        ticket_id: The ticket ID to attach the file to
        upload_token: The upload token returned by upload_attachment tool
        comment: Comment text to include with the attachment (default: 'Attaching file to ticket.')
    """
    logging.info(f"MCP TOOL CALLED -> attach_file_to_ticket({ticket_id})")

    if not ticket_id or not upload_token:
        return "Error: Ticket ID and upload token are required"

    payload = {
        "ticket": {
            "comment": {
                "body": comment,
                "uploads": [upload_token],
                "public": True
            }
        }
    }

    data = await make_zendesk_request(
        f"tickets/{ticket_id}",
        method="PUT",
        json_data=payload
    )

    if not data:
        return f"❌ Failed to attach file to ticket #{ticket_id}"

    ticket_url = f"{ZENDESK_URL}/agent/tickets/{ticket_id}"
    return (
        f"✅ File attached to ticket #{ticket_id} successfully!\n"
        f"Comment: {comment}\n"
        f"URL: {ticket_url}"
    )


@mcp.tool()
async def upload_and_attach_text(
    ticket_id: str,
    filename: str,
    content: str,
    comment: str = "Please find the attached file."
) -> str:
    """Upload text content as a file AND attach it to a ticket in one step.

    This is the recommended tool when you want to attach any text, report,
    summary, analysis, or notes to an existing Zendesk ticket.
    No file path needed — content is passed directly as text.

    Args:
        ticket_id: The ticket ID to attach the file to
        filename: Name for the file (e.g., 'analysis.txt', 'report.md', 'summary.txt')
        content: The text content to upload and attach
        comment: Comment to add alongside the attachment
    """
    logging.info(f"MCP TOOL CALLED -> upload_and_attach_text({ticket_id}, {filename})")

    if not ticket_id or not filename or not content:
        return "Error: ticket_id, filename, and content are all required"

    # Step 1: Upload the content
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "text/plain"

    url = f"{ZENDESK_URL}/api/v2/uploads"
    params = {"filename": filename}

    try:
        headers = get_auth_header()
    except ValueError as e:
        return f"Authentication error: {e}"

    headers["Content-Type"] = mime_type
    file_bytes = content.encode("utf-8")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                headers=headers,
                params=params,
                content=file_bytes,
                timeout=config.zendesk.timeout
            )
            response.raise_for_status()
            upload_data = response.json()
        except httpx.HTTPStatusError as e:
            return f"❌ Upload failed: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Upload error: {e}"

    token = upload_data.get("upload", {}).get("token")
    if not token:
        return "❌ Upload succeeded but no token returned"

    # Step 2: Attach to ticket
    payload = {
        "ticket": {
            "comment": {
                "body": comment,
                "uploads": [token],
                "public": True
            }
        }
    }

    data = await make_zendesk_request(
        f"tickets/{ticket_id}",
        method="PUT",
        json_data=payload
    )

    if not data:
        return f"❌ File uploaded (token: {token}) but failed to attach to ticket #{ticket_id}"

    ticket_url = f"{ZENDESK_URL}/agent/tickets/{ticket_id}"
    att_size = len(file_bytes) / 1024

    return (
        f"✅ File uploaded and attached to ticket #{ticket_id}!\n"
        f"File: {filename} ({att_size:.1f} KB)\n"
        f"Comment: {comment}\n"
        f"URL: {ticket_url}"
    )


@mcp.tool()
async def create_ticket_with_text_attachment(
    subject: str,
    description: str,
    filename: str,
    file_content: str,
    priority: str = "normal",
    ticket_type: str = "question"
) -> str:
    """Create a new Zendesk ticket with a text file attached in one step.

    Use this when you want to create a ticket AND immediately attach a
    document, report, analysis, or notes — all in a single operation.

    Args:
        subject: Ticket subject/title
        description: Ticket description shown in the first comment
        filename: Name for the attached file (e.g., 'report.txt', 'analysis.md')
        file_content: Text content to attach as a file
        priority: Ticket priority (low, normal, high, urgent)
        ticket_type: Type of ticket (question, incident, problem, task)
    """
    logging.info(f"MCP TOOL CALLED -> create_ticket_with_text_attachment({subject})")

    if not all([subject, description, filename, file_content]):
        return "Error: subject, description, filename, and file_content are all required"

    valid_priorities = ["low", "normal", "high", "urgent"]
    valid_types = ["question", "incident", "problem", "task"]

    priority = priority.lower().strip()
    ticket_type = ticket_type.lower().strip()

    if priority not in valid_priorities:
        return f"Error: Invalid priority. Must be one of: {', '.join(valid_priorities)}"
    if ticket_type not in valid_types:
        return f"Error: Invalid type. Must be one of: {', '.join(valid_types)}"

    # Step 1: Upload the file content
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "text/plain"

    url = f"{ZENDESK_URL}/api/v2/uploads"
    params = {"filename": filename}

    try:
        headers = get_auth_header()
    except ValueError as e:
        return f"Authentication error: {e}"

    headers["Content-Type"] = mime_type
    file_bytes = file_content.encode("utf-8")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                headers=headers,
                params=params,
                content=file_bytes,
                timeout=config.zendesk.timeout
            )
            response.raise_for_status()
            upload_data = response.json()
        except httpx.HTTPStatusError as e:
            return f"❌ File upload failed: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ File upload error: {e}"

    token = upload_data.get("upload", {}).get("token")
    if not token:
        return "❌ File upload succeeded but no token returned"

    # Step 2: Create the ticket with the attachment
    payload = {
        "ticket": {
            "subject": subject,
            "comment": {
                "body": description,
                "uploads": [token],
                "public": True
            },
            "priority": priority,
            "type": ticket_type
        }
    }

    data = await make_zendesk_request("tickets", method="POST", json_data=payload)

    if not data:
        return f"❌ File uploaded (token: {token}) but ticket creation failed"

    ticket = data.get("ticket", {})
    ticket_id = ticket.get("id")
    ticket_url = f"{ZENDESK_URL}/agent/tickets/{ticket_id}"
    att_size = len(file_bytes) / 1024

    return (
        f"✅ Ticket created with attachment!\n"
        f"Ticket ID: #{ticket_id}\n"
        f"Subject: {subject}\n"
        f"Attached: {filename} ({att_size:.1f} KB)\n"
        f"URL: {ticket_url}"
    )


def main():
    """Start MCP server."""
    logging.info("Starting Zendesk MCP Server...")

    # Check if credentials are set
    if not all([ZENDESK_URL, ZENDESK_EMAIL, ZENDESK_API_TOKEN]):
        logging.error(
            "Missing Zendesk credentials! "
            "Set ZENDESK_URL, ZENDESK_EMAIL, and ZENDESK_API_TOKEN."
        )
        return

    logging.info(f"Zendesk URL: {ZENDESK_URL}")
    logging.info(f"Zendesk Email: {ZENDESK_EMAIL}")

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()