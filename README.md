# Atlassian MCP Server

A read-only Model Context Protocol (MCP) server for Atlassian products (Confluence and Jira).

## Installation

```bash
pip install -e .
```

## Configuration

Set your Atlassian credentials as environment variables:

```bash
export ATLASSIAN_DOMAIN=your-company.atlassian.net
export ATLASSIAN_EMAIL=your-email@company.com

# Separate tokens for each service (recommended)
export ATLASSIAN_CONFLUENCE_TOKEN=your-confluence-token
export ATLASSIAN_JIRA_TOKEN=your-jira-token

# OR for backward compatibility, single token (if it has access to both)
export ATLASSIAN_API_TOKEN=your-api-token
```

### Creating API Tokens

1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"

**For Confluence:**

- When creating a Confluence token, select these scopes:
  - `read:content:confluence` - View pages, blog posts, comments, attachments
  - `read:content-details:confluence` - View content metadata and properties

**For Jira:**

- When creating a Jira token, you'll see different scope options. Look for:
  - Scopes that allow **reading issues** and **projects**
  - **Search** capabilities for JQL queries
  - Basic **browse** permissions

> **Note:** The exact scope names may vary in the Atlassian interface. Choose the minimal read-only scopes that allow viewing issues, projects, and searching. If you're unsure, you can start with broader read permissions and restrict them later.

## Usage

Start the MCP server:

```bash
atlassian-mcp
```

## Available Tools

### Confluence

- **confluence_get_page** - Get a page by ID
- **confluence_get_page_by_url** - Get a page by URL
- **confluence_search_pages** - Search for pages
- **confluence_list_spaces** - List all spaces

### Jira

- **jira_get_issue** - Get an issue by key (e.g., PROJ-123)
- **jira_get_issue_by_url** - Get an issue by URL
- **jira_search_issues** - Search issues using JQL
- **jira_list_projects** - List all projects

## Supported URLs

### Confluence Pages

- `https://domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title`
- `https://domain.atlassian.net/wiki/display/SPACE/Page+Title?pageId=123456`
- `https://domain.atlassian.net/wiki/pages/viewpage.action?pageId=123456`

### Jira Issues

- `https://domain.atlassian.net/browse/PROJ-123`
- `https://domain.atlassian.net/jira/software/projects/PROJ/boards/1?selectedIssue=PROJ-123`

## MCP Client Configuration

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "python",
      "args": ["-m", "atlassian_mcp.server"],
      "cwd": "/path/to/your/atlassian_mcp",
      "env": {
        "ATLASSIAN_DOMAIN": "your-company.atlassian.net",
        "ATLASSIAN_EMAIL": "your-email@company.com",
        "ATLASSIAN_CONFLUENCE_TOKEN": "your-confluence-token",
        "ATLASSIAN_JIRA_TOKEN": "your-jira-token"
      }
    }
  }
}
```

### API Endpoints Used

This server uses the following Atlassian REST API endpoints:

**Confluence REST API:**

- `GET /wiki/rest/api/content/{id}` - Get page content
- `GET /wiki/rest/api/content/search` - Search pages using CQL
- `GET /wiki/rest/api/space` - List spaces

**Jira REST API v3:**

- `GET /rest/api/3/issue/{issueIdOrKey}` - Get issue details
- `GET /rest/api/3/search` - Search issues using JQL
- `GET /rest/api/3/project` - List projects

All endpoints are read-only and require basic authentication with your email and API token.
