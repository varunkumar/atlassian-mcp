#!/usr/bin/env python3
"""
Test script to verify Atlassian API connections independently.
This script tests both Confluence and Jira API access using the same credentials
as the MCP server.
"""

import asyncio
import base64
import os
import sys
from typing import Optional

import httpx


class AtlassianTester:
    """Simple tester for Atlassian API connections."""

    def __init__(self):
        # Get credentials from environment (same as MCP server)
        self.domain = os.getenv("ATLASSIAN_DOMAIN")
        self.email = os.getenv("ATLASSIAN_EMAIL")
        self.confluence_token = os.getenv("ATLASSIAN_CONFLUENCE_TOKEN")
        self.jira_token = os.getenv("ATLASSIAN_JIRA_TOKEN")

        if not all([self.domain, self.email]):
            raise ValueError(
                "Missing ATLASSIAN_DOMAIN or ATLASSIAN_EMAIL environment variables")

        self.base_url = f"https://{self.domain}"
        print(f"Testing connection to: {self.base_url}")
        print(f"Using email: {self.email}")
        print(
            f"Confluence token configured: {'Yes' if self.confluence_token else 'No'}")
        print(f"Jira token configured: {'Yes' if self.jira_token else 'No'}")
        print("-" * 60)

    def _create_auth_header(self, token: str) -> str:
        """Create Basic Auth header."""
        auth_string = f"{self.email}:{token}"
        auth_b64 = base64.b64encode(
            auth_string.encode('ascii')).decode('ascii')
        return f"Basic {auth_b64}"

    async def test_confluence(self) -> bool:
        """Test Confluence API access."""
        if not self.confluence_token:
            print("❌ Confluence: No token configured")
            return False

        print("🔍 Testing Confluence API...")

        headers = {
            "Authorization": self._create_auth_header(self.confluence_token),
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
            try:
                # Test 1: List spaces (minimal info)
                print("  → Testing spaces list...")
                spaces_url = f"{self.base_url}/wiki/rest/api/space"
                spaces_params = {"limit": 5, "expand": "description"}

                response = await client.get(spaces_url, params=spaces_params)

                if response.status_code == 200:
                    data = response.json()
                    spaces = data.get("results", [])
                    print(f"  ✅ Success! Found {len(spaces)} spaces")

                    # Show first few spaces
                    for i, space in enumerate(spaces[:3]):
                        print(
                            f"     - {space.get('name', 'Unnamed')} ({space.get('key', 'No key')})")

                    return True
                else:
                    print(f"  ❌ Failed with status {response.status_code}")
                    print(f"     Response: {response.text[:200]}...")
                    return False

            except Exception as e:
                print(f"  ❌ Exception occurred: {str(e)}")
                return False

    async def test_jira(self) -> bool:
        """Test Jira API access."""
        if not self.jira_token:
            print("❌ Jira: No token configured")
            return False

        print("🔍 Testing Jira API...")

        headers = {
            "Authorization": self._create_auth_header(self.jira_token),
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
            try:
                # Test 1: List projects
                print("  → Testing projects list...")
                projects_url = f"{self.base_url}/rest/api/2/project"

                response = await client.get(projects_url)

                if response.status_code == 200:
                    projects = response.json()
                    print(f"  ✅ Success! Found {len(projects)} projects")

                    # Show first few projects
                    for i, project in enumerate(projects[:3]):
                        print(
                            f"     - {project.get('name', 'Unnamed')} ({project.get('key', 'No key')})")

                    return True
                else:
                    print(f"  ❌ Failed with status {response.status_code}")
                    print(f"     Response: {response.text[:200]}...")
                    return False

            except Exception as e:
                print(f"  ❌ Exception occurred: {str(e)}")
                return False

    async def run_tests(self):
        """Run all tests."""
        print("🧪 Atlassian API Connection Test")
        print("=" * 60)

        confluence_ok = await self.test_confluence()
        print()
        jira_ok = await self.test_jira()

        print()
        print("=" * 60)
        print("📊 Test Results:")
        print(f"   Confluence: {'✅ PASS' if confluence_ok else '❌ FAIL'}")
        print(f"   Jira:       {'✅ PASS' if jira_ok else '❌ FAIL'}")

        if confluence_ok and jira_ok:
            print("\n🎉 All tests passed! MCP server should work correctly.")
        elif confluence_ok or jira_ok:
            print("\n⚠️  Partial success. Check token permissions for failed service.")
        else:
            print("\n💥 All tests failed. Check credentials and network connectivity.")

        return confluence_ok, jira_ok


async def main():
    """Main test function."""
    try:
        tester = AtlassianTester()
        await tester.run_tests()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease set the following environment variables:")
        print("  export ATLASSIAN_DOMAIN=arcesium.atlassian.net")
        print("  export ATLASSIAN_EMAIL=your-email@arcesium.com")
        print("  export ATLASSIAN_CONFLUENCE_TOKEN=your-confluence-token")
        print("  export ATLASSIAN_JIRA_TOKEN=your-jira-token")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
