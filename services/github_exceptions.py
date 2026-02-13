"""
Custom exceptions for GitHub API interactions.

These exceptions are raised when specific error conditions occur during
GitHub API calls, allowing for targeted error handling in the service layer.
"""


class GitHubServiceError(Exception):
    """Base exception for GitHub service errors."""
    pass


class GitHubUserNotFoundError(GitHubServiceError):
    """Raised when a GitHub user is not found (404)."""
    
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"GitHub user '{username}' not found")


class GitHubRateLimitError(GitHubServiceError):
    """Raised when GitHub API rate limit is exceeded (403 with rate limit message)."""
    
    def __init__(self, reset_time: int = None):
        self.reset_time = reset_time
        message = "GitHub API rate limit exceeded"
        if reset_time:
            message += f", resets at {reset_time}"
        super().__init__(message)


class GitHubTimeoutError(GitHubServiceError):
    """Raised when GitHub API request times out."""
    
    def __init__(self, endpoint: str = None):
        self.endpoint = endpoint
        message = "GitHub API request timed out"
        if endpoint:
            message += f" ({endpoint})"
        super().__init__(message)


class GitHubAPIError(GitHubServiceError):
    """Raised for general GitHub API errors."""
    
    def __init__(self, status_code: int = None, message: str = None):
        self.status_code = status_code
        self.message = message
        error_msg = "GitHub API error"
        if status_code:
            error_msg += f" (status {status_code})"
        if message:
            error_msg += f": {message}"
        super().__init__(error_msg)


class GitHubNetworkError(GitHubServiceError):
    """Raised for network-related errors when communicating with GitHub."""
    
    def __init__(self, message: str = None):
        self.message = message
        error_msg = "Network error communicating with GitHub API"
        if message:
            error_msg += f": {message}"
        super().__init__(error_msg)
