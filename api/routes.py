"""
API route handlers for GitHub Tamagotchi endpoints.

This module defines all HTTP endpoints for the pet widget service,
including pet SVG generation, stats retrieval, and health checks.
"""

import logging
from fastapi import APIRouter, Query, HTTPException, Response
from fastapi.responses import JSONResponse

from services.pet_service import PetService
from services.github_exceptions import (
    GitHubUserNotFoundError,
    GitHubRateLimitError,
    GitHubTimeoutError,
    GitHubServiceError
)
from api.dependencies import get_pet_service
from db.database import check_db_health

logger = logging.getLogger(__name__)

# Create router for pet-related endpoints
router = APIRouter()


@router.get("/pet")
async def get_pet_widget(user: str = Query(..., description="GitHub username")) -> Response:
    """
    Generate and return SVG pet widget for a GitHub user.
    
    This endpoint generates a dynamic SVG image representing a virtual pet
    whose stats and appearance are driven by the user's GitHub activity.
    The SVG can be embedded in GitHub README files using standard markdown
    image syntax.
    
    Args:
        user: GitHub username (required query parameter)
        
    Returns:
        Response with SVG content and image/svg+xml content-type
        
    Raises:
        HTTPException 400: If username parameter is missing or invalid
        HTTPException 404: If GitHub user not found
        HTTPException 429: If GitHub API rate limit exceeded
        HTTPException 503: If GitHub service is unavailable
        HTTPException 500: For internal server errors
        
    Example:
        GET /pet?user=octocat
        
        Returns SVG image that can be embedded as:
        ![My Pet](https://your-domain.com/pet?user=octocat)
    """
    logger.info(f"Received request for pet widget: user={user}")
    
    # Validate username parameter
    if not user or not user.strip():
        logger.warning("Request received with empty username parameter")
        raise HTTPException(
            status_code=400,
            detail="Username parameter is required and cannot be empty"
        )
    
    try:
        # Get pet service instance
        pet_service = get_pet_service()
        
        # Generate SVG for the user
        svg_content = await pet_service.get_pet_svg(user)
        
        logger.info(f"Successfully generated pet SVG for user: {user}")
        
        # Return SVG with appropriate content type
        return Response(
            content=svg_content,
            media_type="image/svg+xml",
            headers={
                "Cache-Control": "public, max-age=300",  # Cache for 5 minutes
                "Content-Type": "image/svg+xml; charset=utf-8"
            }
        )
        
    except GitHubUserNotFoundError as e:
        logger.warning(f"GitHub user not found: {user}")
        raise HTTPException(
            status_code=404,
            detail=f"GitHub user '{user}' not found"
        )
        
    except GitHubRateLimitError as e:
        logger.error(f"GitHub API rate limit exceeded for user: {user}")
        raise HTTPException(
            status_code=429,
            detail="GitHub API rate limit exceeded. Please try again later."
        )
        
    except GitHubTimeoutError as e:
        logger.error(f"GitHub API timeout for user: {user}")
        raise HTTPException(
            status_code=503,
            detail="GitHub service is currently unavailable. Please try again later."
        )
        
    except GitHubServiceError as e:
        logger.error(f"GitHub service error for user {user}: {e}")
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch GitHub data. Please try again later."
        )
        
    except Exception as e:
        logger.error(f"Unexpected error generating pet for user {user}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Please try again later."
        )


@router.get("/stats")
async def get_pet_stats(user: str = Query(..., description="GitHub username")) -> JSONResponse:
    """
    Get pet statistics as JSON for a GitHub user.
    
    This endpoint returns the raw pet state data in JSON format, including
    all stats (hunger, happiness, health, energy), level, stage, and timestamps.
    This allows clients to integrate pet data with other tools or display
    custom visualizations.
    
    Args:
        user: GitHub username (required query parameter)
        
    Returns:
        JSONResponse with pet state data
        
    Raises:
        HTTPException 400: If username parameter is missing or invalid
        HTTPException 404: If GitHub user not found
        HTTPException 429: If GitHub API rate limit exceeded
        HTTPException 503: If GitHub service is unavailable
        HTTPException 500: For internal server errors
        
    Example:
        GET /stats?user=octocat
        
        Returns JSON:
        {
            "username": "octocat",
            "hunger": 75,
            "happiness": 80,
            "health": 90,
            "energy": 85,
            "level": 5,
            "xp": 520,
            "stage": "baby",
            "last_updated": "2026-02-13T10:30:00"
        }
    """
    logger.info(f"Received request for pet stats: user={user}")
    
    # Validate username parameter
    if not user or not user.strip():
        logger.warning("Request received with empty username parameter")
        raise HTTPException(
            status_code=400,
            detail="Username parameter is required and cannot be empty"
        )
    
    try:
        # Get pet service instance
        pet_service = get_pet_service()
        
        # Get pet stats for the user
        pet_state = await pet_service.get_pet_stats(user)
        
        logger.info(f"Successfully retrieved pet stats for user: {user}")
        
        # Convert PetState to dict for JSON response
        pet_dict = pet_state.model_dump(mode='json')
        
        # Return JSON response with appropriate headers
        return JSONResponse(
            content=pet_dict,
            headers={
                "Cache-Control": "public, max-age=300",  # Cache for 5 minutes
                "Content-Type": "application/json; charset=utf-8"
            }
        )
        
    except GitHubUserNotFoundError as e:
        logger.warning(f"GitHub user not found: {user}")
        raise HTTPException(
            status_code=404,
            detail=f"GitHub user '{user}' not found"
        )
        
    except GitHubRateLimitError as e:
        logger.error(f"GitHub API rate limit exceeded for user: {user}")
        raise HTTPException(
            status_code=429,
            detail="GitHub API rate limit exceeded. Please try again later."
        )
        
    except GitHubTimeoutError as e:
        logger.error(f"GitHub API timeout for user: {user}")
        raise HTTPException(
            status_code=503,
            detail="GitHub service is currently unavailable. Please try again later."
        )
        
    except GitHubServiceError as e:
        logger.error(f"GitHub service error for user {user}: {e}")
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch GitHub data. Please try again later."
        )
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving stats for user {user}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Please try again later."
        )


@router.get("/health")
async def health_check() -> JSONResponse:
    """
    Health check endpoint for deployment platforms.
    
    This endpoint verifies that the application and its dependencies are
    functioning correctly. It checks database connectivity and returns
    appropriate status codes for monitoring and orchestration systems.
    
    Returns:
        JSONResponse with status information
        - 200 if healthy: {"status": "healthy"}
        - 503 if unhealthy: {"status": "unhealthy", "error": "error details"}
        
    Example:
        GET /health
        
        Success response (200):
        {
            "status": "healthy"
        }
        
        Failure response (503):
        {
            "status": "unhealthy",
            "error": "Database connection failed"
        }
    """
    logger.debug("Health check requested")
    
    try:
        # Check database connectivity
        db_healthy = await check_db_health()
        
        if not db_healthy:
            logger.error("Health check failed: Database connection check failed")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": "Database connection failed"
                }
            )
        
        logger.debug("Health check passed")
        return JSONResponse(
            status_code=200,
            content={"status": "healthy"}
        )
        
    except Exception as e:
        logger.error(f"Health check failed with exception: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )
