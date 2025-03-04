"""
Tests for the url_utils module.
"""
import pytest
from url_utils import (
    extract_video_id_from_iframe,
    extract_jwt_token,
    extract_auth_token,
    construct_video_url,
    construct_embed_url,
    get_api_headers
)


class TestExtractVideoIdFromIframe:
    """Tests for extract_video_id_from_iframe function."""

    def test_valid_iframe_src(self):
        """Test extracting video ID from a valid iframe src."""
        iframe_src = "https://cf-embed.play.hotmart.com/embed/12345?param=value"
        video_id = extract_video_id_from_iframe(iframe_src)
        assert video_id == "12345"

    def test_iframe_src_without_embed(self):
        """Test with iframe src that doesn't contain 'embed'."""
        iframe_src = "https://cf-play.hotmart.com/12345?param=value"
        video_id = extract_video_id_from_iframe(iframe_src)
        assert video_id is None

    def test_empty_iframe_src(self):
        """Test with empty iframe src."""
        video_id = extract_video_id_from_iframe("")
        assert video_id is None

    def test_invalid_iframe_src(self):
        """Test with invalid iframe src."""
        video_id = extract_video_id_from_iframe("not a url")
        assert video_id is None

    def test_none_iframe_src(self):
        """Test with None iframe src."""
        video_id = extract_video_id_from_iframe(None)
        assert video_id is None


class TestExtractJwtToken:
    """Tests for extract_jwt_token function."""

    def test_jwt_token_with_jwt_param(self):
        """Test extracting JWT token with jwtToken parameter."""
        iframe_src = "https://cf-embed.play.hotmart.com/embed/12345?jwtToken=test_token&other=value"
        jwt_token = extract_jwt_token(iframe_src)
        assert jwt_token == "test_token"

    def test_jwt_token_with_jwt_param(self):
        """Test extracting JWT token with jwt parameter."""
        iframe_src = "https://cf-embed.play.hotmart.com/embed/12345?jwt=test_token&other=value"
        jwt_token = extract_jwt_token(iframe_src)
        assert jwt_token == "test_token"

    def test_no_jwt_token(self):
        """Test with no JWT token in the URL."""
        iframe_src = "https://cf-embed.play.hotmart.com/embed/12345?param=value"
        jwt_token = extract_jwt_token(iframe_src)
        assert jwt_token is None

    def test_empty_url(self):
        """Test with empty URL."""
        jwt_token = extract_jwt_token("")
        assert jwt_token is None


class TestExtractAuthToken:
    """Tests for extract_auth_token function."""

    def test_extract_using_regex_pattern(self, sample_content_with_auth_token):
        """Test extracting auth token using regex pattern."""
        token = extract_auth_token(sample_content_with_auth_token)
        assert token == "hdntl=exp=1234567890~acl=/*~data=hdntl~hmac=abc123"

    def test_extract_simple_hdntl_token(self):
        """Test extracting simple hdntl token."""
        content = "some content hdntl=simple_token more content"
        token = extract_auth_token(content)
        assert token == "hdntl=simple_token"

    def test_hdntl_with_quote_delimiter(self):
        """Test extracting hdntl token with quote delimiter."""
        content = 'some content hdntl=token_with_quotes" more content'
        token = extract_auth_token(content)
        assert token == "hdntl=token_with_quotes"

    def test_hdntl_with_single_quote_delimiter(self):
        """Test extracting hdntl token with single quote delimiter."""
        content = "some content hdntl=token_with_single_quotes' more content"
        token = extract_auth_token(content)
        assert token == "hdntl=token_with_single_quotes"

    def test_hdntl_with_ampersand_delimiter(self):
        """Test extracting hdntl token with ampersand delimiter."""
        content = "some content hdntl=token_with_ampersand&more=content"
        token = extract_auth_token(content)
        assert token == "hdntl=token_with_ampersand"

    def test_hdntl_without_delimiter(self):
        """Test extracting hdntl token without delimiter."""
        content = "some content hdntl=token_without_delimiter"
        token = extract_auth_token(content)
        assert token == "hdntl=token_without_delimiter"

    def test_no_hdntl_token(self):
        """Test with no hdntl token in the content."""
        content = "some content without token"
        token = extract_auth_token(content)
        assert token is None


class TestConstructVideoUrl:
    """Tests for construct_video_url function."""

    def test_construct_with_auth_token_hdntl_prefix(self):
        """Test constructing video URL with auth token that has hdntl prefix."""
        video_id = "12345"
        auth_token = "hdntl=test_token"
        quality = "audio=2756-video=2292536"
        url = construct_video_url(video_id, auth_token, quality)
        assert url == f"https://vod-akm.play.hotmart.com/video/{video_id}/hls/{video_id}-{quality}.m3u8?{auth_token}"

    def test_construct_with_auth_token_no_prefix(self):
        """Test constructing video URL with auth token that has no prefix."""
        video_id = "12345"
        auth_token = "test_token"
        quality = "audio=2756-video=2292536"
        url = construct_video_url(video_id, auth_token, quality)
        assert url == f"https://vod-akm.play.hotmart.com/video/{video_id}/hls/{video_id}-{quality}.m3u8?hdntl={auth_token}"

    def test_construct_with_auth_token_hdnts_prefix(self):
        """Test constructing video URL with auth token that has hdnts prefix."""
        video_id = "12345"
        auth_token = "hdnts=test_token"
        quality = "audio=2756-video=2292536"
        url = construct_video_url(video_id, auth_token, quality)
        assert url == f"https://vod-akm.play.hotmart.com/video/{video_id}/hls/{video_id}-{quality}.m3u8?{auth_token}"

    def test_construct_without_auth_token(self):
        """Test constructing video URL without auth token."""
        video_id = "12345"
        quality = "audio=2756-video=2292536"
        url = construct_video_url(video_id, None, quality)
        assert url == f"https://vod-akm.play.hotmart.com/video/{video_id}/hls/{video_id}-{quality}.m3u8"

    def test_construct_with_default_quality(self):
        """Test constructing video URL with default quality."""
        video_id = "12345"
        url = construct_video_url(video_id)
        assert "audio=2756-video=2292536" in url
        assert url == f"https://vod-akm.play.hotmart.com/video/{video_id}/hls/{video_id}-audio=2756-video=2292536.m3u8"


class TestConstructEmbedUrl:
    """Tests for construct_embed_url function."""

    def test_construct_with_jwt_token(self):
        """Test constructing embed URL with JWT token."""
        video_id = "12345"
        jwt_token = "test_jwt_token"
        url = construct_embed_url(video_id, jwt_token)
        assert url == f"https://cf-embed.play.hotmart.com/embed/{video_id}?jwt={jwt_token}"

    def test_construct_without_jwt_token(self):
        """Test constructing embed URL without JWT token."""
        video_id = "12345"
        url = construct_embed_url(video_id)
        assert url == f"https://cf-embed.play.hotmart.com/embed/{video_id}"


class TestGetApiHeaders:
    """Tests for get_api_headers function."""

    def test_headers_with_video_id(self):
        """Test getting API headers with video ID."""
        video_id = "12345"
        headers = get_api_headers(video_id)
        assert headers["Content-Type"] == "application/json"
        assert f"https://cf-embed.play.hotmart.com/embed/{video_id}" in headers["Referer"]

    def test_headers_without_video_id(self):
        """Test getting API headers without video ID."""
        headers = get_api_headers()
        assert "Content-Type" not in headers
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Origin" in headers
        assert "Referer" in headers