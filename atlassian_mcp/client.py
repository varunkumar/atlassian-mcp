"""Atlassian API client for Confluence and Jira."""

import base64
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import httpx
from pydantic import BaseModel


class AtlassianConfig(BaseModel):
    """Configuration for Atlassian API access."""
    domain: str
    email: str
    confluence_token: Optional[str] = None
    jira_token: Optional[str] = None

    @classmethod
    def from_env(cls) -> "AtlassianConfig":
        """Create configuration from environment variables."""
        domain = os.getenv("ATLASSIAN_DOMAIN")
        email = os.getenv("ATLASSIAN_EMAIL")
        confluence_token = os.getenv("ATLASSIAN_CONFLUENCE_TOKEN")
        jira_token = os.getenv("ATLASSIAN_JIRA_TOKEN")

        # Backward compatibility: if old single token is provided
        legacy_token = os.getenv("ATLASSIAN_API_TOKEN")
        if legacy_token and not confluence_token and not jira_token:
            confluence_token = legacy_token
            jira_token = legacy_token

        if not all([domain, email]):
            raise ValueError(
                "Missing required environment variables: "
                "ATLASSIAN_DOMAIN, ATLASSIAN_EMAIL"
            )

        if not confluence_token and not jira_token:
            raise ValueError(
                "At least one API token is required: "
                "ATLASSIAN_CONFLUENCE_TOKEN or ATLASSIAN_JIRA_TOKEN"
            )

        return cls(
            domain=domain,
            email=email,
            confluence_token=confluence_token,
            jira_token=jira_token
        )


class AtlassianClient:
    """Client for interacting with Atlassian APIs."""

    def __init__(self, config: AtlassianConfig):
        self.config = config
        self.base_url = f"https://{config.domain}"

        # Create separate clients for Confluence and Jira if tokens are available
        self.confluence_client = None
        self.jira_client = None

        if config.confluence_token:
            confluence_auth = f"{config.email}:{config.confluence_token}"
            confluence_auth_b64 = base64.b64encode(
                confluence_auth.encode('ascii')).decode('ascii')
            confluence_headers = {
                "Authorization": f"Basic {confluence_auth_b64}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            self.confluence_client = httpx.AsyncClient(
                headers=confluence_headers, timeout=30.0)

        if config.jira_token:
            jira_auth = f"{config.email}:{config.jira_token}"
            jira_auth_b64 = base64.b64encode(
                jira_auth.encode('ascii')).decode('ascii')
            jira_headers = {
                "Authorization": f"Basic {jira_auth_b64}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            self.jira_client = httpx.AsyncClient(
                headers=jira_headers, timeout=30.0)

    async def close(self):
        """Close the HTTP clients."""
        if self.confluence_client:
            await self.confluence_client.aclose()
        if self.jira_client:
            await self.jira_client.aclose()

    # URL parsing utilities
    def parse_confluence_url(self, url: str) -> Optional[str]:
        """
        Parse a Confluence URL to extract the page ID.

        Supports URLs like:
        - https://domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title
        - https://domain.atlassian.net/wiki/display/SPACE/Page+Title?pageId=123456
        - https://domain.atlassian.net/wiki/pages/viewpage.action?pageId=123456
        """
        try:
            parsed = urlparse(url)

            # Method 1: Extract from path like /wiki/spaces/SPACE/pages/123456/Page+Title
            path_match = re.search(
                r'/wiki/spaces/[^/]+/pages/(\d+)', parsed.path)
            if path_match:
                return path_match.group(1)

            # Method 2: Extract from query parameter pageId
            query_params = parse_qs(parsed.query)
            if 'pageId' in query_params:
                return query_params['pageId'][0]

            # Method 3: Extract from viewpage.action URL
            if 'viewpage.action' in parsed.path and 'pageId' in query_params:
                return query_params['pageId'][0]

            return None
        except Exception:
            return None

    def parse_jira_url(self, url: str) -> Optional[str]:
        """
        Parse a Jira URL to extract the issue key.

        Supports URLs like:
        - https://domain.atlassian.net/browse/PROJ-123
        - https://domain.atlassian.net/jira/software/projects/PROJ/boards/1?selectedIssue=PROJ-123
        """
        try:
            parsed = urlparse(url)

            # Method 1: Extract from /browse/ISSUE-KEY path
            browse_match = re.search(r'/browse/([A-Z]+-\d+)', parsed.path)
            if browse_match:
                return browse_match.group(1)

            # Method 2: Extract from selectedIssue query parameter
            query_params = parse_qs(parsed.query)
            if 'selectedIssue' in query_params:
                issue_key = query_params['selectedIssue'][0]
                # Validate it looks like an issue key
                if re.match(r'^[A-Z]+-\d+$', issue_key):
                    return issue_key

            # Method 3: Look for issue key pattern anywhere in the URL
            issue_match = re.search(r'([A-Z]+-\d+)', url)
            if issue_match:
                return issue_match.group(1)

            return None
        except Exception:
            return None

    # Confluence methods
    async def confluence_get_page(self, page_id: str) -> Dict[str, Any]:
        """Get a Confluence page by ID."""
        if not self.confluence_client:
            raise ValueError(
                "Confluence token not configured. Please set ATLASSIAN_CONFLUENCE_TOKEN.")

        url = f"{self.base_url}/wiki/rest/api/content/{page_id}"
        params = {
            "expand": "body.storage,space,version,ancestors"
        }

        response = await self.confluence_client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def confluence_search_pages(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for Confluence pages."""
        if not self.confluence_client:
            raise ValueError(
                "Confluence token not configured. Please set ATLASSIAN_CONFLUENCE_TOKEN.")

        url = f"{self.base_url}/wiki/rest/api/content/search"
        params = {
            "cql": f"text ~ \"{query}\" and type = page",
            "limit": limit,
            "expand": "space,version"
        }

        response = await self.confluence_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])

    async def confluence_list_spaces(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List Confluence spaces."""
        if not self.confluence_client:
            raise ValueError(
                "Confluence token not configured. Please set ATLASSIAN_CONFLUENCE_TOKEN.")

        url = f"{self.base_url}/wiki/rest/api/space"
        params = {
            "limit": limit,
            "expand": "description,homepage"
        }

        response = await self.confluence_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])

    async def confluence_get_page_by_url(self, page_url: str) -> Dict[str, Any]:
        """Get a Confluence page by URL."""
        page_id = self.parse_confluence_url(page_url)
        if not page_id:
            raise ValueError(f"Could not extract page ID from URL: {page_url}")
        return await self.confluence_get_page(page_id)

    # Jira methods
    async def jira_get_issue(self, issue_key: str) -> Dict[str, Any]:
        """Get a Jira issue by key."""
        if not self.jira_client:
            raise ValueError(
                "Jira token not configured. Please set ATLASSIAN_JIRA_TOKEN.")

        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        params = {
            "expand": "changelog,attachments,comments"
        }

        response = await self.jira_client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def jira_search_issues(self, jql: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for Jira issues using JQL."""
        if not self.jira_client:
            raise ValueError(
                "Jira token not configured. Please set ATLASSIAN_JIRA_TOKEN.")

        url = f"{self.base_url}/rest/api/3/search"
        params = {
            "jql": jql,
            "maxResults": limit,
            "expand": "changelog"
        }

        response = await self.jira_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("issues", [])

    async def jira_list_projects(self) -> List[Dict[str, Any]]:
        """List Jira projects."""
        if not self.jira_client:
            raise ValueError(
                "Jira token not configured. Please set ATLASSIAN_JIRA_TOKEN.")

        url = f"{self.base_url}/rest/api/3/project"
        params = {
            "expand": "description,lead,projectKeys"
        }

        response = await self.jira_client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def jira_get_issue_by_url(self, issue_url: str) -> Dict[str, Any]:
        """Get a Jira issue by URL."""
        issue_key = self.parse_jira_url(issue_url)
        if not issue_key:
            raise ValueError(
                f"Could not extract issue key from URL: {issue_url}")
        return await self.jira_get_issue(issue_key)
