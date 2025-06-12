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
export ATLASSIAN_API_TOKEN=your-api-token
```

Get your API token at: https://id.atlassian.com/manage-profile/security/api-tokens

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

For Claude Desktop, add to your configuration:

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "atlassian-mcp",
      "env": {
        "ATLASSIAN_DOMAIN": "your-company.atlassian.net",
        "ATLASSIAN_EMAIL": "your-email@company.com",
        "ATLASSIAN_API_TOKEN": "your-api-token"
      }
    }
  }
}
```
