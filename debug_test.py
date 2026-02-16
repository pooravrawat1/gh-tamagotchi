#!/usr/bin/env python
"""Debug script to test GitHub service."""

import asyncio
import logging
from services.github_service import GitHubService
from config.settings import Settings

# Set up logging to see errors
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test():
    """Test GitHub service."""
    try:
        settings = Settings()
        print(f"✓ Settings loaded")
        print(f"  Token: {settings.github_token[:30]}...")
        print(f"  GraphQL URL: {settings.github_graphql_url}")
        print(f"  REST URL: {settings.github_rest_url}")
        
        async with GitHubService(settings) as github_service:
            print(f"✓ GitHub service initialized")
            
            # Test validate_user_exists
            username = "pooravrawat1"
            print(f"\nTesting validate_user_exists('{username}')...")
            try:
                exists = await github_service.validate_user_exists(username)
                print(f"✓ User exists: {exists}")
            except Exception as e:
                print(f"✗ Error: {type(e).__name__}: {e}")
                logger.exception("Detailed error:")
                return
            
            # Test get_contribution_data
            print(f"\nTesting get_contribution_data('{username}', days=7)...")
            try:
                contrib_data = await github_service.get_contribution_data(username, days=7)
                print(f"✓ Contribution data retrieved")
                print(f"  Days: {len(contrib_data.days)}")
            except Exception as e:
                print(f"✗ Error: {type(e).__name__}: {e}")
                logger.exception("Detailed error:")
                return
            
            # Test get_recent_activity
            print(f"\nTesting get_recent_activity('{username}', limit=30)...")
            try:
                activity = await github_service.get_recent_activity(username, limit=30)
                print(f"✓ Recent activity retrieved: {len(activity)} events")
            except Exception as e:
                print(f"✗ Error: {type(e).__name__}: {e}")
                logger.exception("Detailed error:")
                return
    
    except Exception as e:
        print(f"✗ Fatal error: {type(e).__name__}: {e}")
        logger.exception("Detailed error:")

if __name__ == "__main__":
    asyncio.run(test())
