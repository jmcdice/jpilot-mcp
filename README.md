# jpilot-mcp

MCP (Model Context Protocol) Server for Jira - Agent-friendly Jira integration.

## Overview

jpilot-mcp is an MCP server that provides AI agents with direct access to Jira operations. It exposes a set of focused, type-safe tools for managing Jira issues, enabling agents to create epics, stories, tasks, subtasks, and manage issue workflows.

Built with [FastMCP](https://github.com/jlowin/fastmcp) and the official Jira Python library, jpilot-mcp makes it easy for AI agents to interact with Jira through natural language commands.

**Perfect for:**
- Managing Jira issues from Claude Desktop, Augment Code, or any MCP-compatible client
- Automating Jira workflows with AI agents
- Creating and tracking issues without leaving your development environment
- Building custom Jira integrations with natural language

## Features

- **11 Focused Tools**: List projects, create issues, add comments, transition statuses, and more
- **Discovery Tools**: List projects, issue types, and issues with flexible filtering
- **Issue Reading**: Get detailed issue information including comments, subtasks, and parent relationships
- **Issue Creation**: Create epics, stories, tasks, and subtasks with proper hierarchy and markdown support
- **Issue Management**: Add comments and transition issues through workflows
- **Type-Safe**: Built with Pydantic models for reliable data handling
- **Agent-Friendly**: Designed specifically for AI agent interaction via MCP
- **Production Ready**: Tested with real Jira Cloud instances

## Quick Start

**TL;DR:**
```bash
# 1. Clone and install
git clone https://github.com/jmcdice/jpilot-mcp.git
cd jpilot-mcp
./setup.sh

# 2. Edit .env with your Jira credentials
nano .env

# 3. Configure your MCP client (see Configuration section below)

# 4. Start using it!
# In Claude Desktop: "List all my Jira projects"
# In Auggie CLI: auggie "Show me all open issues in project PROJ"
```

## Requirements

- Python 3.11+ (tested with Python 3.13)
- Jira Cloud account with API token
- MCP-compatible client:
  - [Claude Desktop](https://claude.ai/download)
  - [Augment Code](https://www.augmentcode.com/) (VS Code, JetBrains, or CLI)
  - [Cline](https://github.com/cline/cline)
  - Any other MCP-compatible client

## Installation

### Option 1: Automated Setup (Recommended)

```bash
cd ~/dev/jpilot-mcp
./setup.sh
```

The setup script will:
- Create a virtual environment
- Install all dependencies
- Create a `.env` file from the template

Then edit `.env` with your Jira credentials.

### Option 2: Manual Setup

1. Clone or navigate to the project:
```bash
cd ~/dev/jpilot-mcp
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install the package in development mode:
```bash
pip install -e ".[dev]"
```

4. Configure your Jira credentials:
```bash
cp .env.example .env
# Edit .env with your Jira server, email, and API token
```

### Getting Your Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **"Create API token"**
3. Give it a name (e.g., "jpilot-mcp")
4. Copy the token - you'll need it for configuration
5. Your Jira server URL is typically: `https://your-company.atlassian.net`

## Configuration for MCP Clients

### Claude Desktop

Add to your Claude Desktop config file (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "jpilot": {
      "command": "python",
      "args": ["-m", "jpilot_mcp.server"],
      "env": {
        "JIRA_SERVER": "https://your-domain.atlassian.net",
        "JIRA_EMAIL": "your-email@example.com",
        "JIRA_API_TOKEN": "your-api-token",
        "JIRA_DEFAULT_PROJECT": "PROJ"
      }
    }
  }
}
```

**Optional**: Set `JIRA_DEFAULT_PROJECT` to your most-used project key (e.g., `"CIT"`) to avoid specifying it in every command.

**Note**: Use the full path to Python if needed:
```json
"command": "/path/to/jpilot-mcp/.venv/bin/python"
```

Restart Claude Desktop after making changes.

### Augment Code (Auggie CLI)

#### Option 1: Using add-json Command (Recommended)

```bash
auggie mcp add-json jpilot '{
  "command": "/path/to/jpilot-mcp/.venv/bin/python",
  "args": ["-m", "jpilot_mcp.server"],
  "env": {
    "JIRA_SERVER": "https://your-domain.atlassian.net",
    "JIRA_EMAIL": "your-email@example.com",
    "JIRA_API_TOKEN": "your-api-token",
    "JIRA_DEFAULT_PROJECT": "PROJ"
  }
}'
```

**Optional**: Set `JIRA_DEFAULT_PROJECT` to your most-used project key (e.g., `"CIT"`) to avoid specifying it in every command.

**Note**: Replace `/path/to/jpilot-mcp/.venv/bin/python` with the actual path to your virtual environment's Python.

#### Option 2: Manual Configuration

Edit `~/.augment/settings.json`:

```json
{
  "mcpServers": {
    "jpilot": {
      "command": "python",
      "args": ["-m", "jpilot_mcp.server"],
      "env": {
        "JIRA_SERVER": "https://your-domain.atlassian.net",
        "JIRA_EMAIL": "your-email@example.com",
        "JIRA_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

Verify installation:
```bash
auggie mcp list
```

In interactive mode, check status:
```bash
auggie
/mcp-status
```

**Tip**: If you encounter issues with the `--env` flags, use the `add-json` method instead, which handles complex configurations more reliably.

#### Quick Setup Script

You can create a setup script for easy configuration:

```bash
#!/bin/bash
# setup_auggie.sh

auggie mcp add-json jpilot '{
  "command": "/path/to/jpilot-mcp/.venv/bin/python",
  "args": ["-m", "jpilot_mcp.server"],
  "env": {
    "JIRA_SERVER": "https://your-domain.atlassian.net",
    "JIRA_EMAIL": "your-email@example.com",
    "JIRA_API_TOKEN": "your-api-token"
  }
}'

echo "✓ jpilot-mcp configured for Auggie"
echo "Test with: auggie \"List all my Jira projects\""
```

Make it executable and run:
```bash
chmod +x setup_auggie.sh
./setup_auggie.sh
```

### Augment Code (VS Code Extension)

1. Open VS Code
2. Open the Augment panel
3. Click the **settings icon** (⋮) → **Settings**
4. In the MCP section, click **Import from JSON**
5. Paste the configuration:

```json
{
  "mcpServers": {
    "jpilot": {
      "command": "python",
      "args": ["-m", "jpilot_mcp.server"],
      "env": {
        "JIRA_SERVER": "https://your-domain.atlassian.net",
        "JIRA_EMAIL": "your-email@example.com",
        "JIRA_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

6. Click **Save**

### Other MCP Clients

jpilot-mcp uses stdio transport and follows the MCP specification. Configure it in your client using:
- **Command**: `python -m jpilot_mcp.server`
- **Environment variables**: `JIRA_SERVER`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_DEFAULT_PROJECT` (optional)

## Default Project Configuration

You can optionally set a default project to avoid specifying `project_key` in every command:

```bash
export JIRA_DEFAULT_PROJECT=CIT
```

Or in your MCP client configuration:
```json
"env": {
  "JIRA_SERVER": "https://your-domain.atlassian.net",
  "JIRA_EMAIL": "your-email@example.com",
  "JIRA_API_TOKEN": "your-api-token",
  "JIRA_DEFAULT_PROJECT": "CIT"
}
```

**Benefits:**
- Shorter commands: `"List all epics"` instead of `"List all epics in CIT"`
- Less repetition when working primarily on one project
- Can still override by explicitly specifying a different project

**Example usage with default project:**
```bash
# Without default project:
auggie "List all epics in CIT"
auggie "Create a task in CIT with summary 'Update docs'"

# With JIRA_DEFAULT_PROJECT=CIT:
auggie "List all epics"
auggie "Create a task with summary 'Update docs'"

# Can still override:
auggie "List all epics in PROJ"  # Uses PROJ instead of CIT
```

## Available Tools

jpilot-mcp exposes 11 MCP tools for Jira operations:

### Discovery Tools

**`list_jira_projects`**
- Lists all accessible Jira projects
- Returns: Project key, name, description, type, and lead
- Example: "List all my Jira projects"

**`get_jira_issue_types`**
- Gets available issue types for a specific project
- Parameters: `project_key` (e.g., "PROJ")
- Returns: Issue type ID, name, description, and whether it's a subtask type
- Example: "What issue types are available in project PROJ?"

**`list_jira_issues`**
- Lists issues in a project with optional filters
- Parameters:
  - `project_key` (required)
  - `status` (optional: "To Do", "In Progress", "Done", etc.)
  - `assignee` (optional: "me", "unassigned", or email/username)
  - `issue_type` (optional: "Epic", "Story", "Task", etc.)
  - `max_results` (optional: default 100)
- Returns: List of issues with key details
- Example: "Show me all open tasks assigned to me in project PROJ"

### Issue Reading Tools

**`get_jira_issue`**
- Gets detailed information about a specific issue
- Parameters: `issue_key` (e.g., "PROJ-123")
- Returns: Full issue details including description, comments, subtasks, and parent
- Example: "Show me details for issue PROJ-123"

**`get_jira_transitions`**
- Gets available status transitions for an issue
- Parameters: `issue_key`
- Returns: List of available transitions with names and target statuses
- Example: "What status changes are available for PROJ-123?"

### Issue Creation Tools

**`create_jira_epic`**
- Creates a new epic
- Parameters:
  - `project_key` (required)
  - `summary` (required)
  - `description` (optional, markdown supported)
- Returns: Created epic key and URL
- Example: "Create an epic called 'Q4 Features' in project PROJ"

**`create_jira_story`**
- Creates a new story
- Parameters:
  - `project_key` (required)
  - `summary` (required)
  - `description` (optional, markdown supported)
  - `epic_key` (optional, to link to an epic)
- Returns: Created story key and URL
- Example: "Create a story 'User login' under epic PROJ-100"

**`create_jira_task`**
- Creates a new task
- Parameters:
  - `project_key` (required)
  - `summary` (required)
  - `description` (optional, markdown supported)
  - `parent_key` (optional, to link to epic or story)
- Returns: Created task key and URL
- Example: "Create a task 'Update documentation' in project PROJ"

**`create_jira_subtask`**
- Creates a subtask under a parent issue
- Parameters:
  - `parent_key` (required, must be Story or Task)
  - `summary` (required)
  - `description` (optional, markdown supported)
  - `assignee` (optional, display name, email, or account ID)
- Returns: Created subtask key and URL
- Example: "Create a subtask 'Write tests' under PROJ-123"

### Issue Management Tools

**`add_jira_comment`**
- Adds a comment to an issue
- Parameters:
  - `issue_key` (required)
  - `comment` (required, markdown supported)
- Returns: Comment ID, created timestamp, and author
- Example: "Add a comment to PROJ-123 saying 'Fixed in latest release'"

**`transition_jira_issue`**
- Changes the status of an issue
- Parameters:
  - `issue_key` (required)
  - `transition_name` (required, e.g., "In Progress", "Done")
- Returns: Updated issue with new status
- Note: Use `get_jira_transitions` first to see available transitions
- Example: "Move PROJ-123 to Done"

## Usage Examples

Once configured, you can interact with Jira naturally through your MCP client.

### Claude Desktop Examples

**Discovery:**
- "List all my Jira projects"
- "What issue types are available in project PROJ?"
- "Show me all open issues assigned to me in PROJ"

**Creating Issues:**
- "Create an epic called 'Q4 2024 Features' in project PROJ"
- "Create a story 'Implement user authentication' under epic PROJ-100"
- "Create a task 'Update API documentation' in PROJ"
- "Add a subtask 'Write unit tests' to PROJ-123"

**Managing Issues:**
- "Show me details for PROJ-123"
- "Add a comment to PROJ-123: 'Fixed in latest release'"
- "What status transitions are available for PROJ-123?"
- "Move PROJ-123 to In Progress"

**Complex Workflows:**
- "Create an epic for the new payment system, then create 3 stories under it for frontend, backend, and testing"
- "Find all bugs assigned to me and list them with their status"
- "Show me all issues in project PROJ that are in review"

### Augment Code (Auggie CLI) Examples

**Interactive Mode:**
```bash
auggie
```

Then use natural language:
```
List all my Jira projects

Show me all open issues in project PROJ

Create an epic called "Authentication System" in project PROJ

Add a comment to PROJ-123 saying "Implemented the new feature"

Move PROJ-123 to Done
```

**One-Shot Commands:**
```bash
# Quick queries
auggie "List all open bugs in project PROJ"

# Create issues
auggie "Create a task in PROJ for updating the API documentation"

# Complex workflows
auggie "Create an epic for the new dashboard, then create 3 tasks under it"
```

**Automation Examples:**
```bash
# In your CI/CD pipeline
auggie "Create a Jira task for deploying version $VERSION to production"

# Git hooks
auggie "Add a comment to PROJ-123 with the commit message: $(git log -1 --pretty=%B)"

# Scheduled tasks
auggie "List all issues in PROJ that haven't been updated in 30 days"
```

### Augment Code (VS Code) Examples

With the Augment extension, you can use jpilot-mcp directly in your editor:

- Select code → Ask Augment: "Create a Jira task for refactoring this function"
- In chat: "Show me all issues related to authentication in project PROJ"
- In chat: "Create a subtask for writing tests for the new API endpoint"

## Testing

### Manual Testing

Run the included test script to verify all tools work with your Jira instance:

```bash
source .venv/bin/activate
python test_server.py
```

This will:
- Test all discovery tools
- Validate issue creation tools
- Test issue reading with real issues
- Test issue management (comments and transitions)
- Clean up any test data created

### Running Unit Tests

```bash
pytest
```

### Code Formatting

```bash
black jpilot_mcp tests
```

### Type Checking

```bash
mypy jpilot_mcp
```

## Architecture

```
jpilot_mcp/
├── core/           # Core Jira business logic
│   ├── client.py   # Jira client wrapper
│   ├── issues.py   # Issue operations
│   ├── projects.py # Project operations
│   ├── search.py   # Search operations
│   └── models.py   # Pydantic data models
├── server.py       # MCP server implementation
└── config.py       # Configuration management
```

## Troubleshooting

### Connection Issues

**Error: "Failed to connect to Jira"**
- Verify your `JIRA_SERVER` URL is correct (should be `https://your-domain.atlassian.net`)
- Check that your API token is valid
- Ensure your email matches the Jira account

**Error: "Missing required environment variables"**
- Make sure you've created the `.env` file
- Verify all three variables are set: `JIRA_SERVER`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
- If using Claude Desktop, check the environment variables in the config file

### Issue Creation Issues

**Error: "Specify a valid issue type"**
- Use `get_jira_issue_types` to see available issue types for your project
- Issue type names are case-sensitive
- Some projects may not have all standard issue types (Epic, Story, Task)

**Error: "Field X is required"**
- Some Jira projects have required custom fields
- The MCP server currently only supports standard fields
- You may need to create issues manually in Jira if custom fields are required

### Claude Desktop Not Showing Tools

1. Check the config file location: `~/Library/Application Support/Claude/claude_desktop_config.json`
2. Verify the JSON syntax is valid
3. Restart Claude Desktop after making config changes
4. Check Claude Desktop logs for errors

## Notes

- **Markdown Support**: Descriptions and comments support markdown formatting, which is automatically converted to Jira's ADF (Atlassian Document Format)
- **Assignee Flexibility**: When assigning issues, you can use display names, email addresses, or Jira account IDs
- **Parent Relationships**: Stories can be linked to Epics, Tasks can be linked to Epics or Stories, and Subtasks must have a parent Story or Task
- **Status Transitions**: Available transitions depend on your Jira workflow configuration. Use `get_jira_transitions` to see what's available for each issue
- **Rate Limiting**: Jira Cloud has API rate limits. The server handles this gracefully, but very high-frequency operations may be throttled

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Support

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/jmcdice/jpilot-mcp/issues)
- **Discussions**: Ask questions or share ideas in [GitHub Discussions](https://github.com/jmcdice/jpilot-mcp/discussions)

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) by jlowin
- Uses the official [Jira Python library](https://github.com/pycontribs/jira)
- Inspired by the original jpilot CLI tool

## Related Projects

- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol specification
- [FastMCP](https://github.com/jlowin/fastmcp) - Python framework for building MCP servers
- [Augment Code](https://www.augmentcode.com/) - AI-powered coding assistant with MCP support
- [Claude Desktop](https://claude.ai/download) - Anthropic's desktop app with MCP support

