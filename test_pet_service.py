#!/usr/bin/env python
"""Debug script to test full pet service."""

import asyncio
import logging
from api.dependencies import get_pet_service

# Set up logging to see errors
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test():
    """Test pet service."""
    try:
        print("Testing PetService...")
        pet_service = get_pet_service()
        username = "pooravrawat1"
        
        print(f"\nGenerating pet SVG for '{username}'...")
        try:
            svg = await pet_service.get_pet_svg(username)
            print(f"✓ Pet SVG generated successfully!")
            print(f"  SVG length: {len(svg)} bytes")
            print(f"  Starts with: {svg[:100]}...")
        except Exception as e:
            print(f"✗ Error: {type(e).__name__}: {e}")
            logger.exception("Detailed error:")
    
    except Exception as e:
        print(f"✗ Fatal error: {type(e).__name__}: {e}")
        logger.exception("Detailed error:")

if __name__ == "__main__":
    asyncio.run(test())
