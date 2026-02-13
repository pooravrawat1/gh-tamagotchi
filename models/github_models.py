"""
GitHub data models for API responses.

This module defines the Pydantic models for GitHub API data
including contribution data and activity events.
"""

from datetime import date as date_type, datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ContributionDay(BaseModel):
    """Represents a single day's contribution data."""
    date: date_type = Field(description="Date of contributions")
    count: int = Field(ge=0, description="Number of contributions on this day")


class ContributionData(BaseModel):
    """
    Aggregated contribution data from GitHub GraphQL API.
    
    Contains total commits and daily breakdown for a specified period.
    """
    username: str = Field(description="GitHub username")
    total_commits: int = Field(ge=0, description="Total commits in the period")
    contribution_days: List[ContributionDay] = Field(
        default_factory=list,
        description="List of contribution days with counts"
    )


class ActivityEvent(BaseModel):
    """
    Represents a GitHub activity event from the REST API.
    
    Captures events like PushEvent, PullRequestEvent, etc.
    """
    type: str = Field(description="Event type (e.g., PushEvent, PullRequestEvent)")
    created_at: datetime = Field(description="Timestamp when event was created")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional event-specific data"
    )
