"""
GitHub Tamagotchi API - Main Application Entry Point

This module initializes the FastAPI application and configures
the core application settings, middleware, and lifecycle events.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    
    This will be used to:
    - Initialize database tables
    - Validate configuration
    - Set up services
    """
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    
    This will be used to:
    - Close database connections
    - Clean up resources
    """
    pass


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
    uvicorn.run(app, host="0.0.0.0", port=8000)
