"""Issue creation and management operations."""

from typing import Optional, Dict, Any
from jira.exceptions import JIRAError

from .client import JiraClient, JiraError


def _markdown_to_adf(text: str) -> Dict[str, Any]:
    """Convert markdown text to Atlassian Document Format (ADF).

    This is a simple conversion that wraps text in paragraphs.
    For more complex markdown, a proper parser would be needed.

    Args:
        text: Markdown text

    Returns:
        ADF document structure
    """
    # Split by double newlines to create paragraphs
    paragraphs = text.split("\n\n")
    
    content = []
    for para in paragraphs:
        if para.strip():
            # Split by single newlines within paragraph
            lines = para.strip().split("\n")
            para_content = []
            
            for i, line in enumerate(lines):
                if line.strip():
                    para_content.append({
                        "type": "text",
                        "text": line.strip()
                    })
                    # Add hard break between lines (except last)
                    if i < len(lines) - 1:
                        para_content.append({"type": "hardBreak"})
            
            if para_content:
                content.append({
                    "type": "paragraph",
                    "content": para_content
                })
    
    # If no content, add empty paragraph
    if not content:
        content = [{
            "type": "paragraph",
            "content": []
        }]
    
    return {
        "type": "doc",
        "version": 1,
        "content": content
    }


def _find_user_by_identifier(client: JiraClient, identifier: str) -> Optional[str]:
    """Find a user's account ID by display name, email, or account ID.

    Args:
        client: Jira client instance
        identifier: Display name, email, or account ID

    Returns:
        Account ID if found, None otherwise
    """
    try:
        # If it looks like an account ID, return it
        if identifier.startswith("557058:") or identifier.startswith("qm:") or identifier.startswith("712020:"):
            return identifier

        # Special case: "me" or "myself" returns current user
        if identifier.lower() in ["me", "myself"]:
            myself = client.client.myself()
            return myself["accountId"]

        # For GDPR strict mode, use the user picker API which supports query parameter
        # This works better than search_users which uses deprecated username parameter
        try:
            url = f"{client.client._options['server']}/rest/api/3/user/search"
            params = {"query": identifier, "maxResults": 50}
            response = client.client._session.get(url, params=params)
            response.raise_for_status()
            users = response.json()

            if users:
                # Try to find exact match first (by email or display name)
                for user in users:
                    if (user.get("emailAddress", "").lower() == identifier.lower() or
                        user.get("displayName", "").lower() == identifier.lower()):
                        return user["accountId"]

                # If no exact match, return first result
                return users[0]["accountId"]
        except Exception:
            # Fallback to old method if new API fails
            users = client.client.search_users(identifier)
            if users:
                return users[0].accountId

        return None
    except Exception:
        return None


def create_issue(
    client: JiraClient,
    project_key: str,
    summary: str,
    issue_type: str,
    description: Optional[str] = None,
    parent_key: Optional[str] = None,
    assignee: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new Jira issue.

    Args:
        client: Jira client instance
        project_key: Project key (e.g., 'PROJ')
        summary: Issue summary/title
        issue_type: Issue type (e.g., 'Epic', 'Story', 'Task', 'Subtask')
        description: Optional issue description (markdown supported)
        parent_key: Optional parent issue key (for stories under epics or subtasks)
        assignee: Optional assignee (display name, email, or account ID)

    Returns:
        Dictionary with created issue details (key, url)

    Raises:
        JiraError: If issue creation fails
    """
    try:
        # Build issue fields
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        
        # Add description if provided
        if description:
            fields["description"] = _markdown_to_adf(description)
        
        # Add parent if provided
        if parent_key:
            fields["parent"] = {"key": parent_key}
        
        # Add assignee if provided
        if assignee:
            account_id = _find_user_by_identifier(client, assignee)
            if account_id:
                fields["assignee"] = {"accountId": account_id}
            else:
                # If user not found, log but don't fail
                pass
        
        # Create the issue
        new_issue = client.client.create_issue(fields=fields)
        
        return {
            "key": new_issue.key,
            "url": f"{client.config.server}/browse/{new_issue.key}",
            "id": new_issue.id,
        }
    except JIRAError as e:
        raise JiraError(f"Failed to create issue: {e.text}") from e


def create_epic(
    client: JiraClient,
    project_key: str,
    summary: str,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new Epic.

    Args:
        client: Jira client instance
        project_key: Project key (e.g., 'PROJ')
        summary: Epic summary/title
        description: Optional epic description (markdown supported)

    Returns:
        Dictionary with created epic details (key, url)

    Raises:
        JiraError: If epic creation fails
    """
    return create_issue(
        client=client,
        project_key=project_key,
        summary=summary,
        issue_type="Epic",
        description=description,
    )


def create_story(
    client: JiraClient,
    project_key: str,
    summary: str,
    description: Optional[str] = None,
    epic_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new Story.

    Args:
        client: Jira client instance
        project_key: Project key (e.g., 'PROJ')
        summary: Story summary/title
        description: Optional story description (markdown supported)
        epic_key: Optional parent epic key

    Returns:
        Dictionary with created story details (key, url)

    Raises:
        JiraError: If story creation fails
    """
    return create_issue(
        client=client,
        project_key=project_key,
        summary=summary,
        issue_type="Story",
        description=description,
        parent_key=epic_key,
    )


def create_task(
    client: JiraClient,
    project_key: str,
    summary: str,
    description: Optional[str] = None,
    parent_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new Task.

    Args:
        client: Jira client instance
        project_key: Project key (e.g., 'PROJ')
        summary: Task summary/title
        description: Optional task description (markdown supported)
        parent_key: Optional parent issue key (epic or story)

    Returns:
        Dictionary with created task details (key, url)

    Raises:
        JiraError: If task creation fails
    """
    return create_issue(
        client=client,
        project_key=project_key,
        summary=summary,
        issue_type="Task",
        description=description,
        parent_key=parent_key,
    )


def create_subtask(
    client: JiraClient,
    parent_key: str,
    summary: str,
    description: Optional[str] = None,
    assignee: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new Subtask under a parent issue.

    Args:
        client: Jira client instance
        parent_key: Parent issue key (must be Story or Task)
        summary: Subtask summary/title
        description: Optional subtask description (markdown supported)
        assignee: Optional assignee (display name, email, or account ID)

    Returns:
        Dictionary with created subtask details (key, url)

    Raises:
        JiraError: If subtask creation fails
    """
    try:
        # Get parent to determine project
        parent = client.client.issue(parent_key)
        project_key = parent.fields.project.key

        return create_issue(
            client=client,
            project_key=project_key,
            summary=summary,
            issue_type="Subtask",
            description=description,
            parent_key=parent_key,
            assignee=assignee,
        )
    except JIRAError as e:
        if e.status_code == 404:
            raise JiraError(f"Parent issue '{parent_key}' not found") from e
        raise JiraError(f"Failed to create subtask: {e.text}") from e


def add_comment(
    client: JiraClient,
    issue_key: str,
    comment: str,
) -> Dict[str, Any]:
    """Add a comment to an issue.

    Args:
        client: Jira client instance
        issue_key: Issue key (e.g., 'PROJ-123')
        comment: Comment text (markdown supported)

    Returns:
        Dictionary with comment details (id, created)

    Raises:
        JiraError: If adding comment fails
    """
    try:
        # Convert comment to ADF format for API v3
        comment_adf = _markdown_to_adf(comment)

        # Use the low-level API to add comment with ADF
        url = f"{client.client._options['server']}/rest/api/3/issue/{issue_key}/comment"
        data = {"body": comment_adf}
        response = client.client._session.post(url, json=data)
        response.raise_for_status()
        comment_data = response.json()

        return {
            "id": comment_data["id"],
            "created": comment_data["created"],
            "author": comment_data["author"]["displayName"],
        }
    except JIRAError as e:
        if e.status_code == 404:
            raise JiraError(f"Issue '{issue_key}' not found") from e
        raise JiraError(f"Failed to add comment to '{issue_key}': {e.text}") from e
    except Exception as e:
        raise JiraError(f"Failed to add comment to '{issue_key}': {str(e)}") from e


def update_issue(
    client: JiraClient,
    issue_key: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    assignee: Optional[str] = None,
    priority: Optional[str] = None,
    epic_link: Optional[str] = None,
    labels: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Update an existing Jira issue.

    Args:
        client: Jira client instance
        issue_key: Issue key to update (e.g., 'PROJ-123')
        summary: New summary/title (optional)
        description: New description (markdown supported, optional)
        assignee: New assignee (display name, email, or account ID, optional)
        priority: New priority (e.g., 'High', 'Medium', 'Low', optional)
        epic_link: Link this issue to an epic by providing epic key (e.g., 'PROJ-100', optional)
        labels: Set labels (list of strings, optional)

    Returns:
        Dictionary with updated issue details

    Raises:
        JiraError: If update fails
    """
    try:
        # Build update fields
        fields = {}

        if summary is not None:
            fields["summary"] = summary

        if description is not None:
            fields["description"] = _markdown_to_adf(description)

        if assignee is not None:
            if assignee.lower() == "unassigned" or assignee == "":
                fields["assignee"] = None
            else:
                account_id = _find_user_by_identifier(client, assignee)
                if account_id:
                    fields["assignee"] = {"accountId": account_id}

        if priority is not None:
            fields["priority"] = {"name": priority}

        if labels is not None:
            fields["labels"] = labels

        # Handle epic link (parent field)
        if epic_link is not None:
            fields["parent"] = {"key": epic_link}

        # Update the issue
        if fields:
            issue = client.client.issue(issue_key)
            issue.update(fields=fields)

        # Fetch updated issue to return current state
        updated_issue = client.client.issue(issue_key)

        return {
            "key": updated_issue.key,
            "summary": updated_issue.fields.summary,
            "status": updated_issue.fields.status.name,
            "assignee": updated_issue.fields.assignee.displayName if updated_issue.fields.assignee else "Unassigned",
            "priority": updated_issue.fields.priority.name if updated_issue.fields.priority else None,
            "url": f"{client.config.server}/browse/{updated_issue.key}",
        }
    except JIRAError as e:
        if e.status_code == 404:
            raise JiraError(f"Issue '{issue_key}' not found") from e
        raise JiraError(f"Failed to update issue '{issue_key}': {e.text}") from e
    except Exception as e:
        raise JiraError(f"Failed to update issue '{issue_key}': {str(e)}") from e


def transition_issue(
    client: JiraClient,
    issue_key: str,
    transition_name: str,
) -> Dict[str, Any]:
    """Transition an issue to a new status.

    Args:
        client: Jira client instance
        issue_key: Issue key (e.g., 'PROJ-123')
        transition_name: Name of the transition (e.g., 'In Progress', 'Done')

    Returns:
        Dictionary with new status

    Raises:
        JiraError: If transition fails or transition name not found
    """
    try:
        issue = client.client.issue(issue_key)
        transitions = client.client.transitions(issue)

        # Find transition by name (case-insensitive)
        transition_id = None
        for t in transitions:
            if t["name"].lower() == transition_name.lower():
                transition_id = t["id"]
                break

        if transition_id is None:
            available = [t["name"] for t in transitions]
            raise JiraError(
                f"Transition '{transition_name}' not found for issue '{issue_key}'. "
                f"Available transitions: {', '.join(available)}"
            )

        # Perform transition
        client.client.transition_issue(issue_key, transition_id)

        # Fetch updated issue to get new status
        updated_issue = client.client.issue(issue_key)

        return {
            "key": issue_key,
            "status": updated_issue.fields.status.name,
        }
    except JIRAError as e:
        if e.status_code == 404:
            raise JiraError(f"Issue '{issue_key}' not found") from e
        raise JiraError(f"Failed to transition '{issue_key}': {e.text}") from e
    except JiraError:
        raise

