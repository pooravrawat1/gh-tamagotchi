"""
Dependency injection setup for FastAPI application.

This module provides factory functions for creating and configuring
all service dependencies. These are used by FastAPI's dependency injection
system to provide services to route handlers.
"""

import logging
import httpx
from typing import Optional

from config.settings import get_settings, Settings
from services.github_service import GitHubService
from services.game_engine import GameEngine
from db.repository import PetRepository
from db.database import get_session_factory
from rendering.svg_renderer import SVGRenderer
from utils.cache import CacheService
from services.pet_service import PetService

logger = logging.getLogger(__name__)

# Global instances (singletons)
_github_service: Optional[GitHubService] = None
_game_engine: Optional[GameEngine] = None
_pet_repository: Optional[PetRepository] = None
_svg_renderer: Optional[SVGRenderer] = None
_cache_service: Optional[CacheService] = None
_pet_service: Optional[PetService] = None
_http_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """
    Get or create the async HTTP client for GitHub API calls.
    
    Returns:
        httpx.AsyncClient instance configured for GitHub API
    """
    global _http_client
    
    if _http_client is None:
        logger.debug("Creating new AsyncClient for GitHub API")
        _http_client = httpx.AsyncClient(timeout=30.0)
    
    return _http_client


async def get_github_service() -> GitHubService:
    """
    Get or create the GitHub service.
    
    The GitHub service is created once and reused for all requests.
    It handles all interactions with the GitHub API.
    
    Returns:
        GitHubService instance
    """
    global _github_service
    
    if _github_service is None:
        logger.debug("Creating new GitHubService")
        settings = get_settings()
        http_client = await get_http_client()
        _github_service = GitHubService(
            settings=settings,
            http_client=http_client
        )
        logger.info("GitHubService initialized")
    
    return _github_service


def get_game_engine(settings: Optional[Settings] = None) -> GameEngine:
    """
    Get or create the game engine.
    
    The game engine is created once and reused for all requests.
    It handles all game logic including stat calculations and evolution.
    
    Args:
        settings: Optional Settings instance (if None, will be loaded)
    
    Returns:
        GameEngine instance
    """
    global _game_engine
    
    if _game_engine is None:
        logger.debug("Creating new GameEngine")
        if settings is None:
            settings = get_settings()
        
        _game_engine = GameEngine(
            hunger_decay_rate=settings.hunger_decay_rate,
            happiness_decay_rate=settings.happiness_decay_rate,
            energy_decay_rate=settings.energy_decay_rate,
            health_decay_rate=settings.health_decay_rate,
            commit_hunger_boost=settings.commit_hunger_boost,
            commit_happiness_boost=settings.commit_happiness_boost,
            pr_merged_happiness_boost=settings.pr_merged_happiness_boost,
            pr_merged_xp_boost=settings.pr_merged_xp_boost,
            inactive_days_threshold=settings.inactive_days_threshold,
            inactive_happiness_penalty=settings.inactive_happiness_penalty,
            inactive_energy_penalty=settings.inactive_energy_penalty
        )
        logger.info("GameEngine initialized")
    
    return _game_engine


def get_pet_repository() -> PetRepository:
    """
    Get or create the pet repository.
    
    The pet repository is created once and reused for all requests.
    It handles all database operations for pet persistence.
    
    Returns:
        PetRepository instance
    """
    global _pet_repository
    
    if _pet_repository is None:
        logger.debug("Creating new PetRepository")
        _pet_repository = PetRepository(session_factory=get_session_factory())
        logger.info("PetRepository initialized")
    
    return _pet_repository


def get_svg_renderer() -> SVGRenderer:
    """
    Get or create the SVG renderer.
    
    The SVG renderer is created once and reused for all requests.
    It handles all SVG generation for pet widgets.
    
    Returns:
        SVGRenderer instance
    """
    global _svg_renderer
    
    if _svg_renderer is None:
        logger.debug("Creating new SVGRenderer")
        _svg_renderer = SVGRenderer()
        logger.info("SVGRenderer initialized")
    
    return _svg_renderer


def get_cache_service() -> CacheService:
    """
    Get or create the cache service.
    
    The cache service is created once and reused for all requests.
    It handles in-memory caching of GitHub API responses.
    
    Returns:
        CacheService instance
    """
    global _cache_service
    
    if _cache_service is None:
        logger.debug("Creating new CacheService")
        _cache_service = CacheService()
        logger.info("CacheService initialized")
    
    return _cache_service


def get_pet_service(
    github_service: Optional[GitHubService] = None,
    game_engine: Optional[GameEngine] = None,
    pet_repository: Optional[PetRepository] = None,
    svg_renderer: Optional[SVGRenderer] = None,
    cache_service: Optional[CacheService] = None,
    settings: Optional[Settings] = None
) -> PetService:
    """
    Get or create the pet service.
    
    The pet service is the main orchestration service that coordinates
    all pet-related operations. It's created once and reused for all requests.
    
    Args:
        github_service: Optional GitHubService (if None, will be created)
        game_engine: Optional GameEngine (if None, will be created)
        pet_repository: Optional PetRepository (if None, will be created)
        svg_renderer: Optional SVGRenderer (if None, will be created)
        cache_service: Optional CacheService (if None, will be created)
        settings: Optional Settings (if None, will be loaded)
    
    Returns:
        PetService instance
    """
    global _pet_service
    
    if _pet_service is None:
        logger.debug("Creating new PetService")
        
        if settings is None:
            settings = get_settings()
        
        if github_service is None:
            # Note: This is synchronous, but get_github_service is async
            # In production, this should be called during startup
            logger.warning("GitHubService not provided to get_pet_service")
        
        if game_engine is None:
            game_engine = get_game_engine(settings)
        
        if pet_repository is None:
            pet_repository = get_pet_repository()
        
        if svg_renderer is None:
            svg_renderer = get_svg_renderer()
        
        if cache_service is None:
            cache_service = get_cache_service()
        
        if github_service is None:
            raise ValueError("GitHubService must be provided to PetService")
        
        _pet_service = PetService(
            github_service=github_service,
            game_engine=game_engine,
            repository=pet_repository,
            renderer=svg_renderer,
            cache=cache_service,
            settings=settings
        )
        logger.info("PetService initialized")
    
    return _pet_service


async def get_pet_service_dependency() -> PetService:
    """
    FastAPI dependency for PetService.

    This async wrapper ensures the GitHub service can be created even when a
    request path is exercised without the startup event pre-warming services.
    """
    github_service = await get_github_service()
    return get_pet_service(github_service=github_service)


def reset_dependencies() -> None:
    """
    Reset all dependency singletons.
    
    This is useful for testing or when you need to reinitialize services.
    WARNING: This should only be called during testing or shutdown.
    """
    global _github_service, _game_engine, _pet_repository, _svg_renderer, _cache_service, _pet_service, _http_client
    
    logger.debug("Resetting all service dependencies")
    
    if _http_client is not None:
        # Note: AsyncClient cleanup should be done in async context
        _http_client = None
    
    _github_service = None
    _game_engine = None
    _pet_repository = None
    _svg_renderer = None
    _cache_service = None
    _pet_service = None
