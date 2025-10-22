"""MCP server for Jira integration using FastMCP."""

import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import get_jira_config
from .core import (
    JiraClient,
    JiraError,
    create_jira_client,
    list_projects,
    get_issue_types,
    list_issues,
    get_issue,
    get_transitions,
    create_epic,
    create_story,
    create_task,
    create_subtask,
    add_comment,
    update_issue,
    transition_issue,
)

# Create FastMCP server
mcp = FastMCP(
    name="jpilot-mcp",
    instructions="MCP server for Jira integration. Provides tools for managing Jira issues, epics, stories, tasks, and subtasks.",
)

# Global Jira client (initialized on first use)
_jira_client: JiraClient | None = None


def get_client() -> JiraClient:
    """Get or create the Jira client instance."""
    global _jira_client
    if _jira_client is None:
        try:
            config = get_jira_config()
            _jira_client = create_jira_client(config)
        except Exception as e:
            raise JiraError(f"Failed to initialize Jira client: {str(e)}") from e
    return _jira_client


# ============================================================================
# Discovery Tools
# ============================================================================


@mcp.tool()
def list_jira_projects() -> dict[str, Any]:
    """List all accessible Jira projects.

    Returns:
        Dictionary with 'projects' key containing list of all projects
    """
    try:
        client = get_client()
        projects = list_projects(client)
        return {"projects": projects, "count": len(projects)}
    except Exception as e:
        # Return error information for debugging
        import os
        return {
            "error": str(e),
            "type": type(e).__name__,
            "env_check": {
                "JIRA_SERVER": os.getenv("JIRA_SERVER", "NOT SET"),
                "JIRA_EMAIL": os.getenv("JIRA_EMAIL", "NOT SET"),
                "JIRA_API_TOKEN": "SET" if os.getenv("JIRA_API_TOKEN") else "NOT SET"
            }
        }


@mcp.tool()
def get_jira_issue_types(project_key: str | None = None) -> dict[str, Any]:
    """Get available issue types for a Jira project.

    Args:
        project_key: Project key (e.g., 'PROJ'). If not provided, uses JIRA_DEFAULT_PROJECT from config.

    Returns:
        Dictionary with 'issue_types' key containing list of all available issue types
    """
    # Use default project if not specified
    if not project_key:
        from .config import get_jira_config
        config = get_jira_config()
        if not config.default_project:
            raise ValueError(
                "No project_key provided and no JIRA_DEFAULT_PROJECT configured. "
                "Please either specify project_key or set JIRA_DEFAULT_PROJECT environment variable."
            )
        project_key = config.default_project

    client = get_client()
    issue_types = get_issue_types(client, project_key)
    return {"issue_types": issue_types, "count": len(issue_types), "project": project_key}


@mcp.tool()
def list_jira_issues(
    project_key: str | None = None,
    status: str | None = None,
    assignee: str | None = None,
    issue_type: str | None = None,
    max_results: int = 100,
) -> dict[str, Any]:
    """List ALL issues in a Jira project with optional filters.

    Returns ALL matching issues including those with and without assignees.
    Do NOT filter results after calling this tool - return everything it provides.

    Args:
        project_key: Project key (e.g., 'PROJ'). If not provided, uses JIRA_DEFAULT_PROJECT from config.
        status: Optional status filter (e.g., 'To Do', 'In Progress', 'Done'). Leave empty to get all statuses.
        assignee: Optional assignee filter ('me', 'unassigned', or email/username). Leave empty to get all issues regardless of assignee.
        issue_type: Optional issue type filter (e.g., 'Epic', 'Story', 'Task'). Leave empty to get all types.
        max_results: Maximum number of results (default: 100)

    Returns:
        Dictionary with 'issues' key containing the complete list of ALL matching issues
    """
    # Use default project if not specified
    if not project_key:
        from .config import get_jira_config
        config = get_jira_config()
        if not config.default_project:
            raise ValueError(
                "No project_key provided and no JIRA_DEFAULT_PROJECT configured. "
                "Please either specify project_key or set JIRA_DEFAULT_PROJECT environment variable."
            )
        project_key = config.default_project

    client = get_client()
    issues = list_issues(client, project_key, status, assignee, issue_type, max_results)
    return {"issues": issues, "count": len(issues), "project": project_key}


# ============================================================================
# Issue Reading Tools
# ============================================================================


@mcp.tool()
def get_jira_issue(issue_key: str) -> dict[str, Any]:
    """Get detailed information about a specific Jira issue.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')

    Returns:
        Detailed issue information including description, comments, subtasks, and parent
    """
    client = get_client()
    return get_issue(client, issue_key)


@mcp.tool()
def get_jira_transitions(issue_key: str) -> dict[str, Any]:
    """Get available status transitions for a Jira issue.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')

    Returns:
        Dictionary with 'transitions' key containing list of all available transitions
    """
    client = get_client()
    transitions = get_transitions(client, issue_key)
    return {"transitions": transitions, "count": len(transitions), "issue_key": issue_key}


# ============================================================================
# Issue Creation Tools
# ============================================================================


@mcp.tool()
def create_jira_epic(
    summary: str,
    project_key: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Create a new Epic in Jira.

    Args:
        summary: Epic summary/title
        project_key: Project key (e.g., 'PROJ'). If not provided, uses JIRA_DEFAULT_PROJECT from config.
        description: Optional epic description (markdown supported)

    Returns:
        Created epic details with key and URL
    """
    # Use default project if not specified
    if not project_key:
        from .config import get_jira_config
        config = get_jira_config()
        if not config.default_project:
            raise ValueError(
                "No project_key provided and no JIRA_DEFAULT_PROJECT configured. "
                "Please either specify project_key or set JIRA_DEFAULT_PROJECT environment variable."
            )
        project_key = config.default_project

    client = get_client()
    return create_epic(client, project_key, summary, description)


@mcp.tool()
def create_jira_story(
    summary: str,
    project_key: str | None = None,
    description: str | None = None,
    epic_key: str | None = None,
) -> dict[str, Any]:
    """Create a new Story in Jira.

    **IMPORTANT**: When creating stories for an epic, ALWAYS provide the epic_key parameter to link them together.
    This creates the proper parent-child relationship in Jira.

    Args:
        summary: Story summary/title
        project_key: Project key (e.g., 'PROJ'). If not provided, uses JIRA_DEFAULT_PROJECT from config.
        description: Optional story description (markdown supported)
        epic_key: **STRONGLY RECOMMENDED** - Parent epic key to link this story to (e.g., 'CIT-123').
                  Always provide this when creating stories under an epic.

    Returns:
        Created story details with key and URL

    Example:
        create_jira_story(
            summary="Implement user login",
            epic_key="CIT-123",  # Links this story to epic CIT-123
            description="Add authentication flow"
        )
    """
    # Use default project if not specified
    if not project_key:
        from .config import get_jira_config
        config = get_jira_config()
        if not config.default_project:
            raise ValueError(
                "No project_key provided and no JIRA_DEFAULT_PROJECT configured. "
                "Please either specify project_key or set JIRA_DEFAULT_PROJECT environment variable."
            )
        project_key = config.default_project

    client = get_client()
    return create_story(client, project_key, summary, description, epic_key)


@mcp.tool()
def create_jira_task(
    summary: str,
    project_key: str | None = None,
    description: str | None = None,
    parent_key: str | None = None,
) -> dict[str, Any]:
    """Create a new Task in Jira.

    **IMPORTANT**: When creating tasks for an epic or story, ALWAYS provide the parent_key parameter to link them together.
    This creates the proper parent-child relationship in Jira.

    Args:
        summary: Task summary/title
        project_key: Project key (e.g., 'PROJ'). If not provided, uses JIRA_DEFAULT_PROJECT from config.
        description: Optional task description (markdown supported)
        parent_key: **STRONGLY RECOMMENDED** - Parent issue key (epic or story) to link this task to (e.g., 'CIT-123').
                    Always provide this when creating tasks under an epic or story.

    Returns:
        Created task details with key and URL

    Example:
        create_jira_task(
            summary="Setup database",
            parent_key="CIT-123",  # Links this task to epic CIT-123
            description="Configure PostgreSQL with pgvector"
        )
    """
    # Use default project if not specified
    if not project_key:
        from .config import get_jira_config
        config = get_jira_config()
        if not config.default_project:
            raise ValueError(
                "No project_key provided and no JIRA_DEFAULT_PROJECT configured. "
                "Please either specify project_key or set JIRA_DEFAULT_PROJECT environment variable."
            )
        project_key = config.default_project

    client = get_client()
    return create_task(client, project_key, summary, description, parent_key)


@mcp.tool()
def create_jira_subtask(
    parent_key: str,
    summary: str,
    description: str | None = None,
    assignee: str | None = None,
) -> dict[str, Any]:
    """Create a new Subtask under a parent issue in Jira.

    Args:
        parent_key: Parent issue key (must be Story or Task)
        summary: Subtask summary/title
        description: Optional subtask description (markdown supported)
        assignee: Optional assignee (display name, email, or account ID)

    Returns:
        Created subtask details with key and URL
    """
    client = get_client()
    return create_subtask(client, parent_key, summary, description, assignee)


# ============================================================================
# Issue Management Tools
# ============================================================================


@mcp.tool()
def add_jira_comment(issue_key: str, comment: str) -> dict[str, Any]:
    """Add a comment to a Jira issue.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        comment: Comment text (markdown supported)

    Returns:
        Comment details with id, created timestamp, and author
    """
    client = get_client()
    return add_comment(client, issue_key, comment)


@mcp.tool()
def update_jira_issue(
    issue_key: str,
    summary: str | None = None,
    description: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    epic_link: str | None = None,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Update an existing Jira issue.

    Use this tool to modify issue fields like summary, description, assignee, priority, or to link an issue to an epic.

    IMPORTANT: To link a story/task to an epic, use the epic_link parameter with the epic's key (e.g., 'CIT-123').

    Args:
        issue_key: Issue key to update (e.g., 'PROJ-123')
        summary: New summary/title (optional)
        description: New description (markdown supported, optional)
        assignee: New assignee (display name, email, account ID, or 'unassigned', optional)
        priority: New priority (e.g., 'High', 'Medium', 'Low', optional)
        epic_link: Link this issue to an epic by providing the epic key (e.g., 'PROJ-100', optional)
        labels: Set labels as a list of strings (optional)

    Returns:
        Updated issue details including key, summary, status, assignee, priority, and URL

    Examples:
        - Link a story to an epic: update_jira_issue('CIT-124', epic_link='CIT-123')
        - Change assignee: update_jira_issue('CIT-124', assignee='john.doe@example.com')
        - Update multiple fields: update_jira_issue('CIT-124', summary='New title', priority='High', epic_link='CIT-123')
    """
    client = get_client()
    return update_issue(
        client,
        issue_key,
        summary=summary,
        description=description,
        assignee=assignee,
        priority=priority,
        epic_link=epic_link,
        labels=labels,
    )


@mcp.tool()
def transition_jira_issue(issue_key: str, transition_name: str) -> dict[str, Any]:
    """Change the status of a Jira issue.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        transition_name: Transition name (e.g., 'In Progress', 'Done')
                        Use get_jira_transitions to see available transitions

    Returns:
        Updated issue with new status
    """
    client = get_client()
    return transition_issue(client, issue_key, transition_name)


# ============================================================================
# Main Entry Point
# ============================================================================


def main() -> None:
    """Main entry point for the MCP server."""
    try:
        # Run the server with stdio transport
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("\nShutting down jpilot-mcp server...", file=sys.stderr)
    except Exception as e:
        print(f"Error running server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

