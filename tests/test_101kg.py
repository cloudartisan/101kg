"""
Tests for the main 101kg.py module using mock objects.
"""
import pytest
import sys
import os
import json
import importlib
from unittest.mock import patch, MagicMock, call, mock_open

# Import the main module using importlib to avoid SyntaxError with numeric module name
kg_module = importlib.import_module('101kg')

# Get main function reference
main_func = kg_module.main
load_config_func = kg_module.load_config


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


def test_load_config_existing(monkeypatch):
    """Test loading configuration from an existing file."""
    mock_config = {
        'email': 'test@example.com',
        'password': 'password123'
    }
    mock_file_content = json.dumps(mock_config)
    
    # Mock os.path.exists to return True
    monkeypatch.setattr(os.path, 'exists', lambda _: True)
    # Mock open to return our mock config data
    with patch('builtins.open', mock_open(read_data=mock_file_content)):
        # Mock print function
        with patch('builtins.print') as mock_print:
            # Call the function
            config = load_config_func('/mock/path/config.json')
            
            # Verify the result
            assert config == mock_config
            mock_print.assert_called_with("Loaded configuration from /mock/path/config.json")


def test_load_config_nonexistent(monkeypatch):
    """Test loading configuration when file doesn't exist and we're not interactive."""
    # Mock os.path.exists to return False
    monkeypatch.setattr(os.path, 'exists', lambda _: False)
    # Mock sys.stdin.isatty to return False (non-interactive)
    monkeypatch.setattr(sys.stdin, 'isatty', lambda: False)
    
    # Call the function
    config = load_config_func('/mock/path/config.json')
    
    # Verify the result
    assert config == {}


def test_load_config_interactive_prompting(monkeypatch):
    """Test configuration loading with interactive prompting."""
    # Mock os.path.exists to return False
    monkeypatch.setattr(os.path, 'exists', lambda _: False)
    # Mock sys.stdin.isatty to return True (interactive)
    monkeypatch.setattr(sys.stdin, 'isatty', lambda: True)
    
    # Mock user input
    monkeypatch.setattr('builtins.input', lambda _: 'test@example.com')
    monkeypatch.setattr('101kg.getpass', lambda _: 'password123')
    
    # Mock file operations
    mock_file = mock_open()
    with patch('builtins.open', mock_file):
        # Mock os.chmod to do nothing
        with patch('os.chmod') as mock_chmod:
            # Mock print function
            with patch('builtins.print') as mock_print:
                # Call the function
                config = load_config_func('/mock/path/config.json')
                
                # Verify the result
                assert config == {'email': 'test@example.com', 'password': 'password123'}
                mock_file.assert_called_with('/mock/path/config.json', 'w')
                mock_chmod.assert_called_with('/mock/path/config.json', 0o600)
                
                # Verify that print was called with the right message
                save_message_found = False
                for call_args in mock_print.call_args_list:
                    if "Configuration saved to" in call_args[0][0]:
                        save_message_found = True
                        break
                assert save_message_found


def test_load_config_file_error(monkeypatch):
    """Test load_config with file operation errors."""
    # Mock os.path.exists to return True
    monkeypatch.setattr(os.path, 'exists', lambda _: True)
    
    # Mock open to raise an exception
    with patch('builtins.open', side_effect=Exception("Mock file error")):
        # Mock print function
        with patch('builtins.print') as mock_print:
            # Call the function
            config = load_config_func('/mock/path/config.json')
            
            # Verify error handling
            assert config == {}
            mock_print.assert_called_with("Error loading config: Mock file error")


def test_main_with_direct_url(monkeypatch):
    """Test main function with direct URL download."""
    # Setup mocks
    mock_setup_logger = MagicMock()
    mock_logger = MagicMock()
    mock_downloader_class = MagicMock()
    mock_downloader = MagicMock()
    
    # Configure mocks
    mock_downloader.login.return_value = True
    mock_downloader.download_video.return_value = True
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
        '--url', 'https://example.com/video.mp4',
        '--output', 'test_video'
    ])
    
    # Call the function
    result = main_func()
    
    # Check the results
    assert result == 0  # Success exit code
    mock_downloader.login.assert_called_once()
    mock_downloader.download_video.assert_called_once_with('https://example.com/video.mp4', 'test_video')
    mock_downloader.get_all_lessons.assert_not_called()
    mock_downloader.download_all_lessons.assert_not_called()
    mock_downloader.close.assert_called_once()


def test_main_with_direct_url_failure(monkeypatch):
    """Test main function with failing direct URL download."""
    # Setup mocks
    mock_setup_logger = MagicMock()
    mock_logger = MagicMock()
    mock_downloader_class = MagicMock()
    mock_downloader = MagicMock()
    
    # Configure mocks
    mock_downloader.login.return_value = True
    mock_downloader.download_video.return_value = False  # Download fails
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
        '--url', 'https://example.com/video.mp4'
    ])
    
    # Call the function
    result = main_func()
    
    # Check the results - should still be 0 (success) since we return 0 for direct URL download regardless
    assert result == 0
    mock_downloader.login.assert_called_once()
    mock_downloader.download_video.assert_called_once()
    mock_downloader.close.assert_called_once()


def test_main_list_lessons_only(monkeypatch):
    """Test main function in list-only mode."""
    # Setup mocks
    mock_setup_logger = MagicMock()
    mock_logger = MagicMock()
    mock_downloader_class = MagicMock()
    mock_downloader = MagicMock()
    
    # Configure mocks
    mock_downloader.login.return_value = True
    mock_downloader.get_all_lessons.return_value = [
        {'title': 'Lesson 1', 'hash': 'abc123'},
        {'title': 'Lesson 2', 'hash': 'def456'}
    ]
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
        '--list'
    ])
    
    # Call the function
    result = main_func()
    
    # Check the results
    assert result == 0  # Success exit code
    mock_downloader.login.assert_called_once()
    mock_downloader.get_all_lessons.assert_called_once()
    mock_downloader.download_all_lessons.assert_not_called()  # Should not be called in list mode
    mock_downloader.close.assert_called_once()


def test_main_single_video_download(monkeypatch):
    """Test main function with single video download."""
    # Setup mocks
    mock_setup_logger = MagicMock()
    mock_logger = MagicMock()
    mock_downloader_class = MagicMock()
    mock_downloader = MagicMock()
    
    # Configure mocks
    mock_downloader.login.return_value = True
    mock_downloader.get_all_lessons.return_value = [
        {'title': 'Lesson 1', 'hash': 'abc123'},
        {'title': 'Lesson 2', 'hash': 'def456'}
    ]
    mock_downloader.extract_video_url.return_value = [("", "https://example.com/video.mp4")]
    mock_downloader.download_video.return_value = True
    mock_downloader.base_url = "https://example.com"
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
        '--single', 'Lesson 1'
    ])
    
    # Call the function
    result = main_func()
    
    # Check the results
    assert result == 0  # Success exit code
    mock_downloader.login.assert_called_once()
    mock_downloader.get_all_lessons.assert_called_once()
    mock_downloader.extract_video_url.assert_called_once_with("https://example.com/lesson/abc123")
    mock_downloader.download_video.assert_called_once()
    mock_downloader.close.assert_called_once()


def test_main_single_video_not_found(monkeypatch):
    """Test main function when single video is not found."""
    # Setup mocks
    mock_setup_logger = MagicMock()
    mock_logger = MagicMock()
    mock_downloader_class = MagicMock()
    mock_downloader = MagicMock()
    
    # Configure mocks
    mock_downloader.login.return_value = True
    mock_downloader.get_all_lessons.return_value = [
        {'title': 'Lesson 1', 'hash': 'abc123'},
        {'title': 'Lesson 2', 'hash': 'def456'}
    ]
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
        '--single', 'Nonexistent Lesson'
    ])
    
    # Call the function
    result = main_func()
    
    # Check the results
    assert result == 1  # Error exit code
    mock_downloader.login.assert_called_once()
    mock_downloader.get_all_lessons.assert_called_once()
    mock_downloader.extract_video_url.assert_not_called()
    mock_downloader.download_video.assert_not_called()
    mock_downloader.close.assert_called_once()


def test_main_with_index_download(monkeypatch):
    """Test main function with index-based downloading."""
    # Setup mocks
    mock_setup_logger = MagicMock()
    mock_logger = MagicMock()
    mock_downloader_class = MagicMock()
    mock_downloader = MagicMock()
    
    # Configure mocks
    mock_downloader.login.return_value = True
    mock_downloader.get_all_lessons.return_value = [
        {'title': 'Lesson 1', 'hash': 'abc123'},
        {'title': 'Lesson 2', 'hash': 'def456'},
        {'title': 'Lesson 3', 'hash': 'ghi789'}
    ]
    mock_downloader.extract_video_url.return_value = [("", "https://example.com/video.mp4")]
    mock_downloader.download_video.return_value = True
    mock_downloader.base_url = "https://example.com"
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
        '--indexes', '1,3'
    ])
    
    # Call the function
    result = main_func()
    
    # Check the results
    assert result == 0  # Success exit code
    mock_downloader.login.assert_called_once()
    mock_downloader.get_all_lessons.assert_called_once()
    
    # Should have called extract_video_url twice (for indexes 1 and 3)
    assert mock_downloader.extract_video_url.call_count == 2
    mock_downloader.extract_video_url.assert_any_call("https://example.com/lesson/abc123")
    mock_downloader.extract_video_url.assert_any_call("https://example.com/lesson/ghi789")
    
    # Should have called download_video twice (once for each lesson)
    assert mock_downloader.download_video.call_count == 2
    
    mock_downloader.close.assert_called_once()


def test_main_with_invalid_index_format(monkeypatch):
    """Test main function with invalid index format."""
    # Setup mocks
    mock_setup_logger = MagicMock()
    mock_logger = MagicMock()
    mock_downloader_class = MagicMock()
    mock_downloader = MagicMock()
    
    # Configure mocks
    mock_downloader.login.return_value = True
    mock_downloader.get_all_lessons.return_value = [
        {'title': 'Lesson 1', 'hash': 'abc123'},
        {'title': 'Lesson 2', 'hash': 'def456'}
    ]
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
        '--indexes', '1,invalid'  # Invalid format
    ])
    
    # Call the function
    result = main_func()
    
    # Check the results
    assert result == 1  # Error exit code
    mock_downloader.login.assert_called_once()
    mock_downloader.get_all_lessons.assert_called_once()
    mock_downloader.extract_video_url.assert_not_called()
    mock_downloader.download_video.assert_not_called()
    mock_downloader.close.assert_called_once()


def test_main_keyboard_interrupt(monkeypatch):
    """Test main function with keyboard interrupt."""
    # Setup mocks
    mock_setup_logger = MagicMock()
    mock_logger = MagicMock()
    mock_downloader_class = MagicMock()
    mock_downloader = MagicMock()
    
    # Configure mocks to raise KeyboardInterrupt
    mock_downloader.login.side_effect = KeyboardInterrupt()
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
    assert result == 130  # SIGINT exit code
    mock_downloader.login.assert_called_once()
    mock_downloader.close.assert_called_once()


def test_main_generic_exception(monkeypatch):
    """Test main function with generic exception."""
    # Setup mocks
    mock_setup_logger = MagicMock()
    mock_logger = MagicMock()
    mock_downloader_class = MagicMock()
    mock_downloader = MagicMock()
    
    # Configure mocks to raise an exception
    mock_downloader.login.side_effect = Exception("Test exception")
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
    assert result == 1  # Error exit code
    mock_downloader.login.assert_called_once()
    mock_downloader.close.assert_called_once()
    # Check that the error was logged
    mock_logger.error.assert_called_with("Unhandled exception: Test exception", exc_info=True)