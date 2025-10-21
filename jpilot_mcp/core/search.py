"""Search and query operations for Jira issues."""

from typing import List, Optional, Dict, Any
from jira.exceptions import JIRAError

from .client import JiraClient, JiraError


def search_issues(
    client: JiraClient,
    jql: str,
    max_results: int = 100,
    fields: Optional[List[str]] = None,
) -> List[Any]:
    """Search for issues using JQL (Jira Query Language).

    Args:
        client: Jira client instance
        jql: JQL query string
        max_results: Maximum number of results to return (default: 100)
        fields: List of fields to include in results (default: all)

    Returns:
        List of issue objects

    Raises:
        JiraError: If search fails
    """
    try:
        if fields is None:
            fields = "*all"
        
        issues = client.client.search_issues(
            jql_str=jql,
            maxResults=max_results,
            fields=fields,
        )
        return issues
    except JIRAError as e:
        raise JiraError(f"Failed to search issues with JQL '{jql}': {e.text}") from e


def list_issues(
    client: JiraClient,
    project_key: str,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    issue_type: Optional[str] = None,
    max_results: int = 100,
) -> List[Dict[str, Any]]:
    """List issues in a project with optional filters.

    Args:
        client: Jira client instance
        project_key: Project key (e.g., 'PROJ')
        status: Optional status filter (e.g., 'To Do', 'In Progress', 'Done')
        assignee: Optional assignee filter ('me', 'unassigned', or email/username)
        issue_type: Optional issue type filter (e.g., 'Epic', 'Story', 'Task')
        max_results: Maximum number of results to return (default: 100)

    Returns:
        List of issue dictionaries with key details

    Raises:
        JiraError: If unable to list issues
    """
    # Build JQL query
    jql_parts = [f'project = "{project_key}"']
    
    if status:
        jql_parts.append(f'status = "{status}"')
    
    if assignee:
        if assignee.lower() == "me":
            jql_parts.append("assignee = currentUser()")
        elif assignee.lower() == "unassigned":
            jql_parts.append("assignee is EMPTY")
        else:
            jql_parts.append(f'assignee = "{assignee}"')
    
    if issue_type:
        jql_parts.append(f'issuetype = "{issue_type}"')

    # Build JQL with proper ORDER BY syntax
    jql = " AND ".join(jql_parts)
    jql += " ORDER BY issuetype DESC, rank ASC"
    
    try:
        issues = search_issues(client, jql, max_results=max_results)
        
        # Convert to simplified dictionaries
        result = []
        for issue in issues:
            result.append({
                "key": issue.key,
                "summary": issue.fields.summary,
                "status": issue.fields.status.name,
                "issue_type": issue.fields.issuetype.name,
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                "priority": issue.fields.priority.name if hasattr(issue.fields, "priority") and issue.fields.priority else "None",
                "created": issue.fields.created,
                "updated": issue.fields.updated,
                "url": f"{client.config.server}/browse/{issue.key}",
            })
        
        return result
    except JiraError:
        raise
    except Exception as e:
        raise JiraError(f"Failed to list issues: {str(e)}") from e


def get_issue(client: JiraClient, issue_key: str) -> Dict[str, Any]:
    """Get detailed information about a specific issue.

    Args:
        client: Jira client instance
        issue_key: Issue key (e.g., 'PROJ-123')

    Returns:
        Dictionary with detailed issue information

    Raises:
        JiraError: If issue not found or unable to fetch
    """
    try:
        issue = client.client.issue(issue_key)
        
        # Get subtasks if any
        subtasks = []
        if hasattr(issue.fields, "subtasks") and issue.fields.subtasks:
            for subtask in issue.fields.subtasks:
                subtasks.append({
                    "key": subtask.key,
                    "summary": subtask.fields.summary,
                    "status": subtask.fields.status.name,
                })
        
        # Get comments (last 10)
        comments = []
        if hasattr(issue.fields, "comment") and issue.fields.comment.comments:
            for comment in issue.fields.comment.comments[-10:]:
                comments.append({
                    "author": comment.author.displayName,
                    "body": comment.body,
                    "created": comment.created,
                })
        
        # Get parent if exists
        parent = None
        if hasattr(issue.fields, "parent") and issue.fields.parent:
            parent = {
                "key": issue.fields.parent.key,
                "summary": issue.fields.parent.fields.summary,
                "issue_type": issue.fields.parent.fields.issuetype.name,
            }
        
        return {
            "key": issue.key,
            "summary": issue.fields.summary,
            "description": issue.fields.description or "",
            "status": issue.fields.status.name,
            "issue_type": issue.fields.issuetype.name,
            "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
            "reporter": issue.fields.reporter.displayName if issue.fields.reporter else "Unknown",
            "priority": issue.fields.priority.name if hasattr(issue.fields, "priority") and issue.fields.priority else "None",
            "created": issue.fields.created,
            "updated": issue.fields.updated,
            "url": f"{client.config.server}/browse/{issue.key}",
            "parent": parent,
            "subtasks": subtasks,
            "comments": comments,
        }
    except JIRAError as e:
        if e.status_code == 404:
            raise JiraError(f"Issue '{issue_key}' not found") from e
        raise JiraError(f"Failed to get issue '{issue_key}': {e.text}") from e


def get_transitions(client: JiraClient, issue_key: str) -> List[Dict[str, Any]]:
    """Get available status transitions for an issue.

    Args:
        client: Jira client instance
        issue_key: Issue key (e.g., 'PROJ-123')

    Returns:
        List of available transitions with id and name

    Raises:
        JiraError: If unable to fetch transitions
    """
    try:
        issue = client.client.issue(issue_key)
        transitions = client.client.transitions(issue)
        
        return [
            {
                "id": t["id"],
                "name": t["name"],
                "to_status": t["to"]["name"] if "to" in t else t["name"],
            }
            for t in transitions
        ]
    except JIRAError as e:
        if e.status_code == 404:
            raise JiraError(f"Issue '{issue_key}' not found") from e
        raise JiraError(f"Failed to get transitions for '{issue_key}': {e.text}") from e

