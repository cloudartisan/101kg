"""
Test cases for the browser audio diagnostic tool.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call

# Add scripts directory to import path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
import browser_audio_diagnostic

@pytest.fixture
def mock_browser_manager():
    """Fixture for mocked BrowserManager."""
    with patch('browser_audio_diagnostic.BrowserManager') as mock_browser_class:
        mock_manager = MagicMock()
        mock_browser_class.return_value = mock_manager
        yield mock_manager

@pytest.fixture
def mock_driver():
    """Fixture for mocked WebDriver."""
    mock_driver = MagicMock()
    yield mock_driver

def test_diagnose_audio_capture_successful(mock_browser_manager, mock_driver):
    """Test successful audio capture diagnostic scenario."""
    # Setup the mock manager to return mock driver
    mock_browser_manager.initialize.return_value = mock_driver
    
    # Setup video element
    mock_video = MagicMock()
    mock_driver.find_element.return_value = mock_video
    
    # Mock successful JavaScript recording
    mock_result = {
        'success': True,
        'blob_size': 1000,
        'audioTracks': 1,
        'base64': 'data:video/webm;base64,ABC123=='
    }
    mock_driver.execute_script.return_value = mock_result
    
    # Mock os.path.exists and makedirs
    with patch('os.path.exists', return_value=False), \
         patch('os.makedirs') as mock_makedirs, \
         patch('builtins.open', create=True) as mock_open, \
         patch('base64.b64decode', return_value=b'test_data'), \
         patch('subprocess.run') as mock_subprocess_run:
        
        # Call the function
        browser_audio_diagnostic.diagnose_audio_capture()
        
        # Assertions
        mock_browser_manager.initialize.assert_called_once()
        mock_driver.get.assert_called_once_with('https://www.w3schools.com/html/html5_video.asp')
        mock_driver.execute_script.assert_any_call("arguments[0].play(); arguments[0].muted = false;", mock_video)
        
        # Verify directory creation - Note: log directory is also created
        assert mock_makedirs.call_count >= 1
        assert call('audio_diagnostic_results') in mock_makedirs.call_args_list
        
        # Verify file writing
        mock_open.assert_called()
        
        # Verify ffmpeg conversion
        mock_subprocess_run.assert_called_once()
        
        # Verify browser was closed
        mock_driver.quit.assert_called_once()
        
def test_diagnose_audio_capture_failure(mock_browser_manager, mock_driver):
    """Test failed audio capture diagnostic scenario."""
    # Setup the mock manager to return mock driver
    mock_browser_manager.initialize.return_value = mock_driver
    
    # Setup video element
    mock_video = MagicMock()
    mock_driver.find_element.return_value = mock_video
    
    # Mock failed JavaScript recording
    mock_result = {
        'success': False,
        'error': 'Could not access audio stream'
    }
    mock_driver.execute_script.return_value = mock_result
    
    # Call the function with mocks
    with patch('os.path.exists', return_value=True):
        browser_audio_diagnostic.diagnose_audio_capture()
        
        # Assertions
        mock_browser_manager.initialize.assert_called_once()
        mock_driver.get.assert_called_once_with('https://www.w3schools.com/html/html5_video.asp')
        mock_driver.execute_script.assert_any_call("arguments[0].play(); arguments[0].muted = false;", mock_video)
        
        # Verify browser was closed despite error
        mock_driver.quit.assert_called_once()