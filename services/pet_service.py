"""
Pet service orchestration layer.

This module provides the main service that coordinates all pet-related operations,
including GitHub data fetching, game engine updates, persistence, and rendering.
"""

import logging
from datetime import datetime
from typing import Optional

from services.github_service import GitHubService
from services.game_engine import GameEngine
from db.repository import PetRepository
from rendering.svg_renderer import SVGRenderer
from utils.cache import CacheService
from models.pet_models import PetState
from config.settings import Settings

logger = logging.getLogger(__name__)


class PetService:
    """
    Main service for pet operations.
    
    Orchestrates interactions between GitHub data fetching, game engine calculations,
    database persistence, and SVG rendering. Manages caching to minimize API calls
    and improve response times.
    """
    
    def __init__(
        self,
        github_service: GitHubService,
        game_engine: GameEngine,
        repository: PetRepository,
        renderer: SVGRenderer,
        cache: CacheService,
        settings: Settings
    ):
        """
        Initialize PetService with all required dependencies.
        
        Args:
            github_service: Service for fetching GitHub data
            game_engine: Engine for calculating pet stat updates
            repository: Repository for pet persistence
            renderer: Renderer for generating SVG output
            cache: Cache service for storing GitHub data
            settings: Application settings
        """
        self.github_service = github_service
        self.game_engine = game_engine
        self.repository = repository
        self.renderer = renderer
        self.cache = cache
        self.settings = settings
        
        logger.debug("PetService initialized with all dependencies")
    
    def should_update_from_github(self, pet: PetState) -> bool:
        """
        Determine if GitHub data should be fetched.
        
        Checks if the pet's last update is older than the cache TTL threshold.
        If the pet hasn't been updated in more than cache_ttl_seconds, a fresh
        GitHub fetch is needed.
        
        Args:
            pet: The current pet state
            
        Returns:
            True if GitHub data should be fetched, False if cache is still valid
        """
        current_time = datetime.utcnow()
        time_since_update = (current_time - pet.last_updated).total_seconds()
        cache_ttl = self.settings.cache_ttl_seconds
        
        should_update = time_since_update > cache_ttl
        
        logger.debug(
            f"Cache check for {pet.username}: "
            f"time_since_update={time_since_update:.1f}s, "
            f"cache_ttl={cache_ttl}s, should_update={should_update}"
        )
        
        return should_update
    
    async def get_pet_svg(self, username: str) -> str:
        """
        Generate SVG widget for a GitHub user's pet.
        
        Main orchestration method that:
        1. Validates the GitHub user exists
        2. Fetches GitHub contribution and activity data (with caching)
        3. Gets or creates the pet from the database
        4. Updates pet stats via the game engine
        5. Persists the updated pet
        6. Renders and returns the SVG
        
        Args:
            username: GitHub username to generate pet widget for
            
        Returns:
            SVG string representing the pet widget
            
        Raises:
            GitHubUserNotFoundError: If the GitHub user doesn't exist
            GitHubRateLimitError: If GitHub API rate limit is exceeded
            GitHubTimeoutError: If GitHub API request times out
            GitHubServiceError: For other GitHub API errors
        """
        logger.info(f"Generating pet SVG for user: {username}")
        
        # Step 1: Validate GitHub user exists
        logger.debug(f"Validating GitHub user: {username}")
        await self.github_service.validate_user_exists(username)
        
        # Step 2: Get or create pet from database
        logger.debug(f"Getting or creating pet for user: {username}")
        pet = self.repository.get_or_create_pet(username)
        
        # Step 3: Check if we need to fetch fresh GitHub data
        current_time = datetime.utcnow()
        
        if self.should_update_from_github(pet):
            logger.debug(f"Cache expired, fetching fresh GitHub data for: {username}")
            
            # Fetch GitHub data
            logger.debug(f"Fetching contribution data for: {username}")
            contribution_data = await self.github_service.get_contribution_data(
                username,
                days=7
            )
            
            logger.debug(f"Fetching recent activity for: {username}")
            recent_activity = await self.github_service.get_recent_activity(
                username,
                limit=30
            )
            
            # Update pet stats via game engine
            logger.debug(f"Updating pet stats via game engine for: {username}")
            pet = self.game_engine.update_pet(
                pet,
                contribution_data,
                recent_activity,
                current_time
            )
            
            # Persist updated pet to database
            logger.debug(f"Persisting updated pet for: {username}")
            pet = self.repository.update_pet(pet)
            
            logger.info(f"Pet updated for {username}: "
                       f"hunger={pet.hunger}, happiness={pet.happiness}, "
                       f"level={pet.level}, stage={pet.stage}")
        else:
            logger.debug(f"Using cached pet state for: {username}")
        
        # Step 4: Render SVG from pet state
        logger.debug(f"Rendering SVG for: {username}")
        svg = self.renderer.render_pet(pet)
        
        logger.info(f"Successfully generated pet SVG for: {username}")
        
        return svg
    
    async def get_pet_stats(self, username: str) -> PetState:
        """
        Get pet stats as JSON for a GitHub user.
        
        Uses the same logic as get_pet_svg but returns the PetState object
        instead of rendering SVG. This allows clients to access raw pet data
        in JSON format.
        
        Args:
            username: GitHub username to get pet stats for
            
        Returns:
            PetState object containing all pet statistics
            
        Raises:
            GitHubUserNotFoundError: If the GitHub user doesn't exist
            GitHubRateLimitError: If GitHub API rate limit is exceeded
            GitHubTimeoutError: If GitHub API request times out
            GitHubServiceError: For other GitHub API errors
        """
        logger.info(f"Getting pet stats for user: {username}")
        
        # Step 1: Validate GitHub user exists
        logger.debug(f"Validating GitHub user: {username}")
        await self.github_service.validate_user_exists(username)
        
        # Step 2: Get or create pet from database
        logger.debug(f"Getting or creating pet for user: {username}")
        pet = self.repository.get_or_create_pet(username)
        
        # Step 3: Check if we need to fetch fresh GitHub data
        current_time = datetime.utcnow()
        
        if self.should_update_from_github(pet):
            logger.debug(f"Cache expired, fetching fresh GitHub data for: {username}")
            
            # Fetch GitHub data
            logger.debug(f"Fetching contribution data for: {username}")
            contribution_data = await self.github_service.get_contribution_data(
                username,
                days=7
            )
            
            logger.debug(f"Fetching recent activity for: {username}")
            recent_activity = await self.github_service.get_recent_activity(
                username,
                limit=30
            )
            
            # Update pet stats via game engine
            logger.debug(f"Updating pet stats via game engine for: {username}")
            pet = self.game_engine.update_pet(
                pet,
                contribution_data,
                recent_activity,
                current_time
            )
            
            # Persist updated pet to database
            logger.debug(f"Persisting updated pet for: {username}")
            pet = self.repository.update_pet(pet)
            
            logger.info(f"Pet updated for {username}: "
                       f"hunger={pet.hunger}, happiness={pet.happiness}, "
                       f"level={pet.level}, stage={pet.stage}")
        else:
            logger.debug(f"Using cached pet state for: {username}")
        
        logger.info(f"Successfully retrieved pet stats for: {username}")
        
        return pet
