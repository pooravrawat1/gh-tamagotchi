"""
GitHub Tamagotchi API - Main Application Entry Point

This module initializes the FastAPI application and configures
the core application settings, middleware, and lifecycle events.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from db.database import create_tables, close_db_connection, check_db_health
from api.dependencies import (
    get_github_service,
    get_game_engine,
    get_pet_repository,
    get_svg_renderer,
    get_cache_service,
    get_pet_service
)
from api.routes import router as pet_router
from api.error_handlers import register_error_handlers
from utils.logging import setup_logging, get_logger

# Initialize logging (will be configured in startup event)
logger = get_logger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="GitHub Tamagotchi",
    description="A dynamic pet widget service driven by GitHub activity",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
register_error_handlers(app)

# Include routers
app.include_router(pet_router)


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    
    Performs initialization tasks:
    - Configures logging
    - Loads and validates configuration
    - Creates database tables
    - Initializes service dependencies
    - Validates GitHub token is configured
    - Logs startup information
    """
    # Load settings first to get log level
    settings = get_settings()
    
    # Configure logging based on settings
    setup_logging(
        log_level=settings.log_level,
        use_console=True,
        use_color=True
    )
    
    logger.info("Starting GitHub Tamagotchi application...")
    
    try:
        logger.info(f"Configuration loaded: database={settings.database_url}")
        
        # Validate GitHub token is configured
        if not settings.github_token or settings.github_token == "ghp_your_github_token_here":
            logger.warning(
                "GitHub token not properly configured. "
                "Set GITHUB_TOKEN environment variable with a valid token."
            )
        
        # Initialize database tables
        logger.info("Creating database tables...")
        create_tables()
        logger.info("Database tables created successfully")
        
        # Check database health
        db_healthy = await check_db_health()
        if db_healthy:
            logger.info("Database connection verified")
        else:
            logger.error("Database connection check failed")
        
        # Initialize service dependencies (this validates they can be created)
        logger.info("Initializing service dependencies...")
        cache = get_cache_service()
        github_service = await get_github_service()
        game_engine = get_game_engine(settings)
        pet_repository = get_pet_repository()
        svg_renderer = get_svg_renderer()
        pet_service = get_pet_service(
            github_service,
            game_engine,
            pet_repository,
            svg_renderer,
            cache,
            settings
        )
        logger.info("Service dependencies initialized successfully")
        
        logger.info("GitHub Tamagotchi application started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    
    Performs cleanup tasks:
    - Closes database connections
    - Cleans up resources
    """
    logger.info("Shutting down GitHub Tamagotchi application...")
    
    try:
        close_db_connection()
        logger.info("Database connections closed")
        logger.info("GitHub Tamagotchi application shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "service": "GitHub Tamagotchi",
        "version": "1.0.0",
        "endpoints": {
            "pet": "/pet?user=USERNAME",
            "stats": "/stats?user=USERNAME",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port)
