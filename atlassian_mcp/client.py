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
    api_token: str

    @classmethod
    def from_env(cls) -> "AtlassianConfig":
        """Create configuration from environment variables."""
        domain = os.getenv("ATLASSIAN_DOMAIN")
        email = os.getenv("ATLASSIAN_EMAIL")
        api_token = os.getenv("ATLASSIAN_API_TOKEN")

        if not all([domain, email, api_token]):
            raise ValueError(
                "Missing required environment variables: "
                "ATLASSIAN_DOMAIN, ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN"
            )

        return cls(domain=domain, email=email, api_token=api_token)


class AtlassianClient:
    """Client for interacting with Atlassian APIs."""

    def __init__(self, config: AtlassianConfig):
        self.config = config
        self.base_url = f"https://{config.domain}"

        # Create basic auth header
        auth_string = f"{config.email}:{config.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')

        self.headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

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
        url = f"{self.base_url}/wiki/rest/api/content/{page_id}"
        params = {
            "expand": "body.storage,space,version,ancestors"
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def confluence_search_pages(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for Confluence pages."""
        url = f"{self.base_url}/wiki/rest/api/content/search"
        params = {
            "cql": f"text ~ \"{query}\" and type = page",
            "limit": limit,
            "expand": "space,version"
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])

    async def confluence_list_spaces(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List Confluence spaces."""
        url = f"{self.base_url}/wiki/rest/api/space"
        params = {
            "limit": limit,
            "expand": "description,homepage"
        }

        response = await self.client.get(url, params=params)
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
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        params = {
            "expand": "changelog,attachments,comments"
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def jira_search_issues(self, jql: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for Jira issues using JQL."""
        url = f"{self.base_url}/rest/api/3/search"
        params = {
            "jql": jql,
            "maxResults": limit,
            "expand": "changelog"
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("issues", [])

    async def jira_list_projects(self) -> List[Dict[str, Any]]:
        """List Jira projects."""
        url = f"{self.base_url}/rest/api/3/project"
        params = {
            "expand": "description,lead,projectKeys"
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def jira_get_issue_by_url(self, issue_url: str) -> Dict[str, Any]:
        """Get a Jira issue by URL."""
        issue_key = self.parse_jira_url(issue_url)
        if not issue_key:
            raise ValueError(
                f"Could not extract issue key from URL: {issue_url}")
        return await self.jira_get_issue(issue_key)
