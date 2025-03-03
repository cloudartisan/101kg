"""
URL Utilities Module for Hotmart Video Downloads

This module contains shared utility functions for URL extraction, token handling,
and URL construction used by both URLExtractor and VideoDownloader classes.

This module was created to consolidate duplicate URL extraction code that
existed in both url_extractor.py and video_downloader.py, making the codebase
more maintainable and reducing inconsistencies between different approaches.
"""
import re


# Constants for URL patterns
HOTMART_CDN_BASE = "https://vod-akm.play.hotmart.com/video"
HOTMART_EMBED_BASE = "https://cf-embed.play.hotmart.com/embed"
HOTMART_PLAYER_API = "https://api-player.hotmart.com/v1/content/video"
HOTMART_CLUB_API = "https://api-club.hotmart.com/hot-club-api/rest/v3/content/video"

# Common headers for requests
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
    'Accept': 'application/json',
    'Origin': 'https://cf-embed.play.hotmart.com',
    'Referer': 'https://cf-embed.play.hotmart.com/'
}

# Regular expression patterns
HDNTL_PATTERN = r'hdntl=exp=[0-9]+~acl=[/][*]~data=hdntl~hmac=[a-f0-9]+'


def extract_video_id_from_iframe(iframe_src):
    """
    Extracts the video ID from the iframe source URL.

    Args:
        iframe_src (str): The src attribute of the iframe

    Returns:
        str: The extracted video ID, or None if not found
    """
    try:
        return iframe_src.split('/embed/')[1].split('?')[0]
    except (IndexError, AttributeError):
        return None


def extract_jwt_token(iframe_src):
    """
    Extract JWT token from iframe src if present.

    Args:
        iframe_src (str): The iframe source URL

    Returns:
        str: The JWT token if found, None otherwise
    """
    jwt_token = None
    if 'jwtToken=' in iframe_src:
        jwt_token = iframe_src.split('jwtToken=')[1].split('&')[0]
    elif 'jwt=' in iframe_src:
        jwt_token = iframe_src.split('jwt=')[1].split('&')[0]
    return jwt_token


def extract_auth_token(content):
    """
    Extract authentication token (hdntl) from content.

    Args:
        content (str): HTML content or URL containing the token

    Returns:
        str: The auth token if found, None otherwise
    """
    # Try to match specific regex pattern first
    matches = re.findall(HDNTL_PATTERN, content)
    if matches:
        return matches[0]

    # Fallback to simpler extraction
    if 'hdntl=' in content:
        token_start = content.find('hdntl=')
        if token_start > 0:
            token_end = content.find('"', token_start)
            if token_end < 0:
                token_end = content.find("'", token_start)
            if token_end < 0:
                token_end = content.find('&', token_start)
            if token_end > 0:
                return content[token_start:token_end]
            # If we can't find a delimiter, return the rest of the string
            return content[token_start:]

    return None


def construct_video_url(video_id, auth_token=None, quality="audio=2756-video=2292536"):
    """
    Construct a video URL with the given parameters.

    Args:
        video_id (str): The video ID
        auth_token (str, optional): Authentication token
        quality (str, optional): Video quality string

    Returns:
        str: The constructed video URL
    """
    base_url = f"{HOTMART_CDN_BASE}/{video_id}/hls/{video_id}-{quality}.m3u8"

    if auth_token:
        # If auth_token doesn't start with hdntl= or hdnts=, add hdntl= prefix
        if not auth_token.startswith('hdntl=') and not auth_token.startswith('hdnts='):
            auth_token = f"hdntl={auth_token}"
        return f"{base_url}?{auth_token}"

    return base_url


def construct_embed_url(video_id, jwt_token=None):
    """
    Construct an embed URL with optional JWT token.

    Args:
        video_id (str): The video ID
        jwt_token (str, optional): JWT token for authentication

    Returns:
        str: The constructed embed URL
    """
    embed_url = f"{HOTMART_EMBED_BASE}/{video_id}"
    if jwt_token:
        embed_url += f"?jwt={jwt_token}"
    return embed_url


def get_api_headers(video_id=None):
    """
    Get headers for API requests.

    Args:
        video_id (str, optional): The video ID for setting the referer

    Returns:
        dict: Headers dictionary
    """
    headers = DEFAULT_HEADERS.copy()
    if video_id:
        headers.update({
            'Content-Type': 'application/json',
            'Referer': f'{HOTMART_EMBED_BASE}/{video_id}'
        })
    return headers