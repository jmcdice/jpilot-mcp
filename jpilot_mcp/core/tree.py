"""Utilities for building project trees (Epics → Children).

This module provides helpers to fetch epics and their child issues (Stories, Tasks, etc.)
and to produce a human‑readable tree representation similar to:

  ● PROJ: Epics → Children (tree)

     • PROJ-1 — Epic title [In Progress]
        • PROJ-2 — Story/Task title [Done]
        • (no children yet)

The tree auto-detects what issue types are children of Epics in the project,
supporting both Story-based and Task-based workflows.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import JiraClient, JiraError
from .search import search_issues


def _safe_getattr(obj: Any, name: str, default: Any = None) -> Any:
    try:
        return getattr(obj, name)
    except Exception:
        return default


def _find_epic_link_field_id(client: JiraClient) -> Optional[str]:
    """Try to discover the custom field id used for "Epic Link".

    In company-managed Jira projects, the Epic → Story relationship is stored
    in a custom field commonly named "Epic Link" (e.g., customfield_10014).
    This function scans the field metadata to locate the appropriate field id.

    Returns the field id (e.g., "customfield_10014") if found, otherwise None.
    """
    try:
        fields = client.client.fields()
        for f in fields:
            # `fields()` typically returns dicts; handle objects defensively
            name = f.get("name") if isinstance(f, dict) else _safe_getattr(f, "name")
            if name and str(name).strip().lower() == "epic link":
                return f.get("id") if isinstance(f, dict) else _safe_getattr(f, "id")
    except Exception:
        # If we can't resolve the field id, we'll fall back to `parent`
        return None
    return None


def get_epics_and_children(
    client: JiraClient,
    project_key: str,
) -> List[Dict[str, Any]]:
    """Fetch all epics in a project and their child issues (auto-detected).

    Auto-detects what issue types are children of Epics by querying all
    non-Epic, non-Subtask issues and checking their parent relationships.

    This supports projects using:
    - Epic → Story (traditional Agile/Scrum)
    - Epic → Task (Kanban/operational teams)
    - Epic → mixed (Story + Task + other types)

    Attempts both linking strategies:
    - Team-managed: children have `parent` set to the epic
    - Company-managed: children use the custom "Epic Link" field

    Returns a list of epics keeping board/rank order, each with `children`.
    Each epic dict has: key, summary, status, url, assignee, children: List[dict].
    """
    # Fetch all epics
    epics = search_issues(
        client,
        jql=f'project = "{project_key}" AND issuetype = "Epic" ORDER BY rank ASC',
        max_results=1000,
    )

    # Fetch all potential child issues (non-Epic, non-Subtask)
    # This auto-detects whether the project uses Story, Task, or other types
    children = search_issues(
        client,
        jql=f'project = "{project_key}" AND issuetype != "Epic" AND issuetype != "Subtask" AND issuetype != "Sub-task" ORDER BY rank ASC',
        max_results=2000,
    )

    # Build epic map with empty children lists
    epic_map: Dict[str, Dict[str, Any]] = {}
    for e in epics:
        epic_map[e.key] = {
            "key": e.key,
            "summary": e.fields.summary,
            "status": e.fields.status.name,
            "assignee": e.fields.assignee.displayName if getattr(e.fields, "assignee", None) else "Unassigned",
            "url": f"{client.config.server}/browse/{e.key}",
            "children": [],
        }

    epic_link_field_id = _find_epic_link_field_id(client)

    # Process each potential child issue to find its parent epic
    for child in children:
        parent_key: Optional[str] = None

        # Strategy 1: team-managed projects often populate `parent`
        parent = _safe_getattr(child.fields, "parent")
        if parent and _safe_getattr(parent, "key"):
            parent_key = parent.key

        # Strategy 2: company-managed projects: check Epic Link custom field
        if not parent_key and epic_link_field_id:
            try:
                val = getattr(child.fields, epic_link_field_id)
            except Exception:
                val = None
            if val:
                if isinstance(val, str):
                    parent_key = val
                else:
                    # Try common attributes
                    parent_key = _safe_getattr(val, "key") or _safe_getattr(val, "id")
                    # If an id comes back (rare), try to resolve to key
                    if parent_key and isinstance(parent_key, str) and parent_key.isdigit():
                        try:
                            epic_issue = client.client.issue(parent_key)
                            parent_key = epic_issue.key
                        except Exception:
                            parent_key = None

        # If this child has a parent epic in our map, add it
        if parent_key and parent_key in epic_map:
            epic_map[parent_key]["children"].append(
                {
                    "key": child.key,
                    "summary": child.fields.summary,
                    "status": child.fields.status.name,
                    "issue_type": child.fields.issuetype.name,
                    "assignee": child.fields.assignee.displayName if getattr(child.fields, "assignee", None) else "Unassigned",
                    "url": f"{client.config.server}/browse/{child.key}",
                }
            )

    # Preserve epic order as returned by the JQL (rank asc)
    ordered_epics = [epic_map[e.key] for e in epics]
    return ordered_epics


def format_epics_children_tree(project_key: str, epics: List[Dict[str, Any]]) -> str:
    """Format a list of epics-with-children as a tree string.

    Consistent structure:
    - Header line
    - Blank line
    - Epic line (Markdown link, summary, status, assignee)
    - Child lines with tree connectors (├── for middle items, └── for last)
    - Blank line after each epic
    - Repeat for next epic

    Example:
        ● PROJ: Epics → Children (tree)

        [PROJ-1](url) — Epic Title [Status] — Assignee: Name
        ├── [PROJ-2](url) — Story 1 [Status] — Assignee: Name
        └── [PROJ-3](url) — Task 2 [Status] — Assignee: Name

        [PROJ-4](url) — Another Epic [Status] — Assignee: Name
        └── (no children yet)
    """
    lines: List[str] = []

    # Determine what child types are present across all epics
    child_types = set()
    for epic in epics:
        for child in epic.get("children", []):
            child_types.add(child.get("issue_type", ""))

    # Create a descriptive header based on what we found
    if child_types:
        if len(child_types) == 1:
            child_type_label = list(child_types)[0] + "s"
        else:
            child_type_label = "Children"
    else:
        child_type_label = "Children"

    lines.append(f"● {project_key}: Epics → {child_type_label} (tree)")
    lines.append("")

    for epic in epics:
        e_key = epic.get("key", "")
        e_summary = epic.get("summary", "")
        e_status = epic.get("status", "")
        e_url = epic.get("url", "")
        e_assignee = epic.get("assignee", "Unassigned")

        # Add blank line before each epic for better readability
        lines.append("")
        lines.append(f"[{e_key}]({e_url}) — {e_summary} [{e_status}] — Assignee: {e_assignee}")

        children = epic.get("children", []) or []
        if children:
            for i, child in enumerate(children):
                connector = "└──" if i == len(children) - 1 else "├──"
                c_key = child.get("key", "")
                c_summary = child.get("summary", "")
                c_status = child.get("status", "")
                c_url = child.get("url", "")
                c_assignee = child.get("assignee", "Unassigned")
                lines.append(
                    f"{connector} {c_key} — {c_summary} [{c_status}] — Assignee: {c_assignee}"
                )
        else:
            lines.append("└── (no children yet)")

    return "\n".join(lines)


# Backwards compatibility alias
def get_epics_and_stories(client: JiraClient, project_key: str) -> List[Dict[str, Any]]:
    """Deprecated: Use get_epics_and_children instead.

    This function is maintained for backwards compatibility but now uses
    the auto-detect logic to find all child issue types.
    """
    epics = get_epics_and_children(client, project_key)
    # Rename 'children' to 'stories' for backwards compatibility
    for epic in epics:
        epic["stories"] = epic.pop("children", [])
    return epics


def format_epics_stories_tree(project_key: str, epics: List[Dict[str, Any]]) -> str:
    """Deprecated: Use format_epics_children_tree instead.

    This function is maintained for backwards compatibility.
    """
    # Handle both old format (stories) and new format (children)
    normalized_epics = []
    for epic in epics:
        normalized = epic.copy()
        if "stories" in normalized and "children" not in normalized:
            normalized["children"] = normalized.pop("stories")
        normalized_epics.append(normalized)

    return format_epics_children_tree(project_key, normalized_epics)

