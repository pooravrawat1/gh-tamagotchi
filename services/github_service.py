"""
GitHub API service for fetching user data and activity.

This module provides async methods to interact with GitHub's GraphQL and REST APIs,
including user validation, contribution data fetching, and activity event retrieval.
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta, date
import httpx

from models.github_models import ContributionData, ContributionDay, ActivityEvent
from config.settings import Settings

logger = logging.getLogger(__name__)


class GitHubService:
    """
    Service for interacting with GitHub APIs.
    
    Handles authentication, user validation, and data fetching from both
    GraphQL and REST endpoints.
    """
    
    def __init__(self, settings: Settings, http_client: Optional[httpx.AsyncClient] = None):
        """
        Initialize GitHub service with configuration and HTTP client.
        
        Args:
            settings: Application settings containing GitHub token and API URLs
            http_client: Optional async HTTP client. If not provided, one will be created.
        """
        self.settings = settings
        self.token = settings.github_token
        self.graphql_url = settings.github_graphql_url
        self.rest_url = settings.github_rest_url
        self.http_client = http_client
        self._owns_client = http_client is None
        
        # Headers for GitHub API authentication
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Tamagotchi",
        }
        
        # Headers for GraphQL requests
        self.graphql_headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "GitHub-Tamagotchi",
        }
    
    async def _get_client(self) -> httpx.AsyncClient:
        """
        Get or create async HTTP client.
        
        Returns:
            Async HTTP client instance
        """
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        return self.http_client
    
    async def close(self) -> None:
        """Close HTTP client if we own it."""
        if self._owns_client and self.http_client is not None:
            await self.http_client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def validate_user_exists(self, username: str) -> bool:
        """
        Validate that a GitHub user exists.
        
        Uses the GitHub REST API to check if a user exists by attempting
        to fetch their public profile information.
        
        Args:
            username: GitHub username to validate
            
        Returns:
            True if user exists, False otherwise
            
        Raises:
            httpx.HTTPError: If there's a network or HTTP error (other than 404)
        """
        if not username or not username.strip():
            logger.warning("Empty username provided to validate_user_exists")
            return False
        
        username = username.strip()
        
        try:
            client = await self._get_client()
            url = f"{self.rest_url}/users/{username}"
            
            response = await client.get(url, headers=self.headers)
            
            if response.status_code == 200:
                logger.debug(f"GitHub user '{username}' exists")
                return True
            elif response.status_code == 404:
                logger.debug(f"GitHub user '{username}' not found")
                return False
            else:
                # Log unexpected status codes but treat as error
                logger.warning(
                    f"Unexpected status code {response.status_code} "
                    f"when validating user '{username}'"
                )
                response.raise_for_status()
                return False
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"GitHub user '{username}' not found (404)")
                return False
            logger.error(
                f"HTTP error validating GitHub user '{username}': {e.response.status_code}"
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error validating GitHub user '{username}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error validating GitHub user '{username}': {e}")
            raise
    
    async def get_contribution_data(self, username: str, days: int = 7) -> ContributionData:
        """
        Fetch contribution calendar data via GitHub GraphQL API.
        
        Retrieves the user's contribution calendar for the specified number of days
        and parses it into a ContributionData model.
        
        Args:
            username: GitHub username to fetch contributions for
            days: Number of days to look back (default: 7)
            
        Returns:
            ContributionData object containing total commits and daily breakdown
            
        Raises:
            httpx.HTTPError: If there's a network or HTTP error
            ValueError: If the GraphQL response is invalid or missing expected data
        """
        if not username or not username.strip():
            logger.warning("Empty username provided to get_contribution_data")
            raise ValueError("Username cannot be empty")
        
        username = username.strip()
        
        # Calculate date range
        to_date = datetime.utcnow().date()
        from_date = to_date - timedelta(days=days - 1)
        
        # GraphQL query for contribution calendar
        query = """
        query($userName:String!, $from:DateTime!, $to:DateTime!) {
            user(login: $userName) {
                contributionsCollection(from: $from, to: $to) {
                    contributionCalendar {
                        totalContributions
                        weeks {
                            contributionDays {
                                date
                                contributionCount
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "userName": username,
            "from": f"{from_date}T00:00:00Z",
            "to": f"{to_date}T23:59:59Z",
        }
        
        try:
            client = await self._get_client()
            
            response = await client.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers=self.graphql_headers,
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Check for GraphQL errors
            if "errors" in data:
                error_messages = [error.get("message", "Unknown error") for error in data["errors"]]
                logger.error(f"GraphQL error fetching contributions for '{username}': {error_messages}")
                raise ValueError(f"GraphQL error: {', '.join(error_messages)}")
            
            # Parse the response
            user_data = data.get("data", {}).get("user")
            if not user_data:
                logger.warning(f"No user data returned for '{username}'")
                raise ValueError(f"User '{username}' not found in GraphQL response")
            
            contributions_collection = user_data.get("contributionsCollection", {})
            contribution_calendar = contributions_collection.get("contributionCalendar", {})
            
            total_contributions = contribution_calendar.get("totalContributions", 0)
            weeks = contribution_calendar.get("weeks", [])
            
            # Parse contribution days
            contribution_days = []
            for week in weeks:
                for day_data in week.get("contributionDays", []):
                    contribution_days.append(
                        ContributionDay(
                            date=date.fromisoformat(day_data["date"]),
                            count=day_data["contributionCount"],
                        )
                    )
            
            logger.debug(
                f"Fetched {total_contributions} contributions for '{username}' "
                f"over {len(contribution_days)} days"
            )
            
            return ContributionData(
                username=username,
                total_commits=total_contributions,
                contribution_days=contribution_days,
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching contributions for '{username}': {e.response.status_code}"
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error fetching contributions for '{username}': {e}")
            raise
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing contribution data for '{username}': {e}")
            raise ValueError(f"Failed to parse contribution data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching contributions for '{username}': {e}")
            raise
    
    async def get_recent_activity(self, username: str, limit: int = 30) -> List[ActivityEvent]:
        """
        Fetch recent activity events via GitHub REST API.
        
        Retrieves the user's recent events from the GitHub REST API and filters
        for relevant event types (PushEvent, PullRequestEvent).
        
        Args:
            username: GitHub username to fetch activity for
            limit: Maximum number of events to fetch (default: 30)
            
        Returns:
            List of ActivityEvent objects containing relevant GitHub events
            
        Raises:
            httpx.HTTPError: If there's a network or HTTP error
            ValueError: If the response is invalid or missing expected data
        """
        if not username or not username.strip():
            logger.warning("Empty username provided to get_recent_activity")
            raise ValueError("Username cannot be empty")
        
        username = username.strip()
        
        # Relevant event types for pet activity
        relevant_event_types = {"PushEvent", "PullRequestEvent"}
        
        try:
            client = await self._get_client()
            url = f"{self.rest_url}/users/{username}/events"
            
            # Fetch events with pagination
            params = {"per_page": min(limit, 100)}  # GitHub API max is 100 per page
            
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            events_data = response.json()
            
            if not isinstance(events_data, list):
                logger.warning(f"Unexpected response format for events from '{username}'")
                raise ValueError("Expected list of events from GitHub API")
            
            # Parse and filter events
            activity_events = []
            for event_data in events_data[:limit]:
                event_type = event_data.get("type")
                
                # Only include relevant event types
                if event_type not in relevant_event_types:
                    continue
                
                try:
                    # Parse the event
                    created_at_str = event_data.get("created_at")
                    if not created_at_str:
                        logger.debug(f"Event missing created_at timestamp for '{username}'")
                        continue
                    
                    # Parse ISO format datetime
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    
                    # Extract relevant metadata based on event type
                    metadata = {}
                    
                    if event_type == "PushEvent":
                        payload = event_data.get("payload", {})
                        metadata["commits"] = payload.get("size", 0)
                        metadata["ref"] = payload.get("ref", "")
                    
                    elif event_type == "PullRequestEvent":
                        payload = event_data.get("payload", {})
                        metadata["action"] = payload.get("action", "")
                        pr_data = payload.get("pull_request", {})
                        metadata["merged"] = pr_data.get("merged", False)
                        metadata["title"] = pr_data.get("title", "")
                    
                    activity_events.append(
                        ActivityEvent(
                            type=event_type,
                            created_at=created_at,
                            metadata=metadata,
                        )
                    )
                
                except (KeyError, ValueError, TypeError) as e:
                    logger.debug(f"Error parsing event for '{username}': {e}")
                    continue
            
            logger.debug(
                f"Fetched {len(activity_events)} relevant activity events for '{username}' "
                f"(filtered from {len(events_data)} total events)"
            )
            
            return activity_events
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching activity for '{username}': {e.response.status_code}"
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error fetching activity for '{username}': {e}")
            raise
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing activity data for '{username}': {e}")
            raise ValueError(f"Failed to parse activity data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching activity for '{username}': {e}")
            raise
