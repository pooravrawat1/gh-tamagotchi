"""
GitHub API service for fetching user data and activity.

This module provides async methods to interact with GitHub's GraphQL and REST APIs,
including user validation, contribution data fetching, and activity event retrieval.
Includes comprehensive error handling and retry logic for transient failures.
"""

import logging
import asyncio
from typing import Optional, List, Callable, TypeVar, Any
from datetime import datetime, timedelta, date
import httpx

from models.github_models import ContributionData, ContributionDay, ActivityEvent
from config.settings import Settings
from services.github_exceptions import (
    GitHubServiceError,
    GitHubUserNotFoundError,
    GitHubRateLimitError,
    GitHubTimeoutError,
    GitHubAPIError,
    GitHubNetworkError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class GitHubService:
    """
    Service for interacting with GitHub APIs.
    
    Handles authentication, user validation, and data fetching from both
    GraphQL and REST endpoints. Includes comprehensive error handling and
    retry logic for transient failures.
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    RETRY_BACKOFF = 2.0  # exponential backoff multiplier
    TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}  # Codes to retry on
    
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
    
    async def _retry_with_backoff(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with exponential backoff retry logic.
        
        Retries on transient failures (timeouts, rate limits, 5xx errors).
        Does not retry on permanent failures (4xx errors except 429).
        
        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            GitHubServiceError: If all retries are exhausted or permanent error occurs
        """
        last_exception = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            
            except httpx.TimeoutException as e:
                last_exception = GitHubTimeoutError()
                logger.warning(
                    f"Timeout on attempt {attempt + 1}/{self.MAX_RETRIES}: {e}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** attempt)
                    await asyncio.sleep(delay)
                    continue
                raise last_exception
            
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                
                # Handle rate limit (403 with rate limit message)
                if status_code == 403:
                    rate_limit_reset = e.response.headers.get("X-RateLimit-Reset")
                    logger.error(f"GitHub API rate limit exceeded")
                    raise GitHubRateLimitError(reset_time=rate_limit_reset)
                
                # Handle user not found
                if status_code == 404:
                    logger.debug(f"GitHub resource not found (404)")
                    raise GitHubUserNotFoundError(username="unknown")
                
                # Retry on transient errors (5xx, 429, 408, 500, 502, 503, 504)
                if status_code in self.TRANSIENT_STATUS_CODES:
                    last_exception = GitHubAPIError(status_code=status_code)
                    logger.warning(
                        f"Transient error {status_code} on attempt {attempt + 1}/{self.MAX_RETRIES}"
                    )
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** attempt)
                        await asyncio.sleep(delay)
                        continue
                    raise last_exception
                
                # Don't retry on other 4xx errors
                logger.error(f"GitHub API error {status_code}")
                raise GitHubAPIError(status_code=status_code)
            
            except httpx.RequestError as e:
                # Network errors are transient, retry them
                last_exception = GitHubNetworkError(message=str(e))
                logger.warning(
                    f"Network error on attempt {attempt + 1}/{self.MAX_RETRIES}: {e}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** attempt)
                    await asyncio.sleep(delay)
                    continue
                raise last_exception
        
        # Should not reach here, but raise last exception if we do
        if last_exception:
            raise last_exception
        raise GitHubServiceError("Unknown error in retry logic")
    
    def _handle_rate_limit_response(self, response: httpx.Response) -> None:
        """
        Check response headers for rate limit information and raise if exceeded.
        
        Args:
            response: HTTP response object
            
        Raises:
            GitHubRateLimitError: If rate limit is exceeded
        """
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_time = response.headers.get("X-RateLimit-Reset")
        
        if remaining is not None and int(remaining) == 0:
            logger.error("GitHub API rate limit exhausted")
            raise GitHubRateLimitError(reset_time=reset_time)
    
    def _extract_graphql_errors(self, data: dict) -> Optional[str]:
        """
        Extract error messages from GraphQL response.
        
        Args:
            data: GraphQL response data
            
        Returns:
            Error message string or None if no errors
        """
        if "errors" in data:
            errors = data.get("errors", [])
            if isinstance(errors, list) and errors:
                error_messages = []
                for error in errors:
                    if isinstance(error, dict):
                        msg = error.get("message", "Unknown error")
                        error_messages.append(msg)
                    else:
                        error_messages.append(str(error))
                return ", ".join(error_messages)
        return None
    

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
            GitHubUserNotFoundError: If user is not found
            GitHubRateLimitError: If rate limit is exceeded
            GitHubTimeoutError: If request times out
            GitHubNetworkError: If network error occurs
            GitHubServiceError: For other GitHub API errors
        """
        if not username or not username.strip():
            logger.warning("Empty username provided to validate_user_exists")
            raise ValueError("Username cannot be empty")
        
        username = username.strip()
        
        async def _validate() -> bool:
            client = await self._get_client()
            url = f"{self.rest_url}/users/{username}"
            
            response = await client.get(url, headers=self.headers)
            
            # Check for rate limit before processing
            self._handle_rate_limit_response(response)
            
            if response.status_code == 200:
                logger.debug(f"GitHub user '{username}' exists")
                return True
            elif response.status_code == 404:
                logger.debug(f"GitHub user '{username}' not found")
                raise GitHubUserNotFoundError(username=username)
            else:
                # Unexpected status code
                logger.warning(
                    f"Unexpected status code {response.status_code} "
                    f"when validating user '{username}'"
                )
                response.raise_for_status()
                return False
        
        try:
            return await self._retry_with_backoff(_validate)
        except GitHubServiceError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error validating GitHub user '{username}': {e}")
            raise GitHubServiceError(f"Failed to validate user: {e}")
    
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
            GitHubUserNotFoundError: If user is not found
            GitHubRateLimitError: If rate limit is exceeded
            GitHubTimeoutError: If request times out
            GitHubNetworkError: If network error occurs
            GitHubServiceError: For other GitHub API errors or parsing errors
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
        
        async def _fetch_contributions() -> ContributionData:
            client = await self._get_client()
            
            response = await client.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers=self.graphql_headers,
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Check for rate limit before processing
            self._handle_rate_limit_response(response)
            
            # Check for GraphQL errors
            graphql_error = self._extract_graphql_errors(data)
            if graphql_error:
                logger.error(f"GraphQL error fetching contributions for '{username}': {graphql_error}")
                # Check if it's a user not found error
                if "Could not resolve to a User" in graphql_error or "not found" in graphql_error.lower():
                    raise GitHubUserNotFoundError(username=username)
                raise GitHubAPIError(message=graphql_error)
            
            # Parse the response
            user_data = data.get("data", {}).get("user")
            if not user_data:
                logger.warning(f"No user data returned for '{username}'")
                raise GitHubUserNotFoundError(username=username)
            
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
        
        try:
            return await self._retry_with_backoff(_fetch_contributions)
        except GitHubServiceError:
            raise
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing contribution data for '{username}': {e}")
            raise GitHubServiceError(f"Failed to parse contribution data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching contributions for '{username}': {e}")
            raise GitHubServiceError(f"Failed to fetch contributions: {e}")
    
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
            GitHubUserNotFoundError: If user is not found
            GitHubRateLimitError: If rate limit is exceeded
            GitHubTimeoutError: If request times out
            GitHubNetworkError: If network error occurs
            GitHubServiceError: For other GitHub API errors or parsing errors
        """
        if not username or not username.strip():
            logger.warning("Empty username provided to get_recent_activity")
            raise ValueError("Username cannot be empty")
        
        username = username.strip()
        
        # Relevant event types for pet activity
        relevant_event_types = {"PushEvent", "PullRequestEvent"}
        
        async def _fetch_activity() -> List[ActivityEvent]:
            client = await self._get_client()
            url = f"{self.rest_url}/users/{username}/events"
            
            # Fetch events with pagination
            params = {"per_page": min(limit, 100)}  # GitHub API max is 100 per page
            
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            # Check for rate limit before processing
            self._handle_rate_limit_response(response)
            
            events_data = response.json()
            
            if not isinstance(events_data, list):
                logger.warning(f"Unexpected response format for events from '{username}'")
                raise GitHubAPIError(message="Expected list of events from GitHub API")
            
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
        
        try:
            return await self._retry_with_backoff(_fetch_activity)
        except GitHubServiceError:
            raise
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing activity data for '{username}': {e}")
            raise GitHubServiceError(f"Failed to parse activity data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching activity for '{username}': {e}")
            raise GitHubServiceError(f"Failed to fetch activity: {e}")
