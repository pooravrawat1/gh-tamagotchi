"""
GitHub data models for API responses.

This module defines the Pydantic models for GitHub API data
including contribution data and activity events.
"""

from datetime import date as date_type, datetime
from typing import List, Dict, Any, Optional
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
    commit_days: List[ContributionDay] = Field(
        default_factory=list,
        description="List of days with commit-specific contribution counts"
    )


class GitHubProfileSnapshot(BaseModel):
    """A scored-pet-ready view of a GitHub profile.

    The snapshot is intentionally made up of GitHub facts rather than pet
    decisions.  Keeping this boundary explicit makes the game engine fully
    deterministic and means a cached snapshot can power the SVG, JSON API, and
    future profile page without each surface making its own GitHub calls.

    All activity fields cover the preceding 365 days. The default collector is
    public-only; the excluded private-count field exists solely for a future,
    explicitly opted-in collector.
    """

    username: str = Field(description="Canonical GitHub login")
    display_name: Optional[str] = Field(default=None, description="GitHub display name")
    avatar_url: Optional[str] = Field(default=None, description="GitHub avatar URL")
    account_created_at: datetime = Field(description="When the GitHub account was created")
    followers: int = Field(ge=0, default=0)
    public_repos: int = Field(ge=0, default=0)
    total_stars: int = Field(ge=0, default=0)
    languages: List[str] = Field(default_factory=list)

    recent_commits: int = Field(ge=0, default=0)
    recent_pull_requests: int = Field(ge=0, default=0)
    recent_reviews: int = Field(ge=0, default=0)
    recent_issues: int = Field(ge=0, default=0)
    recent_private_contributions: int = Field(
        ge=0,
        default=0,
        exclude=True,
        description="Authorized aggregate only; never emitted by the public profile API",
    )
    recent_active_days: int = Field(ge=0, default=0)
    recent_total_contributions: int = Field(ge=0, default=0)
    contribution_days: List[ContributionDay] = Field(default_factory=list)

    # GitHub only exposes this by summing bounded historical windows. It is
    # best-effort: a temporarily unavailable older window should not stop a pet
    # from rendering with its current-year activity.
    lifetime_contributions: int = Field(ge=0, default=0)
    fetched_at: datetime = Field(description="When this snapshot was collected")


class ActivityEvent(BaseModel):
    """
    Represents a GitHub activity event from the REST API.
    
    Captures GitHub activity events used by the game engine.
    """
    type: str = Field(description="Event type (e.g., PullRequestEvent)")
    created_at: datetime = Field(description="Timestamp when event was created")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional event-specific data"
    )
