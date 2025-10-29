"""Utilities for building project trees (Epics → Stories).

This module provides helpers to fetch epics and their child stories and to
produce a human‑readable tree representation similar to:

  ● PROJ: Epics → Stories (tree)

     • PROJ-1 — Epic title [In Progress]
        • PROJ-2 — Story title [Done]
        • (no child stories yet)
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


def get_epics_and_stories(
    client: JiraClient,
    project_key: str,
) -> List[Dict[str, Any]]:
    """Fetch all epics in a project and their child stories.

    Attempts both linking strategies:
    - Team-managed: stories have `parent` set to the epic
    - Company-managed: stories use the custom "Epic Link" field

    Returns a list of epics keeping board/rank order, each with `stories`.
    Each epic dict has: key, summary, status, url, stories: List[dict].
    """
    # Fetch epics and stories; keep JIRA issue objects to inspect fields
    epics = search_issues(
        client,
        jql=f'project = "{project_key}" AND issuetype = "Epic" ORDER BY rank ASC',
        max_results=1000,
    )
    stories = search_issues(
        client,
        jql=f'project = "{project_key}" AND issuetype = "Story" ORDER BY rank ASC',
        max_results=2000,
    )

    epic_map: Dict[str, Dict[str, Any]] = {}
    for e in epics:
        epic_map[e.key] = {
            "key": e.key,
            "summary": e.fields.summary,
            "status": e.fields.status.name,
            "assignee": e.fields.assignee.displayName if getattr(e.fields, "assignee", None) else "Unassigned",
            "url": f"{client.config.server}/browse/{e.key}",
            "stories": [],
        }

    epic_link_field_id = _find_epic_link_field_id(client)

    for s in stories:
        parent_key: Optional[str] = None
        # Strategy 1: team-managed projects often populate `parent`
        parent = _safe_getattr(s.fields, "parent")
        if parent and _safe_getattr(parent, "key"):
            parent_key = parent.key

        # Strategy 2: company-managed projects: check Epic Link custom field
        if not parent_key and epic_link_field_id:
            try:
                val = getattr(s.fields, epic_link_field_id)
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

        if parent_key and parent_key in epic_map:
            epic_map[parent_key]["stories"].append(
                {
                    "key": s.key,
                    "summary": s.fields.summary,
                    "status": s.fields.status.name,
                    "assignee": s.fields.assignee.displayName if getattr(s.fields, "assignee", None) else "Unassigned",
                    "url": f"{client.config.server}/browse/{s.key}",
                }
            )

    # Preserve epic order as returned by the JQL (rank asc)
    ordered_epics = [epic_map[e.key] for e in epics]
    return ordered_epics


def format_epics_stories_tree(project_key: str, epics: List[Dict[str, Any]]) -> str:
    """Format a list of epics-with-stories as a tree string.

    Consistent structure:
    - Header line
    - Blank line
    - Epic line (Markdown link, summary, status, assignee)
    - Story lines with tree connectors (├── for middle items, └── for last)
    - Blank line after each epic
    - Repeat for next epic

    Example:
        ● PROJ: Epics → Stories (tree)

        [PROJ-1](url) — Epic Title [Status] — Assignee: Name
        ├── [PROJ-2](url) — Story 1 [Status] — Assignee: Name
        └── [PROJ-3](url) — Story 2 [Status] — Assignee: Name

        [PROJ-4](url) — Another Epic [Status] — Assignee: Name
        └── (no child stories yet)
    """
    lines: List[str] = []
    lines.append(f"● {project_key}: Epics → Stories (tree)")
    lines.append("")

    for epic in epics:
        e_key = epic.get("key", "")
        e_summary = epic.get("summary", "")
        e_status = epic.get("status", "")
        e_url = epic.get("url", "")
        e_assignee = epic.get("assignee", "Unassigned")
        lines.append(f"[{e_key}]({e_url}) — {e_summary} [{e_status}] — Assignee: {e_assignee}")
        stories = epic.get("stories", []) or []
        if stories:
            for i, s in enumerate(stories):
                connector = "└──" if i == len(stories) - 1 else "├──"
                s_key = s.get("key", "")
                s_summary = s.get("summary", "")
                s_status = s.get("status", "")
                s_url = s.get("url", "")
                s_assignee = s.get("assignee", "Unassigned")
                lines.append(
                    f"{connector} [{s_key}]({s_url}) — {s_summary} [{s_status}] — Assignee: {s_assignee}"
                )
        else:
            lines.append("└── (no child stories yet)")
        lines.append("")

    return "\n".join(lines)

