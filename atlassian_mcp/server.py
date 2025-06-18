"""MCP server for Atlassian products (Confluence and Jira)."""

import asyncio
import json
import logging
from typing import Any, Sequence
from urllib.parse import urlparse

from mcp.server import Server
from mcp.server.models import InitializationOptions, ServerCapabilities
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool

from .client import AtlassianClient, AtlassianConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instance
client: AtlassianClient | None = None


async def get_client() -> AtlassianClient:
    """Get or create the Atlassian client."""
    global client
    if client is None:
        config = AtlassianConfig.from_env()
        client = AtlassianClient(config)
    return client


# Initialize the MCP server
server = Server("atlassian-mcp")


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="confluence://pages",
            name="Confluence Pages",
            description="Access to Confluence pages",
            mimeType="application/json",
        ),
        Resource(
            uri="jira://issues",
            name="Jira Issues",
            description="Access to Jira issues",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific resource."""
    parsed = urlparse(uri)

    if parsed.scheme == "confluence":
        if parsed.path.startswith("/page/"):
            page_id = parsed.path.split("/")[-1]
            client_instance = await get_client()
            page_data = await client_instance.confluence_get_page(page_id)
            return json.dumps(page_data, indent=2)
        else:
            raise ValueError(
                f"Invalid Confluence resource path: {parsed.path}")

    elif parsed.scheme == "jira":
        if parsed.path.startswith("/issue/"):
            issue_key = parsed.path.split("/")[-1]
            client_instance = await get_client()
            issue_data = await client_instance.jira_get_issue(issue_key)
            return json.dumps(issue_data, indent=2)
        else:
            raise ValueError(f"Invalid Jira resource path: {parsed.path}")

    else:
        raise ValueError(f"Unknown resource scheme: {parsed.scheme}")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        # Confluence tools
        Tool(
            name="confluence_get_page",
            description="Get a specific Confluence page by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The ID of the Confluence page"
                    }
                },
                "required": ["page_id"]
            }
        ),
        Tool(
            name="confluence_search_pages",
            description="Search for pages in Confluence",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for pages"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="confluence_list_spaces",
            description="List all available Confluence spaces",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of spaces to return",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="confluence_get_page_by_url",
            description="Get a Confluence page by its URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL of the Confluence page"
                    }
                },
                "required": ["url"]
            }
        ),
        # Jira tools
        Tool(
            name="jira_get_issue",
            description="Get a specific Jira issue by key",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The key of the Jira issue (e.g., PROJ-123)"
                    }
                },
                "required": ["issue_key"]
            }
        ),
        Tool(
            name="jira_search_issues",
            description="Search for issues using JQL (Jira Query Language)",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query string"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["jql"]
            }
        ),
        Tool(
            name="jira_list_projects",
            description="List all available Jira projects",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="jira_get_issue_by_url",
            description="Get a Jira issue by its URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL of the Jira issue"
                    }
                },
                "required": ["url"]
            }
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    client_instance = await get_client()

    try:
        if name == "confluence_get_page":
            page_id = arguments["page_id"]
            result = await client_instance.confluence_get_page(page_id)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "confluence_search_pages":
            query = arguments["query"]
            limit = arguments.get("limit", 10)
            result = await client_instance.confluence_search_pages(query, limit)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "confluence_list_spaces":
            limit = arguments.get("limit", 50)
            result = await client_instance.confluence_list_spaces(limit)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "confluence_get_page_by_url":
            url = arguments["url"]
            result = await client_instance.confluence_get_page_by_url(url)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_get_issue":
            issue_key = arguments["issue_key"]
            result = await client_instance.jira_get_issue(issue_key)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_search_issues":
            jql = arguments["jql"]
            limit = arguments.get("limit", 10)
            result = await client_instance.jira_search_issues(jql, limit)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_list_projects":
            result = await client_instance.jira_list_projects()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_get_issue_by_url":
            url = arguments["url"]
            result = await client_instance.jira_get_issue_by_url(url)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point for the server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="atlassian-mcp",
                server_version="0.1.0",
                capabilities=ServerCapabilities(
                    resources={},
                    tools={},
                    prompts={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
