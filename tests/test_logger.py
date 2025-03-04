"""
Tests for the logger module.
"""
import logging
import os
import pytest
from unittest.mock import patch, MagicMock
import logger


@pytest.fixture
def cleanup_logger():
    """Fixture to reset the logger between tests."""
    yield
    # Reset the global _logger variable
    logger._logger = None
    # Remove any handlers from the root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)


class TestLoggerSetup:
    """Tests for logger setup functionality."""

    def test_setup_logger_defaults(self, cleanup_logger):
        """Test setup_logger with default parameters."""
        log = logger.setup_logger()
        assert log.level == logging.INFO
        assert len(log.handlers) == 2  # 1 console handler, 1 file handler
        assert isinstance(log.handlers[0], logging.StreamHandler)
        assert isinstance(log.handlers[1], logging.FileHandler)

    def test_setup_logger_custom_level(self, cleanup_logger):
        """Test setup_logger with custom log level."""
        log = logger.setup_logger(level=logging.DEBUG)
        assert log.level == logging.DEBUG
        # Console handler should inherit logger level by default when console_level is None
        assert log.handlers[0].level == logging.DEBUG  
        # File handler should have DEBUG level
        assert log.handlers[1].level == logging.DEBUG

    def test_setup_logger_console_level(self, cleanup_logger):
        """Test setup_logger with custom console_level."""
        log = logger.setup_logger(level=logging.INFO, console_level=logging.DEBUG)
        assert log.level == logging.INFO
        assert log.handlers[0].level == logging.DEBUG
        assert log.handlers[1].level == logging.INFO

    def test_setup_logger_no_file(self, cleanup_logger):
        """Test setup_logger with log_to_file=False."""
        log = logger.setup_logger(log_to_file=False)
        assert len(log.handlers) == 1
        assert isinstance(log.handlers[0], logging.StreamHandler)

    def test_get_logger_creates_logger(self, cleanup_logger):
        """Test get_logger creates a logger if none exists."""
        # Ensure logger is None
        logger._logger = None
        log = logger.get_logger()
        assert log is not None
        assert log.level == logging.INFO

    def test_get_logger_returns_existing_logger(self, cleanup_logger):
        """Test get_logger returns existing logger if one exists."""
        # Create a logger with a specific level
        original_log = logger.setup_logger(level=logging.DEBUG)
        # Get the logger again
        log = logger.get_logger()
        # Should be the same logger
        assert log is original_log
        assert log.level == logging.DEBUG


class TestLoggingFunctions:
    """Tests for logging convenience functions."""

    @patch('logger.get_logger')
    def test_debug_function(self, mock_get_logger, cleanup_logger):
        """Test debug convenience function."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger.debug("Debug message")
        mock_logger.debug.assert_called_once_with("Debug message")

    @patch('logger.get_logger')
    def test_info_function(self, mock_get_logger, cleanup_logger):
        """Test info convenience function."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger.info("Info message")
        mock_logger.info.assert_called_once_with("Info message")

    @patch('logger.get_logger')
    def test_warning_function(self, mock_get_logger, cleanup_logger):
        """Test warning convenience function."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger.warning("Warning message")
        mock_logger.warning.assert_called_once_with("Warning message")

    @patch('logger.get_logger')
    def test_error_function(self, mock_get_logger, cleanup_logger):
        """Test error convenience function."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger.error("Error message")
        mock_logger.error.assert_called_once_with("Error message")

    @patch('logger.get_logger')
    def test_critical_function(self, mock_get_logger, cleanup_logger):
        """Test critical convenience function."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger.critical("Critical message")
        mock_logger.critical.assert_called_once_with("Critical message")

    @patch('logger.get_logger')
    def test_logging_with_extra_args(self, mock_get_logger, cleanup_logger):
        """Test logging with extra args and kwargs."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger.error("Error message with %s", "substitution", exc_info=True)
        mock_logger.error.assert_called_once_with("Error message with %s", "substitution", exc_info=True)


class TestLogFileCreation:
    """Tests for log file creation."""
    
    def test_log_file_creation(self, cleanup_logger, tmpdir):
        """Test that a log file is created in the logs directory."""
        with patch('logger.os.makedirs') as mock_makedirs:
            with patch('logging.FileHandler') as mock_file_handler:
                logger.setup_logger()
                # Verify that the logs directory is created
                mock_makedirs.assert_called_once_with("logs", exist_ok=True)
                # Verify that a file handler is created
                mock_file_handler.assert_called_once()
                # Extract the log filename from the call arguments
                log_file = mock_file_handler.call_args[0][0]
                assert log_file.startswith("logs/101kg_")
                assert log_file.endswith(".log")