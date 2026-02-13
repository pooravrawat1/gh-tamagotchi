#!/usr/bin/env python
"""
Verification script to check if the application is properly set up.
This script verifies imports, configuration, and database setup.
"""

import sys
import os
from pathlib import Path

def check_imports():
    """Verify all required modules can be imported."""
    print("Checking imports...")
    try:
        import fastapi
        print("  ✓ FastAPI")
        import sqlalchemy
        print("  ✓ SQLAlchemy")
        import httpx
        print("  ✓ httpx")
        import pydantic
        print("  ✓ Pydantic")
        import uvicorn
        print("  ✓ Uvicorn")
        print("✓ All imports successful\n")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}\n")
        return False

def check_configuration():
    """Verify configuration can be loaded."""
    print("Checking configuration...")
    try:
        from config.settings import get_settings
        settings = get_settings()
        print(f"  ✓ Database URL: {settings.database_url}")
        print(f"  ✓ Host: {settings.host}:{settings.port}")
        print(f"  ✓ Log Level: {settings.log_level}")
        print(f"  ✓ Cache TTL: {settings.cache_ttl_seconds}s")
        
        if settings.github_token == "ghp_your_github_token_here":
            print("  ⚠ GitHub token is placeholder (needed for testing)")
        else:
            print("  ✓ GitHub token configured")
        
        print("✓ Configuration loaded successfully\n")
        return True
    except Exception as e:
        print(f"✗ Configuration failed: {e}\n")
        return False

def check_database():
    """Verify database can be initialized."""
    print("Checking database...")
    try:
        from db.database import create_tables, get_engine
        
        # Create tables
        create_tables()
        print("  ✓ Database tables created")
        
        # Check connection
        engine = get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            print("  ✓ Database connection verified")
        
        print("✓ Database setup successful\n")
        return True
    except Exception as e:
        print(f"✗ Database setup failed: {e}\n")
        return False

def check_services():
    """Verify service classes can be instantiated."""
    print("Checking services...")
    try:
        from services.game_engine import GameEngine
        from rendering.svg_renderer import SVGRenderer
        from utils.cache import CacheService
        from config.settings import get_settings
        
        settings = get_settings()
        
        # Check GameEngine
        engine = GameEngine(settings)
        print("  ✓ GameEngine initialized")
        
        # Check SVGRenderer
        renderer = SVGRenderer()
        print("  ✓ SVGRenderer initialized")
        
        # Check CacheService
        cache = CacheService()
        print("  ✓ CacheService initialized")
        
        print("✓ All services initialized successfully\n")
        return True
    except Exception as e:
        print(f"✗ Service initialization failed: {e}\n")
        return False

def check_api():
    """Verify API application can be created."""
    print("Checking API application...")
    try:
        from api.main import app
        print("  ✓ FastAPI app created")
        
        # Check routes
        routes = [route.path for route in app.routes]
        print(f"  ✓ Routes registered: {', '.join(routes)}")
        
        print("✓ API application ready\n")
        return True
    except Exception as e:
        print(f"✗ API application failed: {e}\n")
        return False

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("GitHub Tamagotchi - Setup Verification")
    print("=" * 60 + "\n")
    
    checks = [
        check_imports,
        check_configuration,
        check_database,
        check_services,
        check_api,
    ]
    
    results = [check() for check in checks]
    
    print("=" * 60)
    if all(results):
        print("✓ All checks passed! Application is ready to run.")
        print("\nTo start the application, run:")
        print("  python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
        print("\nThen visit: http://localhost:8000/")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
