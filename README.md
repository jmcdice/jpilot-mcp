# jpilot-mcp

MCP server for Jira. Control Jira from AI agents.

## What It Does

- List projects, issues, components
- Create epics, stories, tasks, subtasks
- Update issues, add comments, change status
- View project trees (Epic → Story/Task hierarchy)
- Auto-detects project structure (Story-based vs Task-based)

## Requirements

- Python 3.11+
- Jira Cloud account + API token
- MCP client (Claude Desktop, Augment Code, etc.)

## Install

```bash
git clone https://github.com/jmcdice/jpilot-mcp.git
cd jpilot-mcp
./setup.sh
```

Edit `.env`:
```bash
JIRA_SERVER=https://your-company.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=your-token-here
JIRA_DEFAULT_PROJECT=PROJ  # optional
```

Get API token: https://id.atlassian.com/manage-profile/security/api-tokens

## Configure MCP Client

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "jpilot": {
      "command": "/path/to/jpilot-mcp/.venv/bin/python",
      "args": ["-m", "jpilot_mcp.server"],
      "env": {
        "JIRA_SERVER": "https://your-company.atlassian.net",
        "JIRA_EMAIL": "you@example.com",
        "JIRA_API_TOKEN": "your-token",
        "JIRA_DEFAULT_PROJECT": "PROJ"
      }
    }
  }
}
```

Restart Claude Desktop.

### Augment Code

```bash
auggie mcp add-json jpilot '{
  "command": "/path/to/jpilot-mcp/.venv/bin/python",
  "args": ["-m", "jpilot_mcp.server"],
  "env": {
    "JIRA_SERVER": "https://your-company.atlassian.net",
    "JIRA_EMAIL": "you@example.com",
    "JIRA_API_TOKEN": "your-token",
    "JIRA_DEFAULT_PROJECT": "PROJ"
  }
}'
```

## Tools

### Discovery
- `list_jira_projects` - List all projects
- `get_jira_issue_types` - Get issue types for a project
- `get_jira_project_components` - List available components
- `list_jira_issues` - List/filter issues
- `get_jira_project_tree` - View Epic → Story/Task hierarchy

### Issue Operations
- `get_jira_issue` - Get issue details
- `create_jira_epic` - Create epic (supports components, duedate, priority, labels, assignee)
- `create_jira_story` - Create story
- `create_jira_task` - Create task
- `create_jira_subtask` - Create subtask
- `update_jira_issue` - Update issue fields
- `add_jira_comment` - Add comment
- `transition_jira_issue` - Change status
- `get_jira_transitions` - List available status transitions

## Usage

```
"List all projects"
"Show me the project tree for TSSE"
"What components are available in TSSE?"
"Create an epic called 'New Feature' with component 'Program/Project' and due date 2026-03-31"
"Create a story under epic PROJ-123"
"Show me all open issues assigned to me"
"Add a comment to PROJ-456"
"Move PROJ-789 to Done"
```

## Key Features

### Project Tree
- Auto-detects Epic → Story vs Epic → Task hierarchies
- Works with team-managed and company-managed projects
- Clean, readable tree output

### Epic Creation
- Supports required fields: components, duedate, priority, labels, assignee
- Use `get_jira_project_components` to discover available components
- All fields optional - adapts to project requirements

### Field Discovery
- List available components before creating issues
- View components, labels, duedate on existing issues
- Prevents "component not found" errors

## Notes

- Markdown supported in descriptions/comments
- ADF (Atlassian Document Format) auto-converted to plain text
- Set `JIRA_DEFAULT_PROJECT` to skip project_key in commands
- All list tools return complete results (no truncation)

## License

MIT

