"""
Pytest configuration and fixtures for 101kg tests.
"""
import os
import pytest
from unittest.mock import MagicMock
import requests
import logging


@pytest.fixture
def mock_session():
    """Create a mock requests session."""
    session = MagicMock(spec=requests.Session)
    session.get.return_value = MagicMock()
    session.get.return_value.status_code = 200
    session.get.return_value.text = ""
    session.get.return_value.json.return_value = {}
    session.cookies = MagicMock()
    return session


@pytest.fixture
def mock_driver():
    """Create a mock Selenium WebDriver."""
    driver = MagicMock()
    driver.get.return_value = None
    driver.execute_script.return_value = {}
    driver.find_element.return_value = MagicMock()
    driver.find_elements.return_value = []
    driver.get_cookies.return_value = []
    driver.switch_to = MagicMock()
    return driver


@pytest.fixture
def sample_iframe_src():
    """Sample iframe src attribute for testing."""
    return "https://cf-embed.play.hotmart.com/embed/12345?jwtToken=sample_token"


@pytest.fixture
def sample_content_with_auth_token():
    """Sample content with auth token for testing."""
    return """
    <html>
    <body>
      <script>
        const token = 'hdntl=exp=1234567890~acl=/*~data=hdntl~hmac=abc123';
        const url = 'https://vod-akm.play.hotmart.com/video/12345/hls/12345-audio=123-video=456.m3u8?' + token;
      </script>
    </body>
    </html>
    """


@pytest.fixture
def sample_m3u8_content():
    """Sample m3u8 playlist content for testing."""
    return """
    #EXTM3U
    #EXT-X-VERSION:3
    #EXT-X-STREAM-INF:BANDWIDTH=2756000,RESOLUTION=1280x720
    12345-audio=2756-video=2292536.m3u8
    #EXT-X-STREAM-INF:BANDWIDTH=1328000,RESOLUTION=854x480
    12345-audio=1328-video=1128536.m3u8
    """


@pytest.fixture
def test_environment():
    """Setup and teardown test environment."""
    # Setup
    original_env = os.environ.copy()
    logging.basicConfig(level=logging.DEBUG)
    
    yield
    
    # Teardown
    os.environ = original_env


@pytest.fixture
def sample_extraction_result():
    """Sample result from JavaScript extraction."""
    return {
        'foundUrl': 'https://vod-akm.play.hotmart.com/video/12345/hls/12345-audio=2756-video=2292536.m3u8?hdntl=exp=1234567890~acl=/*~data=hdntl~hmac=abc123',
        'masterUrl': 'https://vod-akm.play.hotmart.com/video/12345/hls/12345.m3u8?hdntl=exp=1234567890~acl=/*~data=hdntl~hmac=abc123',
        'videoId': '12345',
        'authToken': 'hdntl=exp=1234567890~acl=/*~data=hdntl~hmac=abc123',
        'jwtToken': 'sample_jwt_token',
        'allUrls': [
            'https://vod-akm.play.hotmart.com/video/12345/hls/12345-audio=2756-video=2292536.m3u8?hdntl=exp=1234567890~acl=/*~data=hdntl~hmac=abc123',
            'https://vod-akm.play.hotmart.com/video/12345/hls/12345.m3u8?hdntl=exp=1234567890~acl=/*~data=hdntl~hmac=abc123'
        ]
    }
    
@pytest.fixture
def mock_api_session():
    """Create a mock requests session for API testing."""
    session = MagicMock(spec=requests.Session)
    session.get.return_value = MagicMock()
    session.get.return_value.status_code = 200
    session.get.return_value.json.return_value = {"url": "https://example.com/video.m3u8"}
    session.get.return_value.text = """
    <html>
    <body>
      <script>
        const token = 'hdntl=exp=1234567890~acl=/*~data=hdntl~hmac=abc123';
        const url = 'https://vod-akm.play.hotmart.com/video/12345/hls/12345-audio=123-video=456.m3u8?' + token;
      </script>
    </body>
    </html>
    """
    return session