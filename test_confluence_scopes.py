#!/usr/bin/env python3
"""
Test script to identify required Confluence API scopes.
This will help determine what additional permissions are needed.
"""

import asyncio
import base64
import os

import httpx


async def test_confluence_scopes():
    """Test different Confluence endpoints to identify required scopes."""

    domain = os.getenv("ATLASSIAN_DOMAIN", "arcesium.atlassian.net")
    email = os.getenv("ATLASSIAN_EMAIL", "nagarajv@arcesium.com")
    token = os.getenv("ATLASSIAN_CONFLUENCE_TOKEN")

    if not token:
        print("❌ No ATLASSIAN_CONFLUENCE_TOKEN found")
        return

    base_url = f"https://{domain}"

    # Create auth header
    auth_string = f"{email}:{token}"
    auth_b64 = base64.b64encode(auth_string.encode('ascii')).decode('ascii')

    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    print("🔍 Confluence Scopes Analysis")
    print("Current scopes: read:content:confluence, read:content-details:confluence")
    print("=" * 70)

    # Common additional scopes that might be needed:
    additional_scopes_info = {
        "read:space:confluence": "View space information and metadata",
        "read:page:confluence": "View pages and their content",
        "read:blogpost:confluence": "View blog posts",
        "read:attachment:confluence": "View attachments",
        "read:comment:confluence": "View comments",
        "read:template:confluence": "View templates",
        "read:user:confluence": "View user information",
        "read:group:confluence": "View group information",
        "read:configuration:confluence": "View configuration",
        "read:audit-log:confluence": "View audit logs",
        "search:confluence": "Search content",
        "read:analytics:confluence": "View analytics data"
    }

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:

        print("📋 Testing endpoints that commonly require additional scopes:\n")

        endpoints_to_test = [
            {
                "name": "Spaces List",
                "url": f"{base_url}/wiki/rest/api/space",
                "params": {"limit": 1},
                "likely_scopes": ["read:space:confluence"]
            },
            {
                "name": "User Current",
                "url": f"{base_url}/wiki/rest/api/user/current",
                "params": {},
                "likely_scopes": ["read:user:confluence"]
            },
            {
                "name": "Content Search",
                "url": f"{base_url}/wiki/rest/api/content",
                "params": {"limit": 1},
                "likely_scopes": ["read:page:confluence", "search:confluence"]
            },
            {
                "name": "Space Details",
                "url": f"{base_url}/wiki/rest/api/space",
                "params": {"spaceKey": "TEST", "expand": "description,homepage"},
                "likely_scopes": ["read:space:confluence", "read:content-details:confluence"]
            },
            {
                "name": "Groups",
                "url": f"{base_url}/wiki/rest/api/group",
                "params": {"limit": 1},
                "likely_scopes": ["read:group:confluence"]
            }
        ]

        for endpoint in endpoints_to_test:
            print(f"🔍 Testing: {endpoint['name']}")
            print(f"   URL: {endpoint['url']}")
            print(
                f"   Likely required scopes: {', '.join(endpoint['likely_scopes'])}")

            try:
                response = await client.get(endpoint['url'], params=endpoint['params'])
                print(f"   Status: {response.status_code}")

                if response.status_code == 200:
                    print("   ✅ SUCCESS - Current scopes are sufficient")
                elif response.status_code == 401:
                    print("   ❌ 401 UNAUTHORIZED - Additional scopes likely needed")
                elif response.status_code == 403:
                    print("   ❌ 403 FORBIDDEN - Insufficient permissions/scopes")
                else:
                    print(f"   ⚠️  Unexpected status: {response.status_code}")

            except Exception as e:
                print(f"   ❌ Exception: {e}")

            print()

        print("=" * 70)
        print("🎯 RECOMMENDATIONS:")
        print()
        print("Based on the test results above, you likely need to add these scopes:")
        print()

        for scope, description in additional_scopes_info.items():
            print(f"   • {scope}")
            print(f"     └─ {description}")

        print()
        print("🔧 TO FIX:")
        print("1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens")
        print("2. Delete the current Confluence token")
        print("3. Create a new token with these scopes:")
        print("   ✓ read:content:confluence")
        print("   ✓ read:content-details:confluence")
        print("   ✓ read:space:confluence")
        print("   ✓ read:page:confluence")
        print("   ✓ read:user:confluence")
        print("   ✓ search:confluence")
        print()
        print(
            "💡 TIP: If unsure, start with broader 'read' permissions and narrow down later.")


async def main():
    """Main function."""
    await test_confluence_scopes()


if __name__ == "__main__":
    asyncio.run(main())
