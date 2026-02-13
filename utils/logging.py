"""
Logging configuration for GitHub Tamagotchi service.

This module provides centralized logging setup with structured logging,
sensitive data filtering, and configurable log levels. It ensures that
no sensitive information (like GitHub tokens) is exposed in logs.
"""

import logging
import logging.handlers
import sys
from typing import Optional
from pathlib import Path


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter that redacts sensitive data from log records.
    
    This filter prevents sensitive information like GitHub tokens,
    database URLs with passwords, and other credentials from being
    exposed in logs.
    """
    
    # Patterns to redact (case-insensitive)
    SENSITIVE_PATTERNS = [
        "github_token",
        "ghp_",
        "ghu_",
        "ghs_",
        "ghr_",
        "password",
        "token",
        "secret",
        "api_key",
        "authorization",
        "bearer",
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to redact sensitive data.
        
        Args:
            record: The log record to filter
            
        Returns:
            True to allow the record to be logged
        """
        # Redact message
        record.msg = self._redact_message(str(record.msg))
        
        # Redact arguments if present
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._redact_value(v) for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._redact_value(arg) for arg in record.args
                )
        
        # Redact exception info if present
        if record.exc_info:
            record.exc_text = self._redact_message(
                record.exc_text or ""
            )
        
        return True
    
    @staticmethod
    def _redact_message(message: str) -> str:
        """
        Redact sensitive patterns from a message string.
        
        Args:
            message: The message to redact
            
        Returns:
            The message with sensitive data redacted
        """
        import re
        
        # Redact GitHub tokens (ghp_, ghu_, ghs_, ghr_ prefixes)
        message = re.sub(
            r'(ghp_|ghu_|ghs_|ghr_)[a-zA-Z0-9_]+',
            r'\1***REDACTED***',
            message,
            flags=re.IGNORECASE
        )
        
        # Redact common credential patterns
        message = re.sub(
            r'(password|token|secret|api_key|authorization|bearer)\s*[:=]\s*[^\s,}]+',
            r'\1=***REDACTED***',
            message,
            flags=re.IGNORECASE
        )
        
        # Redact database URLs with passwords
        message = re.sub(
            r'(postgresql|mysql|sqlite)://[^:]+:[^@]+@',
            r'\1://***:***@',
            message,
            flags=re.IGNORECASE
        )
        
        return message
    
    @staticmethod
    def _redact_value(value) -> str:
        """
        Redact sensitive values.
        
        Args:
            value: The value to potentially redact
            
        Returns:
            The redacted value or original if not sensitive
        """
        if not isinstance(value, str):
            return value
        
        # Check if value looks like a token or credential
        if any(pattern in value.lower() for pattern in SensitiveDataFilter.SENSITIVE_PATTERNS):
            return "***REDACTED***"
        
        # Check if value is a GitHub token
        if value.startswith(("ghp_", "ghu_", "ghs_", "ghr_")):
            return "***REDACTED***"
        
        return value


class StructuredFormatter(logging.Formatter):
    """
    Structured logging formatter that provides consistent, readable output.
    
    Formats log records with timestamp, level, logger name, and message
    in a consistent format suitable for both console and file output.
    """
    
    # ANSI color codes for console output
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
        "RESET": "\033[0m",       # Reset
    }
    
    def __init__(self, use_color: bool = False):
        """
        Initialize the formatter.
        
        Args:
            use_color: Whether to use ANSI color codes in output
        """
        self.use_color = use_color
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record.
        
        Args:
            record: The log record to format
            
        Returns:
            The formatted log message
        """
        # Build the base format
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        level = record.levelname
        logger_name = record.name
        message = record.getMessage()
        
        # Add color if enabled and not a file handler
        if self.use_color:
            color = self.COLORS.get(level, "")
            reset = self.COLORS["RESET"]
            level = f"{color}{level}{reset}"
        
        # Format the log line
        log_line = f"{timestamp} - {level:8} - {logger_name:30} - {message}"
        
        # Add exception info if present
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)
        
        return log_line


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    use_console: bool = True,
    use_color: bool = True,
) -> None:
    """
    Configure logging for the application.
    
    Sets up logging with the specified level, optionally writing to a file,
    and applies the SensitiveDataFilter to prevent credential leakage.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to a log file. If provided, logs will be written to this file
        use_console: Whether to log to console (default: True)
        use_color: Whether to use ANSI colors in console output (default: True)
        
    Example:
        from utils.logging import setup_logging
        
        setup_logging(log_level="DEBUG", log_file="app.log")
    """
    # Validate log level
    log_level_upper = log_level.upper()
    if log_level_upper not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError(
            f"Invalid log level: {log_level}. "
            "Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
        )
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level_upper))
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create sensitive data filter
    sensitive_filter = SensitiveDataFilter()
    
    # Console handler
    if use_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level_upper))
        console_handler.setFormatter(
            StructuredFormatter(use_color=use_color)
        )
        console_handler.addFilter(sensitive_filter)
        root_logger.addHandler(console_handler)
    
    # File handler (if log_file is specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,  # Keep 5 backup files
        )
        file_handler.setLevel(getattr(logging, log_level_upper))
        file_handler.setFormatter(
            StructuredFormatter(use_color=False)  # No colors in file
        )
        file_handler.addFilter(sensitive_filter)
        root_logger.addHandler(file_handler)
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.debug(f"Logging configured: level={log_level_upper}, file={log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    This is a convenience function that returns a logger with the given name.
    The logger will automatically inherit the root logger's configuration
    and filters.
    
    Args:
        name: The name of the logger (typically __name__)
        
    Returns:
        A logger instance
        
    Example:
        from utils.logging import get_logger
        
        logger = get_logger(__name__)
        logger.info("Application started")
    """
    return logging.getLogger(name)
