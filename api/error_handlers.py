"""
Centralized error handlers for GitHub Tamagotchi API.

This module defines exception handlers for all error scenarios that can occur
in the API, including GitHub service errors, validation errors, and general
server errors. All handlers are registered with the FastAPI application to
provide consistent error responses across all endpoints.
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from services.github_exceptions import (
    GitHubServiceError,
    GitHubUserNotFoundError,
    GitHubRateLimitError,
    GitHubTimeoutError,
    GitHubAPIError,
    GitHubNetworkError,
)

logger = logging.getLogger(__name__)


async def github_user_not_found_handler(
    request: Request,
    exc: GitHubUserNotFoundError
) -> JSONResponse:
    """
    Handle GitHub user not found errors (404).
    
    When a requested GitHub user does not exist, return a 404 response
    with a user-friendly error message.
    
    Args:
        request: The HTTP request that triggered the error
        exc: The GitHubUserNotFoundError exception
        
    Returns:
        JSONResponse with 404 status code and error details
    """
    logger.warning(f"GitHub user not found: {exc.username}")
    
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": f"GitHub user '{exc.username}' not found",
            "detail": "The requested GitHub user does not exist or is not accessible"
        }
    )


async def github_rate_limit_handler(
    request: Request,
    exc: GitHubRateLimitError
) -> JSONResponse:
    """
    Handle GitHub API rate limit errors (429).
    
    When the GitHub API rate limit is exceeded, return a 429 response
    with information about when the limit will reset.
    
    Args:
        request: The HTTP request that triggered the error
        exc: The GitHubRateLimitError exception
        
    Returns:
        JSONResponse with 429 status code and rate limit information
    """
    logger.error(f"GitHub API rate limit exceeded: {exc}")
    
    response_content = {
        "error": "rate_limit_exceeded",
        "message": "GitHub API rate limit exceeded",
        "detail": "Please try again later. The service respects GitHub's API rate limits."
    }
    
    # Include reset time if available
    if exc.reset_time:
        response_content["reset_time"] = exc.reset_time
    
    return JSONResponse(
        status_code=429,
        content=response_content,
        headers={"Retry-After": "300"}  # Suggest retry after 5 minutes
    )


async def github_timeout_handler(
    request: Request,
    exc: GitHubTimeoutError
) -> JSONResponse:
    """
    Handle GitHub API timeout errors (503).
    
    When a GitHub API request times out, return a 503 response indicating
    that the GitHub service is temporarily unavailable.
    
    Args:
        request: The HTTP request that triggered the error
        exc: The GitHubTimeoutError exception
        
    Returns:
        JSONResponse with 503 status code and service unavailable message
    """
    logger.error(f"GitHub API timeout: {exc}")
    
    return JSONResponse(
        status_code=503,
        content={
            "error": "service_unavailable",
            "message": "GitHub service is temporarily unavailable",
            "detail": "The request to GitHub API timed out. Please try again later."
        },
        headers={"Retry-After": "60"}  # Suggest retry after 1 minute
    )


async def github_api_error_handler(
    request: Request,
    exc: GitHubAPIError
) -> JSONResponse:
    """
    Handle general GitHub API errors (5xx, transient errors).
    
    For general GitHub API errors that are not specifically handled,
    return a 503 response indicating a service error.
    
    Args:
        request: The HTTP request that triggered the error
        exc: The GitHubAPIError exception
        
    Returns:
        JSONResponse with 503 status code and error details
    """
    logger.error(f"GitHub API error: {exc}")
    
    response_content = {
        "error": "github_service_error",
        "message": "Unable to fetch GitHub data",
        "detail": "An error occurred while communicating with GitHub. Please try again later."
    }
    
    # Include status code if available
    if exc.status_code:
        response_content["status_code"] = exc.status_code
    
    return JSONResponse(
        status_code=503,
        content=response_content,
        headers={"Retry-After": "60"}
    )


async def github_network_error_handler(
    request: Request,
    exc: GitHubNetworkError
) -> JSONResponse:
    """
    Handle network errors communicating with GitHub (503).
    
    When a network error occurs while communicating with GitHub,
    return a 503 response indicating a service error.
    
    Args:
        request: The HTTP request that triggered the error
        exc: The GitHubNetworkError exception
        
    Returns:
        JSONResponse with 503 status code and error details
    """
    logger.error(f"Network error communicating with GitHub: {exc}")
    
    return JSONResponse(
        status_code=503,
        content={
            "error": "network_error",
            "message": "Network error communicating with GitHub",
            "detail": "Unable to reach GitHub service. Please try again later."
        },
        headers={"Retry-After": "60"}
    )


async def github_service_error_handler(
    request: Request,
    exc: GitHubServiceError
) -> JSONResponse:
    """
    Handle generic GitHub service errors (500).
    
    Catch-all handler for any GitHubServiceError that is not specifically
    handled by more specific handlers.
    
    Args:
        request: The HTTP request that triggered the error
        exc: The GitHubServiceError exception
        
    Returns:
        JSONResponse with 500 status code and error details
    """
    logger.error(f"GitHub service error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An internal error occurred",
            "detail": "An unexpected error occurred while processing your request."
        }
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors (400).
    
    When request validation fails (e.g., missing required parameters,
    invalid parameter types), return a 400 response with validation details.
    
    Args:
        request: The HTTP request that triggered the error
        exc: The RequestValidationError exception
        
    Returns:
        JSONResponse with 400 status code and validation error details
    """
    logger.warning(f"Request validation error: {exc}")
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "detail": "The request contains invalid parameters",
            "errors": errors
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle all unhandled exceptions (500).
    
    Catch-all handler for any exception that is not specifically handled.
    Logs the full exception for debugging while returning a generic error
    message to the client.
    
    Args:
        request: The HTTP request that triggered the error
        exc: The exception that was raised
        
    Returns:
        JSONResponse with 500 status code and generic error message
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later."
        }
    )


def register_error_handlers(app: FastAPI) -> None:
    """
    Register all error handlers with the FastAPI application.
    
    This function should be called during application initialization to
    register all custom exception handlers with the FastAPI app.
    
    Args:
        app: The FastAPI application instance
        
    Example:
        from fastapi import FastAPI
        from api.error_handlers import register_error_handlers
        
        app = FastAPI()
        register_error_handlers(app)
    """
    # Register GitHub-specific exception handlers
    # Order matters: more specific exceptions should be registered first
    app.add_exception_handler(
        GitHubUserNotFoundError,
        github_user_not_found_handler
    )
    app.add_exception_handler(
        GitHubRateLimitError,
        github_rate_limit_handler
    )
    app.add_exception_handler(
        GitHubTimeoutError,
        github_timeout_handler
    )
    app.add_exception_handler(
        GitHubNetworkError,
        github_network_error_handler
    )
    app.add_exception_handler(
        GitHubAPIError,
        github_api_error_handler
    )
    app.add_exception_handler(
        GitHubServiceError,
        github_service_error_handler
    )
    
    # Register validation error handler
    app.add_exception_handler(
        RequestValidationError,
        validation_error_handler
    )
    
    # Register general exception handler (must be last)
    app.add_exception_handler(
        Exception,
        general_exception_handler
    )
    
    logger.info("Error handlers registered successfully")
