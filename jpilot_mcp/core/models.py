"""Pydantic models for type-safe Jira data structures."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# Project Models
# ============================================================================


class Project(BaseModel):
    """Jira project information."""

    key: str = Field(..., description="Project key (e.g., 'PROJ')")
    name: str = Field(..., description="Project name")
    description: str = Field(default="", description="Project description")
    project_type: str = Field(default="", description="Project type (e.g., 'software')")
    lead: str = Field(default="", description="Project lead display name")
    url: Optional[str] = Field(default=None, description="Project URL")


class IssueType(BaseModel):
    """Jira issue type information."""

    id: str = Field(..., description="Issue type ID")
    name: str = Field(..., description="Issue type name (e.g., 'Epic', 'Story')")
    description: str = Field(default="", description="Issue type description")
    subtask: bool = Field(default=False, description="Whether this is a subtask type")


# ============================================================================
# Issue Models
# ============================================================================


class IssueReference(BaseModel):
    """Minimal issue reference (for parent/child relationships)."""

    key: str = Field(..., description="Issue key (e.g., 'PROJ-123')")
    summary: str = Field(..., description="Issue summary")
    issue_type: Optional[str] = Field(default=None, description="Issue type")
    status: Optional[str] = Field(default=None, description="Issue status")


class Comment(BaseModel):
    """Issue comment."""

    author: str = Field(..., description="Comment author display name")
    body: str = Field(..., description="Comment text")
    created: str = Field(..., description="Creation timestamp")


class IssueSummary(BaseModel):
    """Summary information about an issue (for list views)."""

    key: str = Field(..., description="Issue key (e.g., 'PROJ-123')")
    summary: str = Field(..., description="Issue summary/title")
    status: str = Field(..., description="Issue status")
    issue_type: str = Field(..., description="Issue type (e.g., 'Epic', 'Story')")
    assignee: str = Field(..., description="Assignee display name or 'Unassigned'")
    priority: str = Field(..., description="Priority level")
    created: str = Field(..., description="Creation timestamp")
    updated: str = Field(..., description="Last update timestamp")
    url: str = Field(..., description="Issue URL")


class IssueDetail(BaseModel):
    """Detailed information about an issue."""

    key: str = Field(..., description="Issue key (e.g., 'PROJ-123')")
    summary: str = Field(..., description="Issue summary/title")
    description: str = Field(default="", description="Issue description")
    status: str = Field(..., description="Issue status")
    issue_type: str = Field(..., description="Issue type (e.g., 'Epic', 'Story')")
    assignee: str = Field(..., description="Assignee display name or 'Unassigned'")
    reporter: str = Field(..., description="Reporter display name")
    priority: str = Field(..., description="Priority level")
    created: str = Field(..., description="Creation timestamp")
    updated: str = Field(..., description="Last update timestamp")
    url: str = Field(..., description="Issue URL")
    parent: Optional[IssueReference] = Field(default=None, description="Parent issue if exists")
    subtasks: List[IssueReference] = Field(default_factory=list, description="List of subtasks")
    comments: List[Comment] = Field(default_factory=list, description="Recent comments")


class Transition(BaseModel):
    """Available status transition for an issue."""

    id: str = Field(..., description="Transition ID")
    name: str = Field(..., description="Transition name")
    to_status: str = Field(..., description="Target status name")


# ============================================================================
# Operation Result Models
# ============================================================================


class IssueCreated(BaseModel):
    """Result of creating an issue."""

    key: str = Field(..., description="Created issue key (e.g., 'PROJ-123')")
    url: str = Field(..., description="Issue URL")
    id: str = Field(..., description="Issue ID")


class CommentAdded(BaseModel):
    """Result of adding a comment."""

    id: str = Field(..., description="Comment ID")
    created: str = Field(..., description="Creation timestamp")
    author: str = Field(..., description="Comment author display name")


class IssueTransitioned(BaseModel):
    """Result of transitioning an issue."""

    key: str = Field(..., description="Issue key")
    status: str = Field(..., description="New status")


# ============================================================================
# Tool Input Models (for MCP)
# ============================================================================


class ListIssuesInput(BaseModel):
    """Input parameters for listing issues."""

    project_key: str = Field(..., description="Project key (e.g., 'PROJ')")
    status: Optional[str] = Field(default=None, description="Filter by status")
    assignee: Optional[str] = Field(
        default=None,
        description="Filter by assignee ('me', 'unassigned', or email/username)"
    )
    issue_type: Optional[str] = Field(default=None, description="Filter by issue type")
    max_results: int = Field(default=100, description="Maximum number of results")


class GetIssueInput(BaseModel):
    """Input parameters for getting issue details."""

    issue_key: str = Field(..., description="Issue key (e.g., 'PROJ-123')")


class GetIssueTypesInput(BaseModel):
    """Input parameters for getting issue types."""

    project_key: str = Field(..., description="Project key (e.g., 'PROJ')")


class CreateEpicInput(BaseModel):
    """Input parameters for creating an epic."""

    project_key: str = Field(..., description="Project key (e.g., 'PROJ')")
    summary: str = Field(..., description="Epic summary/title")
    description: Optional[str] = Field(default=None, description="Epic description (markdown supported)")


class CreateStoryInput(BaseModel):
    """Input parameters for creating a story."""

    project_key: str = Field(..., description="Project key (e.g., 'PROJ')")
    summary: str = Field(..., description="Story summary/title")
    description: Optional[str] = Field(default=None, description="Story description (markdown supported)")
    epic_key: Optional[str] = Field(default=None, description="Parent epic key")


class CreateTaskInput(BaseModel):
    """Input parameters for creating a task."""

    project_key: str = Field(..., description="Project key (e.g., 'PROJ')")
    summary: str = Field(..., description="Task summary/title")
    description: Optional[str] = Field(default=None, description="Task description (markdown supported)")
    parent_key: Optional[str] = Field(default=None, description="Parent issue key (epic or story)")


class CreateSubtaskInput(BaseModel):
    """Input parameters for creating a subtask."""

    parent_key: str = Field(..., description="Parent issue key (must be Story or Task)")
    summary: str = Field(..., description="Subtask summary/title")
    description: Optional[str] = Field(default=None, description="Subtask description (markdown supported)")
    assignee: Optional[str] = Field(
        default=None,
        description="Assignee (display name, email, or account ID)"
    )


class AddCommentInput(BaseModel):
    """Input parameters for adding a comment."""

    issue_key: str = Field(..., description="Issue key (e.g., 'PROJ-123')")
    comment: str = Field(..., description="Comment text (markdown supported)")


class TransitionIssueInput(BaseModel):
    """Input parameters for transitioning an issue."""

    issue_key: str = Field(..., description="Issue key (e.g., 'PROJ-123')")
    transition_name: str = Field(..., description="Transition name (e.g., 'In Progress', 'Done')")


class GetTransitionsInput(BaseModel):
    """Input parameters for getting available transitions."""

    issue_key: str = Field(..., description="Issue key (e.g., 'PROJ-123')")

