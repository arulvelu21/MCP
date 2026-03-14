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
logging.basicConfig(level=getattr(logging, config.jira.log_level))

mcp = FastMCP("jira")

# Jira configuration from config
JIRA_URL = config.jira.url
JIRA_EMAIL = config.jira.email
JIRA_API_TOKEN = config.jira.api_token


def get_auth_header() -> dict[str, str]:
    """Generate Basic Auth header for Jira API."""
    if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
        raise ValueError("Missing Jira credentials in environment variables")
    
    credentials = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    encoded = base64.b64encode(credentials.encode()).decode()
    
    return {
        "Authorization": f"Basic {encoded}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


async def make_jira_request(
    endpoint: str, 
    method: str = "GET", 
    json_data: dict = None
) -> dict[str, Any] | None:
    """Make a request to the Jira API with proper error handling."""
    url = f"{JIRA_URL}/rest/api/3/{endpoint}"
    
    try:
        headers = get_auth_header()
    except ValueError as e:
        logging.error(f"Authentication error: {e}")
        return None
    
    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, timeout=config.jira.timeout)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=json_data, timeout=config.jira.timeout)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=json_data, timeout=config.jira.timeout)
            else:
                logging.error(f"Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            
            # PUT requests often return 204 No Content
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
            logging.error(f"Jira request failed: {e}")
            return None


@mcp.tool()
async def create_issue(
    project_key: str, 
    summary: str, 
    description: str, 
    issue_type: str = "Task"
) -> str:
    """Create a new Jira issue.
    
    Args:
        project_key: The project key (e.g., PROJ, DEV)
        summary: Issue title/summary
        description: Detailed description of the issue
        issue_type: Type of issue (Task, Bug, Story, Epic)
    """
    logging.info(f"MCP TOOL CALLED -> create_issue({project_key}, {summary})")
    
    # Validate input
    project_key = project_key.upper().strip()
    if not project_key or not summary:
        return "Error: Project key and summary are required"
    
    payload = {
        "fields": {
            "project": {
                "key": project_key
            },
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            },
            "issuetype": {
                "name": issue_type
            }
        }
    }
    
    data = await make_jira_request("issue", method="POST", json_data=payload)
    
    if not data:
        return "Failed to create issue. Check logs for details."
    
    issue_key = data.get("key")
    issue_url = f"{JIRA_URL}/browse/{issue_key}"
    
    return f"✅ Issue created successfully!\nKey: {issue_key}\nURL: {issue_url}"


@mcp.tool()
async def get_issue(issue_key: str) -> str:
    """Get details of a Jira issue.
    
    Args:
        issue_key: The issue key (e.g., PROJ-123)
    """
    logging.info(f"MCP TOOL CALLED -> get_issue({issue_key})")
    
    # Validate input
    issue_key = issue_key.upper().strip()
    if not issue_key:
        return "Error: Issue key is required"
    
    data = await make_jira_request(f"issue/{issue_key}")
    
    if not data:
        return f"Unable to fetch issue {issue_key}. Check if the issue key is correct."
    
    fields = data.get("fields", {})
    
    # Extract description text safely
    description = "No description"
    if fields.get("description"):
        try:
            desc_content = fields["description"].get("content", [])
            if desc_content and desc_content[0].get("content"):
                description = desc_content[0]["content"][0].get("text", "No description")
        except (KeyError, IndexError):
            pass
    
    result = f"""
Issue: {issue_key}
Summary: {fields.get("summary", "N/A")}
Status: {fields.get("status", {}).get("name", "N/A")}
Type: {fields.get("issuetype", {}).get("name", "N/A")}
Priority: {fields.get("priority", {}).get("name", "N/A") if fields.get("priority") else "None"}
Assignee: {fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned"}
Reporter: {fields.get("reporter", {}).get("displayName", "N/A") if fields.get("reporter") else "N/A"}
Created: {fields.get("created", "N/A")}
Updated: {fields.get("updated", "N/A")}

Description:
{description}

URL: {JIRA_URL}/browse/{issue_key}
"""
    
    return result


@mcp.tool()
async def search_issues(jql: str, max_results: int = 10) -> str:
    """Search for Jira issues using JQL (Jira Query Language).
    
    Args:
        jql: JQL query string (e.g., "project = PROJ AND status = Open")
        max_results: Maximum number of results to return (default: 10, max: 50)
    """
    logging.info(f"MCP TOOL CALLED -> search_issues({jql})")
    
    # Validate input
    if not jql:
        return "Error: JQL query is required"
    
    max_results = min(max(1, max_results), 50)  # Clamp between 1 and 50
    
    # Using new Jira search/jql API (POST)
    payload = {
        "jql": jql,
        "maxResults": max_results,
        "fieldsByKeys": False,
        "fields": ["summary", "status", "assignee", "issuetype", "priority"]
    }
    data = await make_jira_request("search/jql", method="POST", json_data=payload)
    
    if not data:
        return "Search failed. Check your JQL syntax."
    
    issues = data.get("issues", [])
    total = data.get("total", 0)
    
    if not issues:
        return "No issues found matching your search criteria."
    
    results = []
    for issue in issues:
        key = issue.get("key")
        fields = issue.get("fields", {})
        summary = fields.get("summary", "N/A")
        status = fields.get("status", {}).get("name", "N/A")
        assignee = fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned"
        
        results.append(f"• {key}: {summary}\n  Status: {status} | Assignee: {assignee}")
    
    header = f"Found {total} issue(s) (showing {len(issues)}):\n"
    return header + "\n".join(results)


@mcp.tool()
async def update_issue(issue_key: str, field: str, value: str) -> str:
    """Update a specific field in a Jira issue.
    
    Args:
        issue_key: The issue key (e.g., PROJ-123)
        field: Field to update (summary, description, priority)
        value: New value for the field
    """
    logging.info(f"MCP TOOL CALLED -> update_issue({issue_key}, {field}, {value})")
    
    # Validate input
    issue_key = issue_key.upper().strip()
    field = field.lower().strip()
    
    if not issue_key or not field or not value:
        return "Error: Issue key, field, and value are required"
    
    # Build payload based on field type
    if field == "summary":
        payload = {"fields": {"summary": value}}
    elif field == "description":
        payload = {
            "fields": {
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": value}]
                        }
                    ]
                }
            }
        }
    elif field == "priority":
        payload = {"fields": {"priority": {"name": value}}}
    else:
        return f"Unsupported field: {field}. Supported fields: summary, description, priority"
    
    data = await make_jira_request(f"issue/{issue_key}", method="PUT", json_data=payload)
    
    if data is None:
        return f"❌ Failed to update {issue_key}. Check logs for details."
    
    return f"✅ Successfully updated {field} for {issue_key}"


@mcp.tool()
async def add_comment(issue_key: str, comment: str) -> str:
    """Add a comment to a Jira issue.
    
    Args:
        issue_key: The issue key (e.g., PROJ-123)
        comment: Comment text to add
    """
    logging.info(f"MCP TOOL CALLED -> add_comment({issue_key})")
    
    # Validate input
    issue_key = issue_key.upper().strip()
    if not issue_key or not comment:
        return "Error: Issue key and comment text are required"
    
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": comment}]
                }
            ]
        }
    }
    
    data = await make_jira_request(f"issue/{issue_key}/comment", method="POST", json_data=payload)
    
    if not data:
        return f"❌ Failed to add comment to {issue_key}"
    
    return f"✅ Comment added successfully to {issue_key}"


@mcp.tool()
async def transition_issue(issue_key: str, transition_name: str) -> str:
    """Transition a Jira issue to a different status.
    
    Args:
        issue_key: The issue key (e.g., PROJ-123)
        transition_name: Name of the transition (e.g., "Done", "In Progress", "To Do")
    """
    logging.info(f"MCP TOOL CALLED -> transition_issue({issue_key}, {transition_name})")
    
    # Validate input
    issue_key = issue_key.upper().strip()
    if not issue_key or not transition_name:
        return "Error: Issue key and transition name are required"
    
    # Get available transitions
    transitions_data = await make_jira_request(f"issue/{issue_key}/transitions")
    
    if not transitions_data:
        return f"Unable to fetch transitions for {issue_key}"
    
    # Find matching transition
    transition_id = None
    available_transitions = []
    
    for trans in transitions_data.get("transitions", []):
        available_transitions.append(trans["name"])
        if trans["name"].lower() == transition_name.lower():
            transition_id = trans["id"]
            break
    
    if not transition_id:
        return f"Transition '{transition_name}' not found.\nAvailable transitions: {', '.join(available_transitions)}"
    
    # Execute transition
    payload = {"transition": {"id": transition_id}}
    data = await make_jira_request(f"issue/{issue_key}/transitions", method="POST", json_data=payload)
    
    if data is None:
        return f"❌ Failed to transition {issue_key}"
    
    return f"✅ Successfully transitioned {issue_key} to '{transition_name}'"


@mcp.tool()
async def get_projects() -> str:
    """Get all accessible Jira projects in the account."""
    logging.info("MCP TOOL CALLED -> get_projects()")
    
    data = await make_jira_request("project")
    
    if not data:
        return "Unable to fetch projects. Check your credentials."
    
    if not data:
        return "No projects found in your Jira account."
    
    results = []
    for project in data:
        key = project.get("key", "N/A")
        name = project.get("name", "N/A")
        project_type = project.get("projectTypeKey", "N/A")
        results.append(f"• [{key}] {name} (Type: {project_type})")
    
    return f"Found {len(data)} project(s):\n\n" + "\n".join(results)


@mcp.tool()
async def get_issue_types(project_key: str) -> str:
    """Get all issue types available for a specific project.
    
    Args:
        project_key: The project key (e.g., PROJ, DEV)
    """
    logging.info(f"MCP TOOL CALLED -> get_issue_types({project_key})")
    
    project_key = project_key.upper().strip()
    data = await make_jira_request(f"project/{project_key}")
    
    if not data:
        return f"Unable to fetch issue types for project {project_key}."
    
    issue_types = data.get("issueTypes", [])
    
    if not issue_types:
        return f"No issue types found for project {project_key}."
    
    results = [f"• {it.get('name')} - {it.get('description', 'No description')}" for it in issue_types]
    
    return f"Issue types for {project_key}:\n\n" + "\n".join(results)


@mcp.tool()
async def get_project_issues(project_key: str, status: str = None, max_results: int = 20) -> str:
    """Get all issues for a specific project with optional status filter.
    
    Args:
        project_key: The project key (e.g., PROJ, DEV)
        status: Optional status filter (e.g., "To Do", "In Progress", "Done")
        max_results: Maximum number of results (default: 20, max: 50)
    """
    logging.info(f"MCP TOOL CALLED -> get_project_issues({project_key}, {status})")
    
    project_key = project_key.upper().strip()
    max_results = min(max(1, max_results), 50)
    
    jql = f"project = {project_key}"
    if status:
        jql += f' AND status = "{status}"'
    jql += " ORDER BY created DESC"
    
    # Using new Jira search/jql API (POST)
    payload = {
        "jql": jql,
        "maxResults": max_results,
        "fieldsByKeys": False,
        "fields": ["summary", "status", "assignee", "issuetype", "priority"]
    }
    data = await make_jira_request("search/jql", method="POST", json_data=payload)
    
    if not data:
        return f"Unable to fetch issues for project {project_key}."
    
    issues = data.get("issues", [])
    total = data.get("total", 0)
    
    if not issues:
        return f"No issues found in project {project_key}."
    
    results = []
    for issue in issues:
        key = issue.get("key")
        fields = issue.get("fields", {})
        summary = fields.get("summary", "N/A")
        status_name = fields.get("status", {}).get("name", "N/A")
        assignee = fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned"
        results.append(f"• {key}: {summary}\n  Status: {status_name} | Assignee: {assignee}")
    
    header = f"Project {project_key} - {total} total issue(s) (showing {len(issues)}):\n"
    return header + "\n".join(results)


def main():
    """Start MCP server."""
    logging.info("Starting Jira MCP Server...")
    
    # Check if credentials are set
    if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
        logging.error("Missing Jira credentials! Set JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN environment variables.")
        return
    
    logging.info(f"Jira URL: {JIRA_URL}")
    logging.info(f"Jira Email: {JIRA_EMAIL}")
    
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()