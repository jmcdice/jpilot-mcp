"""Core Jira functionality."""

from .client import JiraClient, JiraConnectionError, JiraError, create_jira_client
from .projects import list_projects, get_project, get_issue_types
from .search import search_issues, list_issues, get_issue, get_transitions
from .issues import (
    create_issue,
    create_epic,
    create_story,
    create_task,
    create_subtask,
    add_comment,
    transition_issue,
)
from .models import (
    # Project models
    Project,
    IssueType,
    # Issue models
    IssueReference,
    Comment,
    IssueSummary,
    IssueDetail,
    Transition,
    # Result models
    IssueCreated,
    CommentAdded,
    IssueTransitioned,
    # Input models
    ListIssuesInput,
    GetIssueInput,
    GetIssueTypesInput,
    CreateEpicInput,
    CreateStoryInput,
    CreateTaskInput,
    CreateSubtaskInput,
    AddCommentInput,
    TransitionIssueInput,
    GetTransitionsInput,
)

__all__ = [
    # Client
    "JiraClient",
    "JiraConnectionError",
    "JiraError",
    "create_jira_client",
    # Projects
    "list_projects",
    "get_project",
    "get_issue_types",
    # Search
    "search_issues",
    "list_issues",
    "get_issue",
    "get_transitions",
    # Issues
    "create_issue",
    "create_epic",
    "create_story",
    "create_task",
    "create_subtask",
    "add_comment",
    "transition_issue",
    # Models - Project
    "Project",
    "IssueType",
    # Models - Issue
    "IssueReference",
    "Comment",
    "IssueSummary",
    "IssueDetail",
    "Transition",
    # Models - Results
    "IssueCreated",
    "CommentAdded",
    "IssueTransitioned",
    # Models - Inputs
    "ListIssuesInput",
    "GetIssueInput",
    "GetIssueTypesInput",
    "CreateEpicInput",
    "CreateStoryInput",
    "CreateTaskInput",
    "CreateSubtaskInput",
    "AddCommentInput",
    "TransitionIssueInput",
    "GetTransitionsInput",
]

