"""
Tests for the url_extractor module.
"""
import pytest
from unittest.mock import patch, MagicMock, call, ANY
import responses
import re

from url_extractor import URLExtractor
from url_utils import (
    HOTMART_CDN_BASE, 
    HOTMART_EMBED_BASE, 
    HOTMART_PLAYER_API, 
    HOTMART_CLUB_API,
    HDNTL_PATTERN
)


class TestJavaScriptGeneration:
    """Tests for JavaScript extraction script generation."""

    def test_get_extraction_script(self):
        """Test that get_extraction_script combines all script parts."""
        with patch.object(URLExtractor, '_get_script_initialization') as mock_init:
            mock_init.return_value = "init"
            with patch.object(URLExtractor, '_get_token_extraction_script') as mock_token:
                mock_token.return_value = "token"
                with patch.object(URLExtractor, '_get_video_id_extraction_script') as mock_video_id:
                    mock_video_id.return_value = "video_id"
                    with patch.object(URLExtractor, '_get_jwt_token_handling_script') as mock_jwt:
                        mock_jwt.return_value = "jwt"
                        with patch.object(URLExtractor, '_get_network_interception_script') as mock_network:
                            mock_network.return_value = "network"
                            with patch.object(URLExtractor, '_get_url_processing_script') as mock_processing:
                                mock_processing.return_value = "processing"
                                with patch.object(URLExtractor, '_get_video_source_script') as mock_source:
                                    mock_source.return_value = "source"
                                    with patch.object(URLExtractor, '_get_trigger_video_script') as mock_trigger:
                                        mock_trigger.return_value = "trigger"
                                        with patch.object(URLExtractor, '_get_resolution_script') as mock_resolution:
                                            mock_resolution.return_value = "resolution"
                                            
                                            script = URLExtractor.get_extraction_script()
                                            
                                            # Verify all script parts were combined
                                            assert script == "init\ntoken\nvideo_id\njwt\nnetwork\nprocessing\nsource\ntrigger\nresolution"
                                            
                                            # Verify all methods were called
                                            mock_init.assert_called_once()
                                            mock_token.assert_called_once()
                                            mock_video_id.assert_called_once()
                                            mock_jwt.assert_called_once()
                                            mock_network.assert_called_once()
                                            mock_processing.assert_called_once()
                                            mock_source.assert_called_once()
                                            mock_trigger.assert_called_once()
                                            mock_resolution.assert_called_once()

    def test_script_initialization(self):
        """Test the script initialization part."""
        script = URLExtractor._get_script_initialization()
        assert "return new Promise" in script
        assert "foundUrl = null" in script
        assert "allUrls = []" in script
        assert "videoId = null" in script
        assert "authToken = null" in script
        assert "jwtToken = null" in script

    def test_token_extraction_script(self):
        """Test the token extraction script part."""
        script = URLExtractor._get_token_extraction_script()
        assert "window.location.search" in script
        assert "urlParams.has('jwt')" in script
        assert "urlParams.get('jwt')" in script

    def test_video_id_extraction_script(self):
        """Test the video ID extraction script part."""
        script = URLExtractor._get_video_id_extraction_script()
        assert "document.querySelector('video')" in script
        assert "videoElement.dataset.videoId" in script
        assert "videoElement.play()" in script
        assert "processUrl(videoElement.src)" in script

    def test_jwt_token_handling_script(self):
        """Test the JWT token handling script part."""
        script = URLExtractor._get_jwt_token_handling_script()
        assert "jwtToken && videoId" in script
        assert "fetch(`https://cf-embed.play.hotmart.com/video/${videoId}/play?jwt=${jwtToken}`" in script
        assert "then(response => response.json())" in script
        assert "processUrl(data.url)" in script

    def test_network_interception_script(self):
        """Test the network interception script part."""
        script = URLExtractor._get_network_interception_script()
        assert "const hdntlRegex = /hdntl=exp=" in script
        assert "performance.getEntries()" in script
        assert "const origXHROpen = XMLHttpRequest.prototype.open" in script
        assert "const origFetch = window.fetch" in script
        assert "processUrl(url)" in script
        
    def test_url_processing_script(self):
        """Test the URL processing script part."""
        script = URLExtractor._get_url_processing_script()
        assert "function processUrl(url)" in script
        assert "const videoIdIndex = urlParts.findIndex(part => part === 'video')" in script
        assert "const hdntlRegex = /hdntl=exp=" in script
        assert "if (url.includes('/master') && url.includes('.m3u8'))" in script
        assert "if (url.includes('.m3u8') && (url.includes('audio=') || url.includes('video='))" in script
        
    def test_video_source_script(self):
        """Test the video source script part."""
        script = URLExtractor._get_video_source_script()
        assert "const videoSources = document.querySelectorAll('video source')" in script
        assert "const sourceUrl = source.src" in script
        assert "if (sourceUrl && sourceUrl.includes('vod-akm.play.hotmart.com'))" in script
        
    def test_trigger_video_script(self):
        """Test the trigger video script part."""
        script = URLExtractor._get_trigger_video_script()
        assert "const playButtons = document.querySelectorAll('.play-button, button[aria-label=\"Play\"]" in script
        assert "button.click()" in script
        
    def test_resolution_script(self):
        """Test the resolution script part."""
        script = URLExtractor._get_resolution_script()
        assert "setTimeout(" in script
        assert "if (videoId && authToken && !foundUrl)" in script
        assert "foundUrl = `https://vod-akm.play.hotmart.com/video/${videoId}/hls/${videoId}-audio=2756-video=2292536.m3u8?${authToken}`" in script
        assert "resolve({" in script
        assert "}, 8000)" in script


class TestExtractionResultProcessing:
    """Tests for extraction result processing."""

    def test_process_extraction_result_with_found_url(self, sample_extraction_result):
        """Test processing extraction result with foundUrl."""
        result = URLExtractor.process_extraction_result(sample_extraction_result)
        
        # Should return one URL with empty part suffix
        assert len(result) == 1
        assert result[0][0] == ""  # part suffix
        assert result[0][1] == sample_extraction_result['foundUrl']
        
    def test_try_found_url(self, sample_extraction_result):
        """Test the _try_found_url helper method."""
        video_urls = []
        
        # When foundUrl exists, it should return True and add the URL
        result = URLExtractor._try_found_url(sample_extraction_result, video_urls)
        assert result is True
        assert len(video_urls) == 1
        assert video_urls[0][0] == ""
        assert video_urls[0][1] == sample_extraction_result['foundUrl']
        
        # When foundUrl doesn't exist, it should return False and not add anything
        video_urls = []
        result = URLExtractor._try_found_url({}, video_urls)
        assert result is False
        assert len(video_urls) == 0

    def test_process_extraction_result_with_video_id_and_auth_token(self):
        """Test processing extraction result with just video ID and auth token."""
        result_data = {
            'videoId': '12345',
            'authToken': 'hdntl=test_token',
            'allUrls': []
        }
        
        result = URLExtractor.process_extraction_result(result_data)
        
        # Should return one URL with empty part suffix
        assert len(result) == 1
        assert result[0][0] == ""  # part suffix
        # Should construct URL from video ID and auth token
        assert "12345" in result[0][1]
        assert "hdntl=test_token" in result[0][1]
        
    def test_try_construct_from_id_and_token(self):
        """Test the _try_construct_from_id_and_token helper method."""
        video_urls = []
        
        # When videoId and authToken exist, it should return True and add the URL
        result_data = {
            'videoId': '12345',
            'authToken': 'hdntl=test_token'
        }
        result = URLExtractor._try_construct_from_id_and_token(result_data, video_urls)
        assert result is True
        assert len(video_urls) == 1
        assert video_urls[0][0] == ""
        assert "12345" in video_urls[0][1]
        assert "hdntl=test_token" in video_urls[0][1]
        
        # When videoId or authToken doesn't exist, it should return False
        video_urls = []
        result = URLExtractor._try_construct_from_id_and_token({'videoId': '12345'}, video_urls)
        assert result is False
        assert len(video_urls) == 0
        
        video_urls = []
        result = URLExtractor._try_construct_from_id_and_token({'authToken': 'hdntl=test_token'}, video_urls)
        assert result is False
        assert len(video_urls) == 0

    @patch('url_extractor.URLExtractor.get_url_from_api')
    def test_process_extraction_result_with_jwt_token(self, mock_get_url):
        """Test processing extraction result with JWT token."""
        mock_get_url.return_value = "https://example.com/video.m3u8"
        mock_session = MagicMock()
        
        result_data = {
            'videoId': '12345',
            'jwtToken': 'sample_jwt_token',
            'allUrls': []
        }
        
        result = URLExtractor.process_extraction_result(result_data, mock_session)
        
        # Should call get_url_from_api with JWT token
        mock_get_url.assert_called_once_with('12345', mock_session, 'sample_jwt_token')
        
        # Should return URL from API
        assert len(result) == 1
        assert result[0][0] == ""  # part suffix
        assert result[0][1] == "https://example.com/video.m3u8"
        
    @patch('url_extractor.URLExtractor.get_url_from_api')
    def test_try_jwt_token_api(self, mock_get_url):
        """Test the _try_jwt_token_api helper method."""
        mock_get_url.return_value = "https://example.com/video.m3u8"
        mock_session = MagicMock()
        video_urls = []
        
        # When videoId, jwtToken and session exist, it should return True and add the URL
        result_data = {
            'videoId': '12345',
            'jwtToken': 'sample_jwt_token'
        }
        result = URLExtractor._try_jwt_token_api(result_data, mock_session, video_urls)
        assert result is True
        assert len(video_urls) == 1
        assert video_urls[0][0] == ""
        assert video_urls[0][1] == "https://example.com/video.m3u8"
        mock_get_url.assert_called_once_with('12345', mock_session, 'sample_jwt_token')
        
        # When get_url_from_api returns None, it should return False
        mock_get_url.reset_mock()
        mock_get_url.return_value = None
        video_urls = []
        result = URLExtractor._try_jwt_token_api(result_data, mock_session, video_urls)
        assert result is False
        assert len(video_urls) == 0
        
        # When videoId or jwtToken or session doesn't exist, it should return False
        mock_get_url.reset_mock()
        video_urls = []
        result = URLExtractor._try_jwt_token_api({'videoId': '12345'}, mock_session, video_urls)
        assert result is False
        assert len(video_urls) == 0
        mock_get_url.assert_not_called()
        
        video_urls = []
        result = URLExtractor._try_jwt_token_api({'jwtToken': 'sample_jwt_token'}, mock_session, video_urls)
        assert result is False
        assert len(video_urls) == 0
        mock_get_url.assert_not_called()
        
        video_urls = []
        result = URLExtractor._try_jwt_token_api(result_data, None, video_urls)
        assert result is False
        assert len(video_urls) == 0
        mock_get_url.assert_not_called()

    def test_process_extraction_result_with_master_url(self):
        """Test processing extraction result with master URL fallback."""
        result_data = {
            'masterUrl': 'https://example.com/master.m3u8',
            'allUrls': []
        }
        
        result = URLExtractor.process_extraction_result(result_data)
        
        # Should return master URL
        assert len(result) == 1
        assert result[0][0] == ""  # part suffix
        assert result[0][1] == "https://example.com/master.m3u8"
        
    def test_try_master_playlist(self):
        """Test the _try_master_playlist helper method."""
        video_urls = []
        
        # When masterUrl exists, it should return True and add the URL
        result_data = {
            'masterUrl': 'https://example.com/master.m3u8'
        }
        result = URLExtractor._try_master_playlist(result_data, video_urls)
        assert result is True
        assert len(video_urls) == 1
        assert video_urls[0][0] == ""
        assert video_urls[0][1] == "https://example.com/master.m3u8"
        
        # When masterUrl doesn't exist, it should return False
        video_urls = []
        result = URLExtractor._try_master_playlist({}, video_urls)
        assert result is False
        assert len(video_urls) == 0

    @patch('url_extractor.URLExtractor.get_url_from_api')
    def test_process_extraction_result_with_api_fallback(self, mock_get_url):
        """Test processing extraction result with API fallback."""
        mock_get_url.return_value = "https://example.com/video_api.m3u8"
        mock_session = MagicMock()
        
        result_data = {
            'videoId': '12345',
            'allUrls': []
        }
        
        result = URLExtractor.process_extraction_result(result_data, mock_session)
        
        # Should call get_url_from_api without JWT token
        mock_get_url.assert_called_once_with('12345', mock_session)
        
        # Should return URL from API
        assert len(result) == 1
        assert result[0][0] == ""  # part suffix
        assert result[0][1] == "https://example.com/video_api.m3u8"
        
    @patch('url_extractor.URLExtractor.get_url_from_api')
    def test_try_api_with_video_id(self, mock_get_url):
        """Test the _try_api_with_video_id helper method."""
        mock_get_url.return_value = "https://example.com/video_api.m3u8"
        mock_session = MagicMock()
        video_urls = []
        
        # When videoId and session exist, it should return True and add the URL
        result_data = {
            'videoId': '12345'
        }
        result = URLExtractor._try_api_with_video_id(result_data, mock_session, video_urls)
        assert result is True
        assert len(video_urls) == 1
        assert video_urls[0][0] == ""
        assert video_urls[0][1] == "https://example.com/video_api.m3u8"
        mock_get_url.assert_called_once_with('12345', mock_session)
        
        # When get_url_from_api returns None, it should return False
        mock_get_url.reset_mock()
        mock_get_url.return_value = None
        video_urls = []
        result = URLExtractor._try_api_with_video_id(result_data, mock_session, video_urls)
        assert result is False
        assert len(video_urls) == 0
        
        # When videoId or session doesn't exist, it should return False
        mock_get_url.reset_mock()
        video_urls = []
        result = URLExtractor._try_api_with_video_id({}, mock_session, video_urls)
        assert result is False
        assert len(video_urls) == 0
        mock_get_url.assert_not_called()
        
        video_urls = []
        result = URLExtractor._try_api_with_video_id(result_data, None, video_urls)
        assert result is False
        assert len(video_urls) == 0
        mock_get_url.assert_not_called()

    def test_process_extraction_result_direct_construction(self):
        """Test processing extraction result with direct URL construction."""
        result_data = {
            'videoId': '12345',
            'allUrls': []
        }
        
        # Mock all API methods to fail
        with patch('url_extractor.URLExtractor.get_url_from_api', return_value=None):
            result = URLExtractor.process_extraction_result(result_data, MagicMock())
            
            # Should construct URL directly from video ID
            assert len(result) == 1
            assert result[0][0] == ""  # part suffix
            assert "12345" in result[0][1]
            # The URL construction in url_utils.py already has "video" in the base URL
            # So we need to match against the correctly constructed path
            expected_url_part = f"{HOTMART_CDN_BASE}/12345/hls/12345-audio="
            assert expected_url_part in result[0][1]
            
    def test_construct_direct_url(self):
        """Test the _construct_direct_url helper method."""
        video_urls = []
        
        # Should always return True and add the URL
        result = URLExtractor._construct_direct_url('12345', video_urls)
        assert result is True
        assert len(video_urls) == 1
        assert video_urls[0][0] == ""
        assert "12345" in video_urls[0][1]
        expected_url_part = f"{HOTMART_CDN_BASE}/12345/hls/12345-audio="
        assert expected_url_part in video_urls[0][1]

    def test_process_extraction_result_invalid_type(self):
        """Test processing extraction result with invalid data type."""
        # Test with non-dict input
        result = URLExtractor.process_extraction_result("not a dict")
        assert result == []
        
        # Test with None input
        result = URLExtractor.process_extraction_result(None)
        assert result == []


class TestURLExtractionFromAPI:
    """Tests for URL extraction from API endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_api_session):
        """Set up common test variables."""
        self.video_id = "12345"
        self.jwt_token = "sample_jwt_token"
        self.session = mock_api_session
        
    def test_jwt_token_api_endpoint_error(self):
        """Test error handling in JWT token API endpoint."""
        # Test with HTTP error
        self.session.get.return_value.status_code = 404
        url = URLExtractor._try_jwt_token_api_endpoint(self.video_id, self.session, self.jwt_token)
        assert url is None
        
        # Test with JSON parsing error
        self.session.get.return_value.status_code = 200
        self.session.get.return_value.json.side_effect = ValueError("Invalid JSON")
        url = URLExtractor._try_jwt_token_api_endpoint(self.video_id, self.session, self.jwt_token)
        assert url is None
        
        # Test with missing 'url' in response
        self.session.get.return_value.json.side_effect = None
        self.session.get.return_value.json.return_value = {"data": "no url"}
        url = URLExtractor._try_jwt_token_api_endpoint(self.video_id, self.session, self.jwt_token)
        assert url is None

    def test_jwt_token_api_endpoint(self):
        """Test getting URL using JWT token API endpoint."""
        # Reset mock to ensure clean state after error tests
        self.session.get.reset_mock()
        self.session.get.return_value.status_code = 200
        self.session.get.return_value.json.return_value = {"url": "https://example.com/video.m3u8"}
        
        # Test the _try_jwt_token_api_endpoint method
        url = URLExtractor._try_jwt_token_api_endpoint(self.video_id, self.session, self.jwt_token)
        
        # Verify the correct endpoint was called
        jwt_api_url = f"https://cf-embed.play.hotmart.com/video/{self.video_id}/play?jwt={self.jwt_token}"
        self.session.get.assert_called_once_with(jwt_api_url, headers=ANY)
        
        # Verify the URL was returned
        assert url == "https://example.com/video.m3u8"

    def test_player_api(self):
        """Test getting URL using player API."""
        # Reset mock
        self.session.get.reset_mock()
        
        # Test the _try_player_api method
        url = URLExtractor._try_player_api(self.video_id, self.session)
        
        # Verify the correct endpoint was called
        player_api_url = f"{HOTMART_PLAYER_API}/{self.video_id}/play"
        self.session.get.assert_called_once_with(player_api_url, headers=ANY)
        
        # Verify the URL was returned
        assert url == "https://example.com/video.m3u8"

    def test_club_api(self):
        """Test getting URL using club API."""
        # Reset mock
        self.session.get.reset_mock()
        
        # Test the _try_club_api method
        url = URLExtractor._try_club_api(self.video_id, self.session)
        
        # Verify the correct endpoint was called
        club_api_url = f"{HOTMART_CLUB_API}/{self.video_id}/play"
        self.session.get.assert_called_once_with(club_api_url, headers=ANY)
        
        # Verify the URL was returned
        assert url == "https://example.com/video.m3u8"

    def test_embed_api(self):
        """Test getting URL using embed API."""
        # Reset mock
        self.session.get.reset_mock()
        
        # Test the _try_embed_api method
        url = URLExtractor._try_embed_api(self.video_id, self.session)
        
        # Verify the correct endpoint was called
        embed_api_url = f"https://cf-embed.play.hotmart.com/video/{self.video_id}/play"
        self.session.get.assert_called_once_with(embed_api_url, headers=ANY)
        
        # Verify the URL was returned
        assert url == "https://example.com/video.m3u8"

    def test_extract_from_embed_page(self):
        """Test extracting token from embed page and constructing URL."""
        # Reset mock
        self.session.get.reset_mock()
        
        # Test the _try_extract_from_embed_page method
        with patch('url_extractor.extract_auth_token') as mock_extract:
            mock_extract.return_value = "hdntl=exp=1234567890~acl=/*~data=hdntl~hmac=abc123"
            
            url = URLExtractor._try_extract_from_embed_page(self.video_id, self.session)
            
            # Verify the correct URL was called
            embed_url = f"{HOTMART_EMBED_BASE}/{self.video_id}"
            self.session.get.assert_called_once_with(embed_url, headers=ANY)
            
            # Verify token extraction was attempted
            mock_extract.assert_called_once_with(self.session.get.return_value.text)
            
            # Verify URL construction
            assert "12345" in url
            assert "hdntl=exp=1234567890~acl=/*~data=hdntl~hmac=abc123" in url

    def test_get_url_from_api_tries_all_methods(self):
        """Test that get_url_from_api tries all methods in sequence."""
        # Make all methods return None except the last one
        with patch.object(URLExtractor, '_try_jwt_token_api_endpoint', return_value=None) as mock_jwt:
            with patch.object(URLExtractor, '_try_player_api', return_value=None) as mock_player:
                with patch.object(URLExtractor, '_try_club_api', return_value=None) as mock_club:
                    with patch.object(URLExtractor, '_try_embed_api', return_value=None) as mock_embed:
                        with patch.object(URLExtractor, '_try_extract_from_embed_page', return_value="https://final.url") as mock_extract:
                            
                            url = URLExtractor.get_url_from_api(self.video_id, self.session, self.jwt_token)
                            
                            # Verify all methods were called in sequence
                            mock_jwt.assert_called_once_with(self.video_id, self.session, self.jwt_token)
                            mock_player.assert_called_once_with(self.video_id, self.session)
                            mock_club.assert_called_once_with(self.video_id, self.session)
                            mock_embed.assert_called_once_with(self.video_id, self.session)
                            mock_extract.assert_called_once_with(self.video_id, self.session)
                            
                            # Verify the final URL was returned
                            assert url == "https://final.url"

    def test_get_url_from_api_returns_first_success(self):
        """Test that get_url_from_api returns the first successful result."""
        # Make the second method succeed
        with patch.object(URLExtractor, '_try_jwt_token_api_endpoint', return_value=None) as mock_jwt:
            with patch.object(URLExtractor, '_try_player_api', return_value="https://player.url") as mock_player:
                with patch.object(URLExtractor, '_try_club_api', return_value="https://should.not.reach") as mock_club:
                    
                    url = URLExtractor.get_url_from_api(self.video_id, self.session, self.jwt_token)
                    
                    # Verify first two methods were called
                    mock_jwt.assert_called_once_with(self.video_id, self.session, self.jwt_token)
                    mock_player.assert_called_once_with(self.video_id, self.session)
                    
                    # Verify the club API was not called since player API succeeded
                    mock_club.assert_not_called()
                    
                    # Verify the player API URL was returned
                    assert url == "https://player.url"

    def test_get_url_from_api_handles_exception(self):
        """Test that get_url_from_api handles exceptions properly."""
        # Make a method raise an exception
        with patch.object(URLExtractor, '_try_jwt_token_api_endpoint', side_effect=Exception("API error")) as mock_jwt:
            with patch('logger.error') as mock_log_error:
                url = URLExtractor.get_url_from_api(self.video_id, self.session, self.jwt_token)
                
                # Verify the error was logged
                mock_log_error.assert_called_once()
                
                # Verify None was returned on error
                assert url is None
                
    def test_extract_from_embed_page_error(self):
        """Test error handling in extract from embed page."""
        # Reset mock
        self.session.get.reset_mock()
        
        # Test with HTTP error
        self.session.get.return_value.status_code = 404
        with patch('url_extractor.extract_auth_token') as mock_extract:
            mock_extract.return_value = None
            url = URLExtractor._try_extract_from_embed_page(self.video_id, self.session)
            assert url is None
            
        # Test with token extraction failure
        self.session.get.return_value.status_code = 200
        with patch('url_extractor.extract_auth_token') as mock_extract:
            mock_extract.return_value = None
            url = URLExtractor._try_extract_from_embed_page(self.video_id, self.session)
            assert url is None