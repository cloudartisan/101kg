"""
Logging module for 101kg downloader.

Provides standardized logging functionality across the application.
"""
import logging
import os
import sys
from datetime import datetime

# Log levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# Global logger instance
_logger = None


def setup_logger(level=logging.INFO, log_to_file=True, console_level=None):
    """
    Set up the logger with the specified configuration.

    Args:
        level (int): The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file (bool): Whether to log to a file in addition to console
        console_level (int, optional): Separate logging level for console output.
                                      If None, uses the same level as specified in 'level'.

    Returns:
        logging.Logger: Configured logger instance
    """
    global _logger

    if _logger is not None:
        return _logger

    # Create logger
    _logger = logging.getLogger("101kg")
    _logger.setLevel(level)
    _logger.handlers = []  # Clear any existing handlers

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level if console_level is not None else level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    # Add console handler to logger
    _logger.addHandler(console_handler)

    # Add file handler if requested
    if log_to_file:
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/101kg_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)

    return _logger


def get_logger():
    """
    Get the configured logger instance.
    
    If the logger hasn't been set up yet, it will be initialized with default settings.

    Returns:
        logging.Logger: Logger instance
    """
    global _logger
    if _logger is None:
        setup_logger()
    return _logger


# Convenience functions
def debug(msg, *args, **kwargs):
    """Log a debug message."""
    get_logger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """Log an info message."""
    get_logger().info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """Log a warning message."""
    get_logger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """Log an error message."""
    get_logger().error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """Log a critical message."""
    get_logger().critical(msg, *args, **kwargs)