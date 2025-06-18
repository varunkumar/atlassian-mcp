#!/usr/bin/env python3
"""
Detailed Confluence API diagnostic test.
This script tests various Confluence endpoints to identify permission issues.
"""

import asyncio
import base64
import os
import sys

import httpx


async def test_confluence_detailed():
    """Detailed Confluence API testing."""

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

    print(f"🔍 Detailed Confluence API Test")
    print(f"Domain: {domain}")
    print(f"Email: {email}")
    print(f"Token (first 20 chars): {token[:20]}...")
    print("=" * 60)

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:

        # Test 1: Basic API availability
        print("1. Testing basic API availability...")
        try:
            response = await client.get(f"{base_url}/wiki/rest/api/")
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   Response: {response.text[:300]}...")
        except Exception as e:
            print(f"   Exception: {e}")

        print()

        # Test 2: User information
        print("2. Testing user info endpoint...")
        try:
            response = await client.get(f"{base_url}/wiki/rest/api/user/current")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                user_data = response.json()
                print(f"   User: {user_data.get('displayName', 'Unknown')}")
                print(
                    f"   Account ID: {user_data.get('accountId', 'Unknown')}")
            else:
                print(f"   Response: {response.text[:300]}...")
        except Exception as e:
            print(f"   Exception: {e}")

        print()

        # Test 3: Spaces endpoint (the failing one)
        print("3. Testing spaces endpoint (the failing one)...")
        try:
            response = await client.get(f"{base_url}/wiki/rest/api/space", params={"limit": 1})
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Success! Found {data.get('size', 0)} spaces")
                if data.get('results'):
                    space = data['results'][0]
                    print(f"   First space: {space.get('name', 'Unknown')}")
            else:
                print(f"   Response: {response.text[:300]}...")

                # Try to get more specific error info
                if response.status_code == 401:
                    print("\n   🔍 401 Analysis:")
                    print("   - Token might be expired")
                    print("   - Token might not have proper scopes")
                    print("   - Email might not match token owner")
                    print("   - Domain access might be restricted")

        except Exception as e:
            print(f"   Exception: {e}")

        print()

        # Test 4: Content search (alternative endpoint)
        print("4. Testing content search endpoint...")
        try:
            response = await client.get(f"{base_url}/wiki/rest/api/content", params={"limit": 1})
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Success! Found {data.get('size', 0)} content items")
            else:
                print(f"   Response: {response.text[:300]}...")
        except Exception as e:
            print(f"   Exception: {e}")

        print()

        # Test 5: Check token format
        print("5. Token format analysis...")
        if token.startswith("ATATT3xFfGF0"):
            print("   ✅ Token format looks like a valid Atlassian API token")
        else:
            print("   ⚠️  Token format doesn't match expected Atlassian pattern")

        print(f"   Token length: {len(token)} characters")

        # Test 6: Different auth attempts
        print("\n6. Testing different authentication approaches...")

        # Try with different headers
        alt_headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json"
        }

        try:
            response = await client.get(f"{base_url}/wiki/rest/api/space",
                                        params={"limit": 1},
                                        headers=alt_headers)
            print(f"   Alt headers status: {response.status_code}")
        except Exception as e:
            print(f"   Alt headers exception: {e}")


async def main():
    """Main function."""
    await test_confluence_detailed()


if __name__ == "__main__":
    asyncio.run(main())
