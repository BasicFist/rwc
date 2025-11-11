"""
Logging configuration for RWC
Provides centralized logging setup with proper formatters and handlers
"""
import logging
import sys
from pathlib import Path
from typing import Optional
import os


# Log levels
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}


def setup_logging(
    name: str = 'rwc',
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Setup logging configuration for RWC.

    Args:
        name: Logger name (default: 'rwc')
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        console: Whether to log to console (default: True)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging('rwc.api', level='INFO')
        >>> logger.info("API server started")
    """
    # Get level from environment or parameter
    if level is None:
        level = os.getenv('RWC_LOG_LEVEL', 'INFO').upper()

    log_level = LOG_LEVELS.get(level, logging.INFO)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance. If not configured, sets up with defaults.

    Args:
        name: Logger name

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger('rwc.core')
        >>> logger.debug("Model loaded successfully")
    """
    logger = logging.getLogger(name)

    # If logger has no handlers, set it up
    if not logger.handlers:
        setup_logging(name)

    return logger


# Create default logger for the package
default_logger = setup_logging('rwc')


# Convenience functions for common logging patterns
def log_function_call(logger: logging.Logger, func_name: str, **kwargs) -> None:
    """
    Log a function call with parameters.

    Args:
        logger: Logger instance
        func_name: Function name
        **kwargs: Function parameters to log
    """
    params = ', '.join(f'{k}={v}' for k, v in kwargs.items())
    logger.debug(f"Called {func_name}({params})")


def log_performance(logger: logging.Logger, operation: str, duration: float) -> None:
    """
    Log performance metrics.

    Args:
        logger: Logger instance
        operation: Operation description
        duration: Duration in seconds
    """
    logger.info(f"Performance: {operation} completed in {duration:.2f}s")


def log_error_with_context(logger: logging.Logger, error: Exception, context: str) -> None:
    """
    Log an error with additional context.

    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context string
    """
    logger.error(f"{context}: {type(error).__name__}: {str(error)}", exc_info=True)
