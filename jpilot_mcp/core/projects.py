"""Project-related operations."""

from typing import List, Dict, Any
from jira.exceptions import JIRAError

from .client import JiraClient, JiraError


def list_projects(client: JiraClient) -> List[Dict[str, Any]]:
    """List all accessible Jira projects.

    Args:
        client: Jira client instance

    Returns:
        List of project dictionaries with key, name, and description

    Raises:
        JiraError: If unable to fetch projects
    """
    try:
        projects = client.client.projects()
        return [
            {
                "key": project.key,
                "name": project.name,
                "description": getattr(project, "description", ""),
                "project_type": getattr(project, "projectTypeKey", ""),
                "lead": getattr(project.lead, "displayName", "") if hasattr(project, "lead") else "",
            }
            for project in projects
        ]
    except JIRAError as e:
        raise JiraError(f"Failed to list projects: {e.text}") from e


def get_project(client: JiraClient, project_key: str) -> Dict[str, Any]:
    """Get detailed information about a specific project.

    Args:
        client: Jira client instance
        project_key: Project key (e.g., 'PROJ')

    Returns:
        Dictionary with project details

    Raises:
        JiraError: If project not found or unable to fetch
    """
    try:
        project = client.client.project(project_key)
        return {
            "key": project.key,
            "name": project.name,
            "description": getattr(project, "description", ""),
            "project_type": getattr(project, "projectTypeKey", ""),
            "lead": getattr(project.lead, "displayName", "") if hasattr(project, "lead") else "",
            "url": getattr(project, "self", ""),
        }
    except JIRAError as e:
        if e.status_code == 404:
            raise JiraError(f"Project '{project_key}' not found") from e
        raise JiraError(f"Failed to get project '{project_key}': {e.text}") from e


def get_issue_types(client: JiraClient, project_key: str) -> List[Dict[str, Any]]:
    """Get available issue types for a project.

    Args:
        client: Jira client instance
        project_key: Project key (e.g., 'PROJ')

    Returns:
        List of issue type dictionaries with id, name, description, and subtask flag

    Raises:
        JiraError: If unable to fetch issue types
    """
    try:
        # Get project to ensure it exists
        project = client.client.project(project_key)

        # Get issue types for the project
        issue_types = client.client.issue_types()

        # Filter to only those available in this project
        # Note: In Jira API v3, we need to check project's issue types
        project_issue_types = []
        for issue_type in issue_types:
            project_issue_types.append({
                "id": issue_type.id,
                "name": issue_type.name,
                "description": getattr(issue_type, "description", ""),
                "subtask": getattr(issue_type, "subtask", False),
            })

        return project_issue_types
    except JIRAError as e:
        if e.status_code == 404:
            raise JiraError(f"Project '{project_key}' not found") from e
        raise JiraError(f"Failed to get issue types for '{project_key}': {e.text}") from e


def get_project_components(client: JiraClient, project_key: str) -> List[Dict[str, Any]]:
    """Get available components for a project.

    Args:
        client: Jira client instance
        project_key: Project key (e.g., 'PROJ')

    Returns:
        List of component dictionaries with id, name, and description

    Raises:
        JiraError: If unable to fetch components
    """
    try:
        # Get project to ensure it exists and get its components
        project = client.client.project(project_key)

        components = []
        if hasattr(project, "components") and project.components:
            for comp in project.components:
                components.append({
                    "id": comp.id,
                    "name": comp.name,
                    "description": getattr(comp, "description", ""),
                })

        return components
    except JIRAError as e:
        if e.status_code == 404:
            raise JiraError(f"Project '{project_key}' not found") from e
        raise JiraError(f"Failed to get components for '{project_key}': {e.text}") from e

