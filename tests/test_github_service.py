"""
Tests for the GitHubService class, including error handling and retry logic.
"""

import pytest
import pytest_asyncio
import httpx
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from services.github_service import GitHubService
from services.github_exceptions import (
    GitHubUserNotFoundError,
    GitHubRateLimitError,
    GitHubTimeoutError,
    GitHubNetworkError,
    GitHubAPIError,
)
from models.github_models import ContributionData, ContributionDay, ActivityEvent
from config.settings import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        github_token="test_token_123",
        github_graphql_url="https://api.github.com/graphql",
        github_rest_url="https://api.github.com",
        database_url="sqlite:///:memory:",
    )


@pytest_asyncio.fixture
async def github_service(settings):
    """Create a GitHubService instance for testing."""
    service = GitHubService(settings)
    yield service
    await service.close()


class TestValidateUserExists:
    """Tests for validate_user_exists method."""
    
    @pytest.mark.asyncio
    async def test_validate_user_exists_success(self, github_service):
        """Test successful user validation."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_client.get.return_value = mock_response
        
        github_service.http_client = mock_client
        
        result = await github_service.validate_user_exists("octocat")
        
        assert result is True
        mock_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_user_not_found(self, github_service):
        """Test user not found error."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_client.get.return_value = mock_response
        
        github_service.http_client = mock_client
        
        with pytest.raises(GitHubUserNotFoundError):
            await github_service.validate_user_exists("nonexistent")
    
    @pytest.mark.asyncio
    async def test_validate_user_rate_limit(self, github_service):
        """Test rate limit error during user validation."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {"X-RateLimit-Remaining": "0"}
        mock_client.get.return_value = mock_response
        
        github_service.http_client = mock_client
        
        with pytest.raises(GitHubRateLimitError):
            await github_service.validate_user_exists("octocat")

    @pytest.mark.asyncio
    async def test_validate_user_forbidden_is_not_rate_limit(self, github_service):
        """Test a non-rate-limit 403 is surfaced as a GitHub API error."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {"X-RateLimit-Remaining": "100"}
        mock_response.json.return_value = {
            "message": "Resource not accessible by integration"
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 Forbidden",
            request=MagicMock(),
            response=mock_response
        )
        mock_client.get.return_value = mock_response

        github_service.http_client = mock_client

        with pytest.raises(GitHubAPIError) as exc_info:
            await github_service.validate_user_exists("octocat")

        assert exc_info.value.status_code == 403
        assert "Resource not accessible" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_validate_user_timeout(self, github_service):
        """Test timeout error during user validation."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Request timed out")
        
        github_service.http_client = mock_client
        
        with pytest.raises(GitHubTimeoutError):
            await github_service.validate_user_exists("octocat")
    
    @pytest.mark.asyncio
    async def test_validate_user_network_error(self, github_service):
        """Test network error during user validation."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection failed")
        
        github_service.http_client = mock_client
        
        with pytest.raises(GitHubNetworkError):
            await github_service.validate_user_exists("octocat")
    
    @pytest.mark.asyncio
    async def test_validate_user_empty_username(self, github_service):
        """Test validation with empty username."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            await github_service.validate_user_exists("")
    
    @pytest.mark.asyncio
    async def test_validate_user_retry_on_transient_error(self, github_service):
        """Test retry logic on transient errors (5xx)."""
        mock_client = AsyncMock()
        
        # First call returns 503, second call returns 200
        mock_response_503 = MagicMock()
        mock_response_503.status_code = 503
        mock_response_503.headers = {}
        mock_response_503.raise_for_status.side_effect = httpx.HTTPStatusError(
            "503 Server Error",
            request=MagicMock(),
            response=mock_response_503
        )
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.headers = {}
        
        mock_client.get.side_effect = [mock_response_503, mock_response_200]
        
        github_service.http_client = mock_client
        
        result = await github_service.validate_user_exists("octocat")
        
        assert result is True
        assert mock_client.get.call_count == 2


class TestGetContributionData:
    """Tests for get_contribution_data method."""
    
    @pytest.mark.asyncio
    async def test_get_contribution_data_success(self, github_service):
        """Test successful contribution data fetching."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {
            "data": {
                "user": {
                    "contributionsCollection": {
                        "commitContributionsByRepository": [
                            {
                                "contributions": {
                                    "nodes": [
                                        {
                                            "occurredAt": "2024-01-01T12:00:00Z",
                                            "commitCount": 2
                                        },
                                        {
                                            "occurredAt": "2024-01-01T18:00:00Z",
                                            "commitCount": 3
                                        },
                                        {
                                            "occurredAt": "2024-01-02T09:00:00Z",
                                            "commitCount": 4
                                        }
                                    ]
                                }
                            }
                        ],
                        "contributionCalendar": {
                            "totalContributions": 42,
                            "weeks": [
                                {
                                    "contributionDays": [
                                        {
                                            "date": "2024-01-01",
                                            "contributionCount": 5
                                        },
                                        {
                                            "date": "2024-01-02",
                                            "contributionCount": 3
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
        }
        mock_client.post.return_value = mock_response
        
        github_service.http_client = mock_client
        
        result = await github_service.get_contribution_data("octocat", days=7)
        
        assert result.username == "octocat"
        assert result.total_commits == 42
        assert len(result.contribution_days) == 2
        assert result.contribution_days[0].count == 5
        assert len(result.commit_days) == 2
        assert result.commit_days[0].count == 5
        assert result.commit_days[1].count == 4
    
    @pytest.mark.asyncio
    async def test_get_contribution_data_user_not_found(self, github_service):
        """Test user not found in GraphQL response."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {
            "errors": [
                {"message": "Could not resolve to a User with the login of 'nonexistent'."}
            ]
        }
        mock_client.post.return_value = mock_response
        
        github_service.http_client = mock_client
        
        with pytest.raises(GitHubUserNotFoundError):
            await github_service.get_contribution_data("nonexistent")
    
    @pytest.mark.asyncio
    async def test_get_contribution_data_rate_limit(self, github_service):
        """Test rate limit error during contribution data fetch."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "0"}
        mock_client.post.return_value = mock_response
        
        github_service.http_client = mock_client
        
        with pytest.raises(GitHubRateLimitError):
            await github_service.get_contribution_data("octocat")
    
    @pytest.mark.asyncio
    async def test_get_contribution_data_timeout(self, github_service):
        """Test timeout error during contribution data fetch."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("Request timed out")
        
        github_service.http_client = mock_client
        
        with pytest.raises(GitHubTimeoutError):
            await github_service.get_contribution_data("octocat")
    
    @pytest.mark.asyncio
    async def test_get_contribution_data_empty_username(self, github_service):
        """Test with empty username."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            await github_service.get_contribution_data("")
    
    @pytest.mark.asyncio
    async def test_get_contribution_data_retry_on_transient_error(self, github_service):
        """Test retry logic on transient errors."""
        mock_client = AsyncMock()
        
        # First call times out, second call succeeds
        mock_client.post.side_effect = [
            httpx.TimeoutException("Timeout"),
            MagicMock(
                status_code=200,
                headers={},
                json=lambda: {
                    "data": {
                        "user": {
                            "contributionsCollection": {
                                "commitContributionsByRepository": [],
                                "contributionCalendar": {
                                    "totalContributions": 10,
                                    "weeks": []
                                }
                            }
                        }
                    }
                }
            )
        ]
        
        github_service.http_client = mock_client
        
        result = await github_service.get_contribution_data("octocat")
        
        assert result.total_commits == 10
        assert mock_client.post.call_count == 2


class TestGetRecentActivity:
    """Tests for get_recent_activity method."""
    
    @pytest.mark.asyncio
    async def test_get_recent_activity_success(self, github_service):
        """Test successful activity event fetching."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = [
            {
                "type": "PullRequestEvent",
                "created_at": "2024-01-15T09:00:00Z",
                "payload": {
                    "action": "closed",
                    "pull_request": {
                        "merged": True,
                        "title": "Fix bug"
                    }
                }
            }
        ]
        mock_client.get.return_value = mock_response
        
        github_service.http_client = mock_client
        
        result = await github_service.get_recent_activity("octocat", limit=30)
        
        assert len(result) == 1
        assert result[0].type == "PullRequestEvent"
        assert result[0].metadata["merged"] is True
    
    @pytest.mark.asyncio
    async def test_get_recent_activity_rate_limit(self, github_service):
        """Test rate limit error during activity fetch."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "0"}
        mock_client.get.return_value = mock_response
        
        github_service.http_client = mock_client
        
        with pytest.raises(GitHubRateLimitError):
            await github_service.get_recent_activity("octocat")
    
    @pytest.mark.asyncio
    async def test_get_recent_activity_timeout(self, github_service):
        """Test timeout error during activity fetch."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Request timed out")
        
        github_service.http_client = mock_client
        
        with pytest.raises(GitHubTimeoutError):
            await github_service.get_recent_activity("octocat")
    
    @pytest.mark.asyncio
    async def test_get_recent_activity_network_error(self, github_service):
        """Test network error during activity fetch."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection failed")
        
        github_service.http_client = mock_client
        
        with pytest.raises(GitHubNetworkError):
            await github_service.get_recent_activity("octocat")
    
    @pytest.mark.asyncio
    async def test_get_recent_activity_empty_username(self, github_service):
        """Test with empty username."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            await github_service.get_recent_activity("")
    
    @pytest.mark.asyncio
    async def test_get_recent_activity_filters_event_types(self, github_service):
        """Test that only relevant event types are returned."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = [
            {
                "type": "PushEvent",  # Should be filtered out
                "created_at": "2024-01-15T10:30:00Z",
                "payload": {"size": 1, "ref": "main"}
            },
            {
                "type": "IssuesEvent",  # Should be filtered out
                "created_at": "2024-01-15T09:00:00Z",
                "payload": {}
            },
            {
                "type": "PullRequestEvent",
                "created_at": "2024-01-15T08:00:00Z",
                "payload": {
                    "action": "opened",
                    "pull_request": {"merged": False, "title": "New feature"}
                }
            }
        ]
        mock_client.get.return_value = mock_response
        
        github_service.http_client = mock_client
        
        result = await github_service.get_recent_activity("octocat")
        
        # Should only have the PullRequestEvent
        assert len(result) == 1
        assert result[0].type == "PullRequestEvent"
    
    @pytest.mark.asyncio
    async def test_get_recent_activity_retry_on_transient_error(self, github_service):
        """Test retry logic on transient errors."""
        mock_client = AsyncMock()
        
        # First call returns 502, second call succeeds
        mock_response_502 = MagicMock()
        mock_response_502.status_code = 502
        mock_response_502.headers = {}
        mock_response_502.raise_for_status.side_effect = httpx.HTTPStatusError(
            "502 Bad Gateway",
            request=MagicMock(),
            response=mock_response_502
        )
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.headers = {}
        mock_response_200.json.return_value = []
        
        mock_client.get.side_effect = [mock_response_502, mock_response_200]
        
        github_service.http_client = mock_client
        
        result = await github_service.get_recent_activity("octocat")
        
        assert result == []
        assert mock_client.get.call_count == 2


class TestErrorHandlingHelpers:
    """Tests for error handling helper methods."""
    
    @pytest.mark.asyncio
    async def test_handle_rate_limit_response(self, github_service):
        """Test rate limit detection in response headers."""
        mock_response = MagicMock()
        mock_response.headers = {"X-RateLimit-Remaining": "0"}
        
        with pytest.raises(GitHubRateLimitError):
            github_service._handle_rate_limit_response(mock_response)
    
    @pytest.mark.asyncio
    async def test_extract_graphql_errors(self, github_service):
        """Test GraphQL error extraction."""
        data = {
            "errors": [
                {"message": "Error 1"},
                {"message": "Error 2"}
            ]
        }
        
        error_msg = github_service._extract_graphql_errors(data)
        
        assert error_msg == "Error 1, Error 2"
    
    @pytest.mark.asyncio
    async def test_extract_graphql_errors_no_errors(self, github_service):
        """Test GraphQL error extraction with no errors."""
        data = {"data": {"user": {}}}
        
        error_msg = github_service._extract_graphql_errors(data)
        
        assert error_msg is None
