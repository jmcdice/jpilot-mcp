"""Search and query operations for Jira issues."""

from typing import List, Optional, Dict, Any
from jira.exceptions import JIRAError

from .client import JiraClient, JiraError
from .adf_parser import extract_text_from_jira_field
from .issues import (
    PROGRESS_FIELD_HEALTH_STATUS,
    PROGRESS_FIELD_COMPLETION_PCT,
    PROGRESS_FIELD_PROGRESS_UPDATE,
    PROGRESS_FIELD_RISKS_BLOCKERS,
    PROGRESS_FIELD_DECISION_NEEDED,
    PROGRESS_FIELD_DECISION_DETAIL,
    PROGRESS_FIELD_DECISION_MAKERS,
)


def search_issues(
    client: JiraClient,
    jql: str,
    max_results: Optional[int] = 100,
    fields: Optional[List[str]] = None,
) -> List[Any]:
    """Search for issues using JQL (Jira Query Language).

    Args:
        client: Jira client instance
        jql: JQL query string
        max_results: Maximum number of results to return (default: 100).
                     Set to None to fetch ALL matching results (auto-pagination).
        fields: List of fields to include in results (default: all)

    Returns:
        List of issue objects

    Raises:
        JiraError: If search fails

    Note:
        Jira Cloud limits each API page to 100 results. When max_results is None,
        the jira library will auto-paginate to fetch all matching issues.
    """
    try:
        if fields is None:
            fields = "*all"

        # When max_results is None, pass False to jira library to enable auto-pagination
        # This fetches ALL matching results across multiple API calls
        jira_max_results = False if max_results is None else max_results

        issues = client.client.search_issues(
            jql_str=jql,
            maxResults=jira_max_results,
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
                # Extract comment body using ADF parser
                body = extract_text_from_jira_field(comment.body) if comment.body else ""

                comments.append({
                    "author": comment.author.displayName,
                    "body": body,
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
        
        # Extract description using ADF parser
        description = extract_text_from_jira_field(issue.fields.description) if issue.fields.description else ""

        # Get components
        components = []
        if hasattr(issue.fields, "components") and issue.fields.components:
            components = [comp.name for comp in issue.fields.components]

        # Get labels
        labels = []
        if hasattr(issue.fields, "labels") and issue.fields.labels:
            labels = issue.fields.labels

        # Get due date
        duedate = None
        if hasattr(issue.fields, "duedate") and issue.fields.duedate:
            duedate = issue.fields.duedate

        # Build base result
        result = {
            "key": issue.key,
            "summary": issue.fields.summary,
            "description": description,
            "status": issue.fields.status.name,
            "issue_type": issue.fields.issuetype.name,
            "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
            "reporter": issue.fields.reporter.displayName if issue.fields.reporter else "Unknown",
            "priority": issue.fields.priority.name if hasattr(issue.fields, "priority") and issue.fields.priority else "None",
            "components": components,
            "labels": labels,
            "duedate": duedate,
            "created": issue.fields.created,
            "updated": issue.fields.updated,
            "url": f"{client.config.server}/browse/{issue.key}",
            "parent": parent,
            "subtasks": subtasks,
            "comments": comments,
        }

        # Add progress fields if this is an Epic and any progress fields are set
        if issue.fields.issuetype.name == "Epic":
            progress_fields: Dict[str, Any] = {}

            health = getattr(issue.fields, PROGRESS_FIELD_HEALTH_STATUS, None)
            if health:
                progress_fields["health_status"] = health.value if hasattr(health, "value") else str(health)

            completion = getattr(issue.fields, PROGRESS_FIELD_COMPLETION_PCT, None)
            if completion is not None:
                progress_fields["completion_percentage"] = completion
                progress_fields["completion_percentage_display"] = f"{int(completion * 100)}%"

            progress_update = getattr(issue.fields, PROGRESS_FIELD_PROGRESS_UPDATE, None)
            if progress_update:
                progress_fields["progress_update"] = extract_text_from_jira_field(progress_update)

            risks = getattr(issue.fields, PROGRESS_FIELD_RISKS_BLOCKERS, None)
            if risks:
                progress_fields["risks_blockers"] = extract_text_from_jira_field(risks)

            decision = getattr(issue.fields, PROGRESS_FIELD_DECISION_NEEDED, None)
            if decision:
                progress_fields["decision_needed"] = decision.value if hasattr(decision, "value") else str(decision)

            detail = getattr(issue.fields, PROGRESS_FIELD_DECISION_DETAIL, None)
            if detail:
                progress_fields["decision_detail"] = detail

            makers = getattr(issue.fields, PROGRESS_FIELD_DECISION_MAKERS, None)
            if makers:
                progress_fields["decision_makers"] = [
                    user.displayName if hasattr(user, "displayName") else str(user)
                    for user in makers
                ]

            # Only add progress_fields if any were found
            if progress_fields:
                result["progress_fields"] = progress_fields

        return result
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


def get_epic_progress(client: JiraClient, issue_key: str) -> Dict[str, Any]:
    """Get weekly progress report fields from a Jira epic.

    Retrieves the custom fields used for weekly status reporting:
    - Health Status: Overall health indicator (On Track, At Risk, Behind)
    - Completion Percentage: Progress as a decimal (0.0 to 1.0)
    - Progress Update: Text description of recent progress
    - Risks/Blockers: Text description of risks or blockers
    - Decision Needed: Whether a decision is required (Yes/No)
    - Decision Detail: Details about the decision needed
    - Decision Maker(s): Users who need to make the decision

    Args:
        client: Jira client instance
        issue_key: Issue key (e.g., 'TSSE-123')

    Returns:
        Dictionary with issue info and progress field values

    Raises:
        JiraError: If issue not found or unable to fetch
    """
    try:
        issue = client.client.issue(issue_key)

        result: Dict[str, Any] = {
            "key": issue.key,
            "summary": issue.fields.summary,
            "status": issue.fields.status.name,
            "issue_type": issue.fields.issuetype.name,
            "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
            "url": f"{client.config.server}/browse/{issue.key}",
            "progress_fields": {},
        }

        progress = result["progress_fields"]

        # Health Status (dropdown)
        health = getattr(issue.fields, PROGRESS_FIELD_HEALTH_STATUS, None)
        if health:
            progress["health_status"] = health.value if hasattr(health, "value") else str(health)

        # Completion Percentage (number)
        completion = getattr(issue.fields, PROGRESS_FIELD_COMPLETION_PCT, None)
        if completion is not None:
            progress["completion_percentage"] = completion
            progress["completion_percentage_display"] = f"{int(completion * 100)}%"

        # Progress Update (ADF text area)
        progress_update = getattr(issue.fields, PROGRESS_FIELD_PROGRESS_UPDATE, None)
        if progress_update:
            progress["progress_update"] = extract_text_from_jira_field(progress_update)

        # Risks/Blockers (ADF text area)
        risks = getattr(issue.fields, PROGRESS_FIELD_RISKS_BLOCKERS, None)
        if risks:
            progress["risks_blockers"] = extract_text_from_jira_field(risks)

        # Decision Needed (dropdown)
        decision = getattr(issue.fields, PROGRESS_FIELD_DECISION_NEEDED, None)
        if decision:
            progress["decision_needed"] = decision.value if hasattr(decision, "value") else str(decision)

        # Decision Detail (text field)
        detail = getattr(issue.fields, PROGRESS_FIELD_DECISION_DETAIL, None)
        if detail:
            progress["decision_detail"] = detail

        # Decision Maker(s) (multi-user picker)
        makers = getattr(issue.fields, PROGRESS_FIELD_DECISION_MAKERS, None)
        if makers:
            progress["decision_makers"] = [
                user.displayName if hasattr(user, "displayName") else str(user)
                for user in makers
            ]

        return result

    except JIRAError as e:
        if e.status_code == 404:
            raise JiraError(f"Issue '{issue_key}' not found") from e
        raise JiraError(f"Failed to get progress fields for '{issue_key}': {e.text}") from e
