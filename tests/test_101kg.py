"""
Tests for the main 101kg.py module using mock objects.
"""
import pytest
import sys
import importlib
from unittest.mock import patch, MagicMock, call

# Import the main module using importlib to avoid SyntaxError with numeric module name
kg_module = importlib.import_module('101kg')

# Get main function reference
main_func = kg_module.main


def test_main_successful_execution(monkeypatch):
    """Test successful execution of the main function."""
    # Setup mocks
    mock_setup_logger = MagicMock()
    mock_logger = MagicMock()
    mock_downloader_class = MagicMock()
    mock_downloader = MagicMock()
    
    # Configure mocks
    mock_downloader.login.return_value = True
    mock_downloader_class.return_value = mock_downloader
    
    # Monkeypatch
    monkeypatch.setattr(kg_module.logger, 'setup_logger', mock_setup_logger)
    monkeypatch.setattr(kg_module.logger, 'get_logger', lambda: mock_logger)
    monkeypatch.setattr(kg_module, 'VideoDownloader', mock_downloader_class)
    
    # Mock command line arguments
    monkeypatch.setattr(sys, 'argv', ['101kg.py', '--email', 'test@example.com', '--password', 'password123'])
    
    # Call the function
    result = main_func()
    
    # Check the results
    assert result == 0  # Success exit code
    mock_setup_logger.assert_called()
    mock_downloader_class.assert_called_once_with('test@example.com', 'password123', headless=False, browser_type='chrome', browser_profile=None)
    mock_downloader.login.assert_called_once()
    mock_downloader.download_all_lessons.assert_called_once()
    mock_downloader.close.assert_called_once()


def test_main_login_failure(monkeypatch):
    """Test main function when login fails."""
    # Setup mocks
    mock_setup_logger = MagicMock()
    mock_logger = MagicMock()
    mock_downloader_class = MagicMock()
    mock_downloader = MagicMock()
    
    # Configure mocks
    mock_downloader.login.return_value = False  # Login fails
    mock_downloader_class.return_value = mock_downloader
    
    # Monkeypatch
    monkeypatch.setattr(kg_module.logger, 'setup_logger', mock_setup_logger)
    monkeypatch.setattr(kg_module.logger, 'get_logger', lambda: mock_logger)
    monkeypatch.setattr(kg_module, 'VideoDownloader', mock_downloader_class)
    
    # Mock command line arguments
    monkeypatch.setattr(sys, 'argv', ['101kg.py', '--email', 'test@example.com', '--password', 'wrong_password'])
    
    # Call the function
    result = main_func()
    
    # Check the results
    assert result == 1  # Error exit code
    mock_setup_logger.assert_called()
    mock_downloader_class.assert_called_once_with('test@example.com', 'wrong_password', headless=False, browser_type='chrome', browser_profile=None)
    mock_downloader.login.assert_called_once()
    mock_downloader.download_all_lessons.assert_not_called()  # Should not be called on login failure
    mock_downloader.close.assert_called_once()  # Should still be called for cleanup


def test_main_with_verbose_and_headless(monkeypatch):
    """Test main function with verbose and headless options."""
    # Setup mocks
    mock_setup_logger = MagicMock()
    mock_logger = MagicMock()
    mock_downloader_class = MagicMock()
    mock_downloader = MagicMock()
    
    # Configure mocks
    mock_downloader.login.return_value = True
    mock_downloader_class.return_value = mock_downloader
    
    # Monkeypatch
    monkeypatch.setattr(kg_module.logger, 'setup_logger', mock_setup_logger)
    monkeypatch.setattr(kg_module.logger, 'get_logger', lambda: mock_logger)
    monkeypatch.setattr(kg_module, 'VideoDownloader', mock_downloader_class)
    
    # Mock command line arguments
    monkeypatch.setattr(sys, 'argv', [
        '101kg.py',
        '--email', 'test@example.com',
        '--password', 'password123',
        '--verbose',
        '--headless'
    ])
    
    # Call the function
    result = main_func()
    
    # Check the results
    assert result == 0  # Success exit code
    mock_downloader_class.assert_called_once_with('test@example.com', 'password123', headless=True, browser_type='chrome', browser_profile=None)
    mock_downloader.login.assert_called_once()
    mock_downloader.download_all_lessons.assert_called_once()
    mock_downloader.close.assert_called_once()
    
    # Check if verbose mode was correctly passed to logger setup
    setup_calls = mock_setup_logger.call_args_list
    assert len(setup_calls) > 0
    # Verify a call with matching log level and console level exists (verbose mode)
    matching_call = False
    for call_args in setup_calls:
        kwargs = call_args[1]
        if 'console_level' in kwargs and kwargs.get('level') == kwargs.get('console_level'):
            matching_call = True
            break
    assert matching_call, "No logger setup call found with matching log level and console level"