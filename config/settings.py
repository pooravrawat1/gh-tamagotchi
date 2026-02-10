"""
Configuration management for GitHub Tamagotchi service.

This module defines all environment variables and settings using Pydantic BaseSettings
for validation and loading from .env files.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be configured via environment variables or .env file.
    """
    
    # GitHub API Configuration
    github_token: str = Field(
        ...,
        description="GitHub personal access token for API authentication"
    )
    github_graphql_url: str = Field(
        default="https://api.github.com/graphql",
        description="GitHub GraphQL API endpoint"
    )
    github_rest_url: str = Field(
        default="https://api.github.com",
        description="GitHub REST API base URL"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./pets.db",
        description="Database connection URL (SQLite or PostgreSQL)"
    )
    
    # Caching Configuration
    cache_ttl_seconds: int = Field(
        default=300,
        ge=0,
        description="Cache TTL in seconds (default: 5 minutes)"
    )
    
    # Game Engine Configuration - Decay Rates (per hour)
    hunger_decay_rate: float = Field(
        default=2.0,
        ge=0.0,
        description="Hunger decay rate per hour"
    )
    happiness_decay_rate: float = Field(
        default=3.0,
        ge=0.0,
        description="Happiness decay rate per hour"
    )
    energy_decay_rate: float = Field(
        default=1.5,
        ge=0.0,
        description="Energy decay rate per hour"
    )
    health_decay_rate: float = Field(
        default=0.5,
        ge=0.0,
        description="Health decay rate per hour"
    )
    
    # Game Engine Configuration - Activity Boosts
    commit_hunger_boost: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Hunger boost for commits today"
    )
    commit_happiness_boost: int = Field(
        default=5,
        ge=0,
        le=100,
        description="Happiness boost for commits today"
    )
    pr_merged_happiness_boost: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Happiness boost for merged PRs"
    )
    pr_merged_xp_boost: int = Field(
        default=20,
        ge=0,
        description="XP boost for merged PRs"
    )
    
    # Game Engine Configuration - Inactivity Penalties
    inactive_days_threshold: int = Field(
        default=3,
        ge=0,
        description="Days of inactivity before penalties apply"
    )
    inactive_happiness_penalty: int = Field(
        default=15,
        ge=0,
        le=100,
        description="Happiness penalty for inactivity"
    )
    inactive_energy_penalty: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Energy penalty for inactivity"
    )
    
    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(
                f"log_level must be one of {allowed_levels}, got '{v}'"
            )
        return v_upper
    
    @field_validator("github_token")
    @classmethod
    def validate_github_token(cls, v: str) -> str:
        """Validate GitHub token is not empty."""
        if not v or not v.strip():
            raise ValueError("github_token cannot be empty")
        return v.strip()
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


def get_settings() -> Settings:
    """
    Factory function to get settings instance.
    
    This allows for lazy loading and makes it easier to override
    settings in tests or different environments.
    """
    return Settings()


# Global settings instance (will be initialized when .env is present)
# For production use, call get_settings() or ensure .env file exists
try:
    settings = Settings()
except Exception:
    # Settings will be initialized when .env is available
    settings = None  # type: ignore
