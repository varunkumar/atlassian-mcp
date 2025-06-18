#!/usr/bin/env python3
"""Command-line interface for the Atlassian MCP server."""

import argparse
import asyncio
import sys

from atlassian_mcp.server import main as server_main


def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Atlassian MCP Server - Read-only access to Confluence and Jira",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  ATLASSIAN_DOMAIN              Your Atlassian domain (e.g., company.atlassian.net)
  ATLASSIAN_EMAIL               Your Atlassian account email
  ATLASSIAN_CONFLUENCE_TOKEN    Your Confluence API token (optional)
  ATLASSIAN_JIRA_TOKEN         Your Jira API token (optional)
  ATLASSIAN_API_TOKEN          Legacy: single token for both services

Examples:
  atlassian-mcp                    # Start the MCP server
  python -m atlassian_mcp          # Alternative way to start
        """
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    return parser


def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
