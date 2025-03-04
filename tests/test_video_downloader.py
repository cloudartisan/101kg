"""
Tests for the VideoDownloader class.
"""
import os
import pytest
import requests
import m3u8
from unittest.mock import MagicMock, patch, mock_open, call
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from video_downloader import VideoDownloader


@pytest.fixture
def video_downloader():
    """Create a VideoDownloader instance with mocked dependencies."""
    with patch('video_downloader.BrowserManager') as mock_browser_manager, \
         patch('video_downloader.requests.Session') as mock_session_class:
        
        # Configure browser manager mock
        mock_browser_manager_instance = mock_browser_manager.return_value
        mock_browser_manager_instance.initialize.return_value = MagicMock()
        
        # Configure session mock
        mock_session = mock_session_class.return_value
        mock_session.get.return_value = MagicMock(status_code=200)
        mock_session.cookies = MagicMock()
        
        # Create downloader
        downloader = VideoDownloader("test@example.com", "password", headless=True)
        
        # Access to mocks for assertions
        downloader._mock_browser_manager = mock_browser_manager_instance
        downloader._mock_session = mock_session
        
        yield downloader


class TestVideoDownloaderInit:
    """Tests for VideoDownloader initialization."""
    
    def test_init_creates_download_dir(self):
        """Test that init creates the download directory if it doesn't exist."""
        with patch('os.path.exists', return_value=False), \
             patch('os.makedirs') as mock_makedirs, \
             patch('video_downloader.BrowserManager') as mock_browser_manager:
            
            mock_browser_manager.return_value.initialize.return_value = MagicMock()
            
            VideoDownloader("test@example.com", "password")
            mock_makedirs.assert_called_once_with("videos")
    
    def test_init_fails_when_browser_init_fails(self):
        """Test that init raises an exception when browser initialization fails."""
        with patch('video_downloader.BrowserManager') as mock_browser_manager, \
             pytest.raises(Exception) as excinfo:
            
            mock_browser_manager.return_value.initialize.return_value = None
            
            VideoDownloader("test@example.com", "password")
            
        assert "Failed to initialize browser" in str(excinfo.value)


class TestVideoDownloaderLogin:
    """Tests for VideoDownloader login method."""
    
    def test_login_success(self, video_downloader):
        """Test successful login process."""
        # Mock the driver's behavior
        mock_driver = video_downloader.driver
        mock_driver.get.return_value = None
        
        # Set up element mocks
        mock_email_field = MagicMock()
        mock_password_field = MagicMock()
        mock_button = MagicMock()
        
        # Set up browser manager to return elements
        video_downloader._mock_browser_manager.wait_for_element.side_effect = [
            mock_email_field,    # Email field
            mock_password_field, # Password field
            mock_button          # Login button
        ]
        
        # Mock cookies
        mock_driver.get_cookies.return_value = [
            {'name': 'test_cookie', 'value': 'test_value', 'domain': 'example.com', 'path': '/'}
        ]
        
        # Mock WebDriverWait to avoid TypeError
        with patch('video_downloader.WebDriverWait') as mock_wait:
            # Call login method
            result = video_downloader.login()
            
            # Assertions
            assert result is True
            mock_driver.get.assert_called_once_with(video_downloader.login_url)
            mock_email_field.send_keys.assert_called_once_with(video_downloader.email)
            mock_password_field.send_keys.assert_called_once_with(video_downloader.password)
            mock_driver.execute_script.assert_called_once_with("arguments[0].click();", mock_button)
            video_downloader._mock_session.cookies.set.assert_called_once()
    
    def test_login_failure_email_field_not_found(self, video_downloader):
        """Test login failure when email field not found."""
        # Set up browser manager to return None for email field
        video_downloader._mock_browser_manager.wait_for_element.side_effect = [
            None  # Email field not found
        ]
        
        # Call login method
        result = video_downloader.login()
        
        # Assertions
        assert result is False
    
    def test_login_failure_password_field_not_found(self, video_downloader):
        """Test login failure when password field not found."""
        # Mock email field
        mock_email_field = MagicMock()
        
        # Set up browser manager to return email field but not password field
        video_downloader._mock_browser_manager.wait_for_element.side_effect = [
            mock_email_field,  # Email field
            None               # Password field not found
        ]
        
        # Call login method
        result = video_downloader.login()
        
        # Assertions
        assert result is False
    
    def test_login_failure_login_button_not_found(self, video_downloader):
        """Test login tries all button selectors before failing."""
        # Mock fields
        mock_email_field = MagicMock()
        mock_password_field = MagicMock()
        
        # Set up browser manager to return fields but no buttons
        video_downloader._mock_browser_manager.wait_for_element.side_effect = [
            mock_email_field,     # Email field
            mock_password_field,  # Password field
            None,                 # First button selector fails
            None,                 # Second button selector fails
            None                  # Third button selector fails
        ]
        
        # Call login method
        result = video_downloader.login()
        
        # Assertions
        assert result is False


class TestVideoDownloaderTransferCookies:
    """Tests for _transfer_cookies_to_session method."""
    
    def test_transfer_cookies(self, video_downloader):
        """Test that cookies are correctly transferred from driver to session."""
        # Set up mock cookies
        mock_cookies = [
            {'name': 'cookie1', 'value': 'value1', 'domain': 'domain1.com', 'path': '/path1'},
            {'name': 'cookie2', 'value': 'value2'}  # No domain or path
        ]
        
        video_downloader.driver.get_cookies.return_value = mock_cookies
        
        # Call the method
        video_downloader._transfer_cookies_to_session()
        
        # Assertions
        assert video_downloader._mock_session.cookies.set.call_count == 2
        video_downloader._mock_session.cookies.set.assert_any_call(
            name='cookie1', value='value1', domain='domain1.com', path='/path1'
        )
        video_downloader._mock_session.cookies.set.assert_any_call(
            name='cookie2', value='value2', domain='', path='/'
        )


class TestVideoDownloaderExtractVideoUrl:
    """Tests for extract_video_url method and its helper methods."""
    
    def test_extract_video_url_success_jwt_approach(self, video_downloader):
        """Test successful video URL extraction using JWT token approach."""
        # Mock iframe
        mock_iframe = MagicMock()
        mock_iframe.get_attribute.return_value = "https://cf-embed.play.hotmart.com/video/12345?jwtToken=test_jwt"
        
        # Mock wait and driver
        mock_wait = MagicMock()
        mock_wait.until.return_value = mock_iframe
        
        with patch('video_downloader.WebDriverWait', return_value=mock_wait), \
             patch('video_downloader.URLExtractor.extract_video_id_from_iframe', return_value="12345"), \
             patch.object(video_downloader, '_extract_jwt_token', return_value="test_jwt"), \
             patch.object(video_downloader, '_try_jwt_token_approach') as mock_jwt_approach:
            
            # Set up JWT approach to return a URL
            mock_jwt_approach.return_value = [("", "https://example.com/video.m3u8")]
            
            # Call the method
            result = video_downloader.extract_video_url("https://example.com/lesson")
            
            # Assertions
            assert result == [("", "https://example.com/video.m3u8")]
            video_downloader.driver.get.assert_called_once_with("https://example.com/lesson")
            mock_jwt_approach.assert_called_once_with("12345", "test_jwt")
    
    def test_extract_video_url_fallback_to_api(self, video_downloader):
        """Test fallback to API approach when JWT approach fails."""
        # Mock iframe
        mock_iframe = MagicMock()
        mock_iframe.get_attribute.return_value = "https://cf-embed.play.hotmart.com/video/12345?jwtToken=test_jwt"
        
        # Mock wait and driver
        mock_wait = MagicMock()
        mock_wait.until.return_value = mock_iframe
        
        with patch('video_downloader.WebDriverWait', return_value=mock_wait), \
             patch('video_downloader.URLExtractor.extract_video_id_from_iframe', return_value="12345"), \
             patch.object(video_downloader, '_extract_jwt_token', return_value="test_jwt"), \
             patch.object(video_downloader, '_try_jwt_token_approach', return_value=[]), \
             patch.object(video_downloader, '_try_api_approach') as mock_api_approach:
            
            # Set up API approach to return a URL
            mock_api_approach.return_value = [("", "https://example.com/video.m3u8")]
            
            # Call the method
            result = video_downloader.extract_video_url("https://example.com/lesson")
            
            # Assertions
            assert result == [("", "https://example.com/video.m3u8")]
            mock_api_approach.assert_called_once_with("12345", "test_jwt")
    
    def test_extract_video_url_all_approaches_fail(self, video_downloader):
        """Test that empty list is returned when all approaches fail."""
        # Mock iframe
        mock_iframe = MagicMock()
        mock_iframe.get_attribute.return_value = "https://cf-embed.play.hotmart.com/video/12345?jwtToken=test_jwt"
        
        # Mock wait and driver
        mock_wait = MagicMock()
        mock_wait.until.return_value = mock_iframe
        
        with patch('video_downloader.WebDriverWait', return_value=mock_wait), \
             patch.object(video_downloader, '_try_jwt_token_approach', return_value=[]), \
             patch.object(video_downloader, '_try_api_approach', return_value=[]), \
             patch.object(video_downloader, '_try_javascript_extraction', return_value=[]), \
             patch.object(video_downloader, '_try_direct_embed_approach', return_value=[]), \
             patch.object(video_downloader, '_try_network_requests_approach', return_value=[]):
            
            # Call the method
            result = video_downloader.extract_video_url("https://example.com/lesson")
            
            # Assertions
            assert result == []
    
    def test_extract_video_url_iframe_not_found(self, video_downloader):
        """Test that empty list is returned when iframe is not found."""
        # Mock wait to raise exception
        mock_wait = MagicMock()
        mock_wait.until.side_effect = Exception("Iframe not found")
        
        with patch('video_downloader.WebDriverWait', return_value=mock_wait):
            # Call the method
            result = video_downloader.extract_video_url("https://example.com/lesson")
            
            # Assertions
            assert result == []


class TestVideoDownloaderJwtTokenApproach:
    """Tests for _try_jwt_token_approach method."""
    
    def test_try_jwt_token_approach_no_token(self, video_downloader):
        """Test that empty list is returned when no JWT token is provided."""
        result = video_downloader._try_jwt_token_approach("12345", None)
        assert result == []
    
    def test_try_jwt_token_approach_direct_api_success(self, video_downloader):
        """Test successful URL retrieval through direct API call with JWT token."""
        # Mock session response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"url": "https://example.com/video.m3u8"}
        video_downloader._mock_session.get.return_value = mock_response
        
        # Call the method
        result = video_downloader._try_jwt_token_approach("12345", "test_jwt")
        
        # Assertions
        assert result == [("", "https://example.com/video.m3u8")]
        video_downloader._mock_session.get.assert_called_once()


class TestVideoDownloaderApiApproach:
    """Tests for _try_api_approach method."""
    
    def test_try_api_approach_success(self, video_downloader):
        """Test successful API approach."""
        with patch.object(video_downloader, 'get_video_url_from_api') as mock_get_url:
            mock_get_url.return_value = "https://example.com/video.m3u8"
            
            result = video_downloader._try_api_approach("12345", "test_jwt")
            
            assert result == [("", "https://example.com/video.m3u8")]
            mock_get_url.assert_called_once_with("12345", "test_jwt")
    
    def test_try_api_approach_failure(self, video_downloader):
        """Test API approach failure."""
        with patch.object(video_downloader, 'get_video_url_from_api') as mock_get_url:
            mock_get_url.return_value = None
            
            result = video_downloader._try_api_approach("12345", "test_jwt")
            
            assert result == []
            mock_get_url.assert_called_once_with("12345", "test_jwt")


class TestVideoDownloaderDownload:
    """Tests for download_video method and its helper methods."""
    
    def test_download_video_hls(self, video_downloader):
        """Test download of HLS video."""
        with patch.object(video_downloader, '_download_hls') as mock_download_hls:
            result = video_downloader.download_video("https://example.com/video.m3u8", "test_video")
            
            assert result is True
            mock_download_hls.assert_called_once_with("https://example.com/video.m3u8", "test_video")
    
    def test_download_video_mp4(self, video_downloader):
        """Test download of MP4 video."""
        with patch.object(video_downloader, '_download_mp4') as mock_download_mp4:
            result = video_downloader.download_video("https://example.com/video.mp4", "test_video")
            
            assert result is True
            mock_download_mp4.assert_called_once_with("https://example.com/video.mp4", "test_video")
    
    def test_download_video_exception(self, video_downloader):
        """Test exception handling during video download."""
        with patch.object(video_downloader, '_download_hls') as mock_download_hls:
            mock_download_hls.side_effect = Exception("Download failed")
            
            result = video_downloader.download_video("https://example.com/video.m3u8", "test_video")
            
            assert result is False
    
    def test_download_mp4_success(self, video_downloader):
        """Test successful MP4 download."""
        # Mock session response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = "1000"
        mock_response.iter_content.return_value = [b"test data"]
        video_downloader._mock_session.get.return_value = mock_response
        
        # Mock file operations
        with patch('builtins.open', mock_open()) as mock_file:
            video_downloader._download_mp4("https://example.com/video.mp4", "test_video")
            
            # Assertions - We only check that get was called once with the right URL
            # and stream param since headers now include dynamic fields
            assert video_downloader._mock_session.get.call_count == 1
            call_args = video_downloader._mock_session.get.call_args
            assert call_args[0][0] == "https://example.com/video.mp4"
            assert call_args[1]['stream'] is True
            
            # Validate the basic headers are present (without requiring exact match
            # which would make the test too brittle)
            headers = call_args[1]['headers']
            assert headers['Origin'] == 'https://cf-embed.play.hotmart.com'
            assert headers['Referer'] == 'https://cf-embed.play.hotmart.com/'
            assert headers['User-Agent'] == 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0'
            assert headers['Accept'] == '*/*'
            assert headers['Accept-Language'] == 'en-US,en;q=0.5'
            
            # Validate file operations
            mock_file.assert_called_once_with(os.path.join("videos", "test_video.mp4"), 'wb')
            mock_file().write.assert_called_once_with(b"test data")
    
    def test_download_mp4_failure(self, video_downloader):
        """Test MP4 download failure handling."""
        # Mock session response for failure
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.headers = {'Content-Type': 'application/json'}
        video_downloader._mock_session.get.return_value = mock_response
        
        # Test exception is raised
        with pytest.raises(Exception) as excinfo:
            video_downloader._download_mp4("https://example.com/video.mp4", "test_video")
        
        assert "MP4 download failed: HTTP 401" in str(excinfo.value)


class TestVideoDownloaderHlsDownload:
    """Tests for _download_hls method."""
    
    def test_download_hls_success_primary_method(self, video_downloader):
        """Test successful HLS download using primary method."""
        # Mock m3u8 playlist
        mock_playlist = MagicMock()
        
        with patch('m3u8.loads', return_value=mock_playlist), \
             patch.object(video_downloader, '_prepare_ffmpeg_headers', return_value="headers"), \
             patch.object(video_downloader, '_download_with_ffmpeg_python') as mock_primary_method:
            
            # Mock session response
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.text = "#EXTM3U\n#EXT-X-VERSION:3"
            video_downloader._mock_session.get.return_value = mock_response
            
            video_downloader._download_hls("https://example.com/video.m3u8", "test_video")
            
            # Assertions
            video_downloader._mock_session.get.assert_called_once()
            mock_primary_method.assert_called_once_with(
                "https://example.com/video.m3u8", 
                os.path.join("videos", "test_video.mp4"), 
                "headers"
            )
    
    def test_download_hls_fallback_method(self, video_downloader):
        """Test HLS download falling back to secondary method when primary fails."""
        # Mock m3u8 playlist
        mock_playlist = MagicMock()
        
        with patch('m3u8.loads', return_value=mock_playlist), \
             patch.object(video_downloader, '_prepare_ffmpeg_headers', return_value="headers"), \
             patch.object(video_downloader, '_download_with_ffmpeg_python', side_effect=Exception("Primary method failed")), \
             patch.object(video_downloader, '_download_with_ffmpeg_subprocess') as mock_fallback_method:
            
            # Mock session response
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.text = "#EXTM3U\n#EXT-X-VERSION:3"
            video_downloader._mock_session.get.return_value = mock_response
            
            video_downloader._download_hls("https://example.com/video.m3u8", "test_video")
            
            # Assertions
            mock_fallback_method.assert_called_once_with(
                "https://example.com/video.m3u8", 
                os.path.join("videos", "test_video.mp4")
            )
    
    def test_download_hls_playlist_fetch_failure(self, video_downloader):
        """Test exception handling when playlist fetch fails."""
        # Mock session response
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        video_downloader._mock_session.get.return_value = mock_response
        
        with pytest.raises(Exception) as excinfo:
            video_downloader._download_hls("https://example.com/video.m3u8", "test_video")
        
        assert "Failed to load playlist: 404" in str(excinfo.value)


class TestVideoDownloaderLessonDownload:
    """Tests for high-level lesson download methods."""
    
    def test_get_lesson_title(self, video_downloader):
        """Test lesson title extraction."""
        # Mock driver and wait
        mock_title_element = MagicMock()
        mock_title_element.text = "Test Lesson Title!"
        
        mock_wait = MagicMock()
        mock_wait.until.return_value = mock_title_element
        
        with patch('video_downloader.WebDriverWait', return_value=mock_wait):
            title = video_downloader.get_lesson_title()
            
            assert title == "Test Lesson Title"
    
    def test_get_lesson_title_exception(self, video_downloader):
        """Test exception handling in lesson title extraction."""
        # Mock wait to raise exception
        mock_wait = MagicMock()
        mock_wait.until.side_effect = Exception("Title not found")
        
        with patch('video_downloader.WebDriverWait', return_value=mock_wait):
            title = video_downloader.get_lesson_title()
            
            assert title == "lesson"
    
    def test_get_all_lessons(self, video_downloader):
        """Test extraction of all lessons."""
        # Mock lesson elements
        mock_lesson1 = MagicMock()
        mock_lesson1.get_attribute.return_value = "hash1"
        mock_title1 = MagicMock()
        mock_title1.text = "Lesson 1"
        mock_lesson1.find_element.return_value = mock_title1
        
        mock_lesson2 = MagicMock()
        mock_lesson2.get_attribute.return_value = "hash2"
        mock_title2 = MagicMock()
        mock_title2.text = "Lesson 2"
        mock_lesson2.find_element.return_value = mock_title2
        
        # Mock wait
        mock_wait = MagicMock()
        mock_wait.until.return_value = [mock_lesson1, mock_lesson2]
        
        with patch('video_downloader.WebDriverWait', return_value=mock_wait):
            lessons = video_downloader.get_all_lessons()
            
            assert len(lessons) == 2
            assert lessons[0] == {'hash': 'hash1', 'title': 'Lesson 1'}
            assert lessons[1] == {'hash': 'hash2', 'title': 'Lesson 2'}
    
    def test_download_all_lessons(self, video_downloader):
        """Test downloading all lessons."""
        # Mock methods
        with patch.object(video_downloader, 'get_all_lessons') as mock_get_lessons, \
             patch.object(video_downloader, 'extract_video_url') as mock_extract_url, \
             patch.object(video_downloader, 'download_video') as mock_download:
            
            # Setup mocks
            mock_get_lessons.return_value = [
                {'hash': 'hash1', 'title': 'Lesson 1'},
                {'hash': 'hash2', 'title': 'Lesson 2'}
            ]
            mock_extract_url.side_effect = [
                [("", "https://example.com/video1.m3u8")],  # First lesson
                [("part1", "https://example.com/video2_part1.m3u8"), 
                 ("part2", "https://example.com/video2_part2.m3u8")]  # Second lesson with parts
            ]
            mock_download.return_value = True
            
            # Call method
            video_downloader.download_all_lessons()
            
            # Assertions
            assert mock_extract_url.call_count == 2
            mock_extract_url.assert_any_call("https://101karategames.club.hotmart.com/lesson/hash1")
            mock_extract_url.assert_any_call("https://101karategames.club.hotmart.com/lesson/hash2")
            
            assert mock_download.call_count == 3
            mock_download.assert_any_call("https://example.com/video1.m3u8", "001_Lesson 1")
            mock_download.assert_any_call("https://example.com/video2_part1.m3u8", "002_Lesson 2_part1")
            mock_download.assert_any_call("https://example.com/video2_part2.m3u8", "002_Lesson 2_part2")