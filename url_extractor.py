"""
URL Extractor Module for Hotmart Video Downloads

This module contains the functionality to extract video URLs from Hotmart's video player.
It's separated to make the code more maintainable and to preserve working URL extraction logic.
"""
import re
import requests
from url_utils import (
    HOTMART_CDN_BASE, 
    HOTMART_EMBED_BASE, 
    HOTMART_PLAYER_API, 
    HOTMART_CLUB_API,
    DEFAULT_HEADERS,
    HDNTL_PATTERN,
    extract_video_id_from_iframe,
    extract_auth_token,
    extract_jwt_token,
    construct_video_url,
    construct_embed_url,
    get_api_headers
)


class URLExtractor:
    """
    Class for extracting video URLs from Hotmart's platform.
    Contains methods for JavaScript injection, API calls, and URL construction.
    """
    
    @staticmethod
    def get_extraction_script():
        """
        Returns the JavaScript code that intercepts network requests to find video URLs.
        
        This script:
        1. Intercepts fetch and XMLHttpRequest requests
        2. Looks for video URLs from the Hotmart CDN
        3. Extracts and constructs proper m3u8 URLs with auth tokens
        
        Returns:
            str: JavaScript code as a string
        """
        script_parts = []
        script_parts.append(URLExtractor._get_script_initialization())
        script_parts.append(URLExtractor._get_token_extraction_script())
        script_parts.append(URLExtractor._get_video_id_extraction_script())
        script_parts.append(URLExtractor._get_jwt_token_handling_script())
        script_parts.append(URLExtractor._get_network_interception_script())
        script_parts.append(URLExtractor._get_url_processing_script())
        script_parts.append(URLExtractor._get_video_source_script())
        script_parts.append(URLExtractor._get_trigger_video_script())
        script_parts.append(URLExtractor._get_resolution_script())
        
        return "\n".join(script_parts)
    
    @staticmethod
    def _get_script_initialization():
        """Initialize the promise and variables."""
        return """
        return new Promise((resolve) => {
            console.log('Starting URL extraction script...');
            let foundUrl = null;
            let allUrls = [];
            let masterUrl = null;
            let videoId = null;
            let authToken = null;
            let jwtToken = null;
        """
    
    @staticmethod
    def _get_token_extraction_script():
        """Extract JWT token from the URL if available."""
        return """
            // Try to get JWT token from URL
            try {
                console.log('Checking URL for JWT token...');
                const urlParams = new URLSearchParams(window.location.search);
                if (urlParams.has('jwt')) {
                    jwtToken = urlParams.get('jwt');
                    console.log('Found JWT token in URL:', jwtToken);
                }
            } catch (e) {
                console.error('Error getting JWT token from URL:', e);
            }
        """
    
    @staticmethod
    def _get_video_id_extraction_script():
        """Extract video ID from the page."""
        return """
            // Try to get video ID from the page
            try {
                const videoElement = document.querySelector('video');
                if (videoElement) {
                    console.log('Found video element:', videoElement);
                    if (videoElement.dataset && videoElement.dataset.videoId) {
                        videoId = videoElement.dataset.videoId;
                        console.log('Found video ID from video element:', videoId);
                    }
                    
                    // Try to play the video to trigger requests
                    console.log('Attempting to play video...');
                    videoElement.currentTime = 0;
                    videoElement.play().catch(e => console.log('Play error:', e));
                    
                    // Try to get the source directly
                    if (videoElement.src) {
                        console.log('Video has direct source:', videoElement.src);
                        if (videoElement.src.includes('vod-akm.play.hotmart.com')) {
                            allUrls.push(videoElement.src);
                            processUrl(videoElement.src);
                        }
                    }
                } else {
                    console.log('No video element found on page');
                }
            } catch (e) {
                console.error('Error getting video ID from page:', e);
            }
        """
    
    @staticmethod
    def _get_jwt_token_handling_script():
        """Handle JWT token direct API call if available."""
        return """
            // If we have JWT token and video ID, try to get the URL directly
            if (jwtToken && videoId) {
                console.log('Trying to get URL using JWT token and video ID...');
                
                // Make a direct fetch request to the API
                fetch(`https://cf-embed.play.hotmart.com/video/${videoId}/play?jwt=${jwtToken}`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data && data.url) {
                        console.log('Got URL from API using JWT token:', data.url);
                        foundUrl = data.url;
                        allUrls.push(data.url);
                        processUrl(data.url);
                    }
                })
                .catch(error => {
                    console.error('Error fetching URL with JWT token:', error);
                });
            }
        """
    
    @staticmethod
    def _get_network_interception_script():
        """Set up network request interception."""
        return """
            // Look for auth token in the page
            try {
                console.log('Searching for auth token in page...');
                const pageContent = document.documentElement.innerHTML;
                
                // Look for hdntl token with the specific format from examples (same as HDNTL_PATTERN in url_utils.py)
                const hdntlRegex = /hdntl=exp=[0-9]+~acl=[/][*]~data=hdntl~hmac=[a-f0-9]+/g;
                const hdntlMatches = pageContent.match(hdntlRegex);
                
                if (hdntlMatches && hdntlMatches.length > 0) {
                    authToken = hdntlMatches[0];
                    console.log('Found hdntl token with regex:', authToken);
                } else if (pageContent.includes('hdntl=')) {
                    console.log('Found hdntl in page content');
                    // Try to extract with a more general approach
                    const tokenMatch = pageContent.match(/hdntl=([^&"'\\s]+)/);
                    if (tokenMatch && tokenMatch[0]) {
                        authToken = tokenMatch[0];
                        console.log('Extracted auth token:', authToken);
                    }
                }
            } catch (e) {
                console.error('Error searching for auth token:', e);
            }
            
            // Check network requests for tokens
            try {
                console.log('Checking performance entries for auth tokens...');
                const entries = performance.getEntries();
                for (const entry of entries) {
                    if (entry.name && entry.name.includes('hdntl=')) {
                        console.log('Found entry with hdntl:', entry.name);
                        allUrls.push(entry.name);
                        processUrl(entry.name);
                    }
                }
            } catch (e) {
                console.error('Error checking performance entries:', e);
            }
            
            // Intercept XMLHttpRequest
            const origXHROpen = XMLHttpRequest.prototype.open;
            const origXHRSend = XMLHttpRequest.prototype.send;
            
            XMLHttpRequest.prototype.open = function() {
                this._url = arguments[1];
                return origXHROpen.apply(this, arguments);
            };
            
            XMLHttpRequest.prototype.send = function() {
                const url = this._url;
                if (url && typeof url === 'string' && url.includes('vod-akm.play.hotmart.com')) {
                    console.log('XHR intercepted:', url);
                    allUrls.push(url);
                    
                    // Process URL same as fetch
                    processUrl(url);
                }
                return origXHRSend.apply(this, arguments);
            };
            
            // Intercept fetch
            const origFetch = window.fetch;
            window.fetch = function() {
                const url = arguments[0];
                if (url && typeof url === 'string' && url.includes('vod-akm.play.hotmart.com')) {
                    console.log('Fetch intercepted:', url);
                    allUrls.push(url);
                    
                    // Process URL
                    processUrl(url);
                }
                return origFetch.apply(this, arguments);
            };
        """
    
    @staticmethod
    def _get_url_processing_script():
        """Define the URL processing function."""
        return """
            // Function to process URLs
            function processUrl(url) {
                // Try to extract video ID from URL if not found yet
                if (!videoId && url) {
                    try {
                        const urlParts = url.split('/');
                        const videoIdIndex = urlParts.findIndex(part => part === 'video') + 1;
                        if (videoIdIndex > 0 && videoIdIndex < urlParts.length) {
                            videoId = urlParts[videoIdIndex];
                            console.log('Extracted video ID from URL:', videoId);
                        }
                    } catch (e) {
                        console.error('Error extracting video ID from URL:', e);
                    }
                }
                
                // Extract auth token if not found yet
                if (!authToken && url.includes('hdntl=')) {
                    try {
                        // Use the same pattern as defined in url_utils.py
                        const hdntlRegex = /hdntl=exp=[0-9]+~acl=[/][*]~data=hdntl~hmac=[a-f0-9]+/g;
                        const hdntlMatches = url.match(hdntlRegex);
                        
                        if (hdntlMatches && hdntlMatches.length > 0) {
                            authToken = hdntlMatches[0];
                            console.log('Extracted auth token with regex from URL:', authToken);
                        } else {
                            // Fallback to simpler extraction
                            const tokenMatch = url.match(/hdntl=([^&]+)/);
                            if (tokenMatch && tokenMatch[0]) {
                                authToken = tokenMatch[0];
                                console.log('Extracted auth token from URL:', authToken);
                            }
                        }
                    } catch (e) {
                        console.error('Error extracting auth token:', e);
                    }
                }
                
                // Store master playlist URL
                if (url.includes('/master') && url.includes('.m3u8')) {
                    console.log('Found master playlist URL:', url);
                    masterUrl = url;
                }
                
                // Look for m3u8 URLs directly first (highest priority)
                if (url.includes('.m3u8') && (url.includes('audio=') || url.includes('video=')) && !foundUrl) {
                    console.log('Found direct m3u8 URL:', url);
                    foundUrl = url;
                }
                // Fallback to .ts URLs if no m3u8 found
                else if (url.includes('.ts') && !foundUrl) {
                    try {
                        console.log('Attempting to convert .ts URL to m3u8:', url);
                        
                        // Extract the base part of the URL (before the segment number)
                        if (url.includes('-')) {
                            const baseUrl = url.substring(0, url.lastIndexOf('-'));
                            console.log('Base URL:', baseUrl);
                            
                            // Extract auth token from URL
                            let urlAuthToken = '';
                            if (url.includes('hdntl=')) {
                                // Try to match the specific format from examples
                                const hdntlRegex = /hdntl=exp=[0-9]+~acl=[/][*]~data=hdntl~hmac=[a-f0-9]+/g;
                                const hdntlMatches = url.match(hdntlRegex);
                                
                                if (hdntlMatches && hdntlMatches.length > 0) {
                                    urlAuthToken = hdntlMatches[0];
                                } else {
                                    urlAuthToken = 'hdntl=' + url.split('hdntl=')[1].split('&')[0];
                                }
                            } else if (url.includes('hdnts=')) {
                                urlAuthToken = 'hdnts=' + url.split('hdnts=')[1].split('&')[0];
                            }
                            
                            if (urlAuthToken) {
                                authToken = urlAuthToken;  // Save for later use
                                const m3u8Url = `${baseUrl}.m3u8?${urlAuthToken}`;
                                console.log('Constructed m3u8 URL:', m3u8Url);
                                foundUrl = m3u8Url;
                            }
                        }
                    } catch (e) {
                        console.error('Error constructing URL:', e);
                    }
                }
            }
        """
    
    @staticmethod
    def _get_video_source_script():
        """Search for video sources directly."""
        return """
            // Also try to find video sources directly
            try {
                const videoSources = document.querySelectorAll('video source');
                console.log('Found video sources:', videoSources.length);
                videoSources.forEach(source => {
                    const sourceUrl = source.src;
                    console.log('Video source URL:', sourceUrl);
                    if (sourceUrl && sourceUrl.includes('vod-akm.play.hotmart.com')) {
                        allUrls.push(sourceUrl);
                        processUrl(sourceUrl);
                    }
                });
            } catch (e) {
                console.error('Error finding video sources:', e);
            }
        """
    
    @staticmethod
    def _get_trigger_video_script():
        """Try to trigger video loading by clicking play buttons."""
        return """
            // Try to trigger video loading by clicking play buttons
            try {
                const playButtons = document.querySelectorAll('.play-button, button[aria-label="Play"], [role="button"][aria-label="Play"]');
                console.log('Found play buttons:', playButtons.length);
                playButtons.forEach(button => {
                    try {
                        console.log('Clicking play button');
                        button.click();
                    } catch (e) {
                        console.error('Error clicking play button:', e);
                    }
                });
            } catch (e) {
                console.error('Error finding play buttons:', e);
            }
        """
    
    @staticmethod
    def _get_resolution_script():
        """Resolve and return the final result."""
        return """
            // Resolve after timeout with all collected URLs
            setTimeout(() => {
                console.log('URL extraction timeout reached');
                console.log('Found URL:', foundUrl);
                console.log('Master URL:', masterUrl);
                console.log('Video ID:', videoId);
                console.log('Auth Token:', authToken);
                console.log('JWT Token:', jwtToken);
                console.log('All URLs:', allUrls.length);
                
                // If we have video ID and auth token but no direct URL, construct one
                if (videoId && authToken && !foundUrl) {
                    console.log('Constructing URL from video ID and auth token');
                    // This matches the format in url_utils.construct_video_url()
                    foundUrl = `https://vod-akm.play.hotmart.com/video/${videoId}/hls/${videoId}-audio=2756-video=2292536.m3u8?${authToken}`;
                    console.log('Constructed URL:', foundUrl);
                }
                
                resolve({
                    foundUrl, 
                    masterUrl,
                    videoId,
                    authToken,
                    jwtToken,
                    allUrls
                });
            }, 8000);  // Increased timeout for more time to capture requests
        });
        """
    
    # Use the function from url_utils instead
    extract_video_id_from_iframe = staticmethod(extract_video_id_from_iframe)
    
    @staticmethod
    def process_extraction_result(result, session=None):
        """
        Process the result from the JavaScript extraction to get video URLs.
        
        This method tries multiple approaches in order of preference:
        1. Use the found URL if available
        2. Construct URL from video ID and auth token
        3. Get URL from API using JWT token
        4. Use master playlist as fallback
        5. Try API with video ID
        6. Construct direct URL as last resort
        
        Args:
            result (dict): The result from executing the JavaScript
            session (requests.Session, optional): Session with authentication cookies
            
        Returns:
            list: List of tuples (part_suffix, video_url)
        """
        video_urls = []
        
        if not isinstance(result, dict):
            return video_urls
            
        # Print all URLs for debugging
        print(f"Found {len(result.get('allUrls', []))} URLs in network requests")
        for url in result.get('allUrls', []):
            print(f"  {url}")
            
        # Try different approaches in order of preference
        if URLExtractor._try_found_url(result, video_urls):
            return video_urls
            
        if URLExtractor._try_construct_from_id_and_token(result, video_urls):
            return video_urls
            
        if URLExtractor._try_jwt_token_api(result, session, video_urls):
            return video_urls
            
        if URLExtractor._try_master_playlist(result, video_urls):
            return video_urls
            
        if URLExtractor._try_api_with_video_id(result, session, video_urls):
            return video_urls
            
        # Last resort: direct URL construction
        if result.get('videoId'):
            URLExtractor._construct_direct_url(result['videoId'], video_urls)
            
        return video_urls
    
    @staticmethod
    def _try_found_url(result, video_urls):
        """Try to use the found URL from extraction result."""
        if result.get('foundUrl'):
            print(f"\nFound URL with auth token: {result['foundUrl']}")
            video_urls.append(("", result['foundUrl']))
            return True
        return False
    
    @staticmethod
    def _try_construct_from_id_and_token(result, video_urls):
        """Try to construct URL from video ID and auth token."""
        if result.get('videoId') and result.get('authToken'):
            video_id = result['videoId']
            auth_token = result['authToken']
            url = construct_video_url(video_id, auth_token)
            print(f"\nConstructed URL with video ID and auth token: {url}")
            video_urls.append(("", url))
            return True
        return False
    
    @staticmethod
    def _try_jwt_token_api(result, session, video_urls):
        """Try to get URL from API using JWT token."""
        if result.get('videoId') and result.get('jwtToken') and session:
            video_id = result['videoId']
            jwt_token = result['jwtToken']
            print(f"\nTrying to get URL using JWT token and video ID: {video_id}")
            
            # Use the get_url_from_api method with the JWT token
            api_url = URLExtractor.get_url_from_api(video_id, session, jwt_token)
            if api_url:
                print(f"Successfully retrieved URL from API: {api_url}")
                video_urls.append(("", api_url))
                return True
        return False
    
    @staticmethod
    def _try_master_playlist(result, video_urls):
        """Try to use master playlist as fallback."""
        if result.get('masterUrl'):
            print(f"\nUsing master playlist as fallback: {result['masterUrl']}")
            video_urls.append(("", result['masterUrl']))
            return True
        return False
    
    @staticmethod
    def _try_api_with_video_id(result, session, video_urls):
        """Try to get URL via API if we have video ID and session."""
        if result.get('videoId') and session:
            print(f"\nAttempting to get URL via API for video ID: {result['videoId']}")
            api_url = URLExtractor.get_url_from_api(result['videoId'], session)
            if api_url:
                print(f"Successfully retrieved URL from API: {api_url}")
                video_urls.append(("", api_url))
                return True
        return False
    
    @staticmethod
    def _construct_direct_url(video_id, video_urls):
        """Construct a direct URL as last resort."""
        direct_url = construct_video_url(video_id)
        print(f"\nConstructing direct URL from video ID (last resort): {direct_url}")
        video_urls.append(("", direct_url))
        return True
    
    @staticmethod
    def get_url_from_api(video_id, session, jwt_token=None):
        """
        Attempt to get the video URL directly from the Hotmart API.
        
        This method tries multiple API endpoints in sequence:
        1. JWT token API (if token provided)
        2. Player API
        3. Club API
        4. Embed API
        5. Extract token from embed page
        
        Args:
            video_id (str): The video ID
            session (requests.Session): Session with authentication cookies
            jwt_token (str, optional): JWT token for authentication
            
        Returns:
            str: The video URL if successful, None otherwise
        """
        try:
            # Try JWT token approach
            if jwt_token:
                url = URLExtractor._try_jwt_token_api_endpoint(video_id, session, jwt_token)
                if url:
                    return url
            
            # Try player API
            url = URLExtractor._try_player_api(video_id, session)
            if url:
                return url
                
            # Try club API
            url = URLExtractor._try_club_api(video_id, session)
            if url:
                return url
                
            # Try embed API
            url = URLExtractor._try_embed_api(video_id, session)
            if url:
                return url
                
            # Try to extract token from embed page
            url = URLExtractor._try_extract_from_embed_page(video_id, session)
            if url:
                return url
            
            return None
        except Exception as e:
            print(f"Error getting URL from API: {str(e)}")
            return None
    
    @staticmethod
    def _try_jwt_token_api_endpoint(video_id, session, jwt_token):
        """Try to get URL using JWT token API endpoint."""
        print(f"Trying to get URL using JWT token for video ID: {video_id}")
        jwt_api_url = f"https://cf-embed.play.hotmart.com/video/{video_id}/play?jwt={jwt_token}"
        headers = get_api_headers(video_id)
        
        response = session.get(jwt_api_url, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()
                if 'url' in data:
                    print(f"Got URL using JWT token: {data['url']}")
                    return data['url']
            except:
                print("Failed to parse JWT API response")
        return None
    
    @staticmethod
    def _try_player_api(video_id, session):
        """Try to get URL using player API."""
        player_api_url = f"{HOTMART_PLAYER_API}/{video_id}/play"
        response = session.get(player_api_url, headers=DEFAULT_HEADERS)
        if response.status_code == 200:
            data = response.json()
            if 'url' in data:
                print(f"Got URL from player API: {data['url']}")
                return data['url']
        return None
    
    @staticmethod
    def _try_club_api(video_id, session):
        """Try to get URL using club API."""
        club_api_url = f"{HOTMART_CLUB_API}/{video_id}/play"
        response = session.get(club_api_url, headers=DEFAULT_HEADERS)
        if response.status_code == 200:
            data = response.json()
            if 'url' in data:
                print(f"Got URL from club API: {data['url']}")
                return data['url']
        return None
    
    @staticmethod
    def _try_embed_api(video_id, session):
        """Try to get URL using embed API."""
        embed_api_url = f"https://cf-embed.play.hotmart.com/video/{video_id}/play"
        headers = get_api_headers(video_id)
        
        response = session.get(embed_api_url, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()
                if 'url' in data:
                    print(f"Got URL from embed API: {data['url']}")
                    return data['url']
            except:
                print("Failed to parse embed API response")
        return None
    
    @staticmethod
    def _try_extract_from_embed_page(video_id, session):
        """Try to extract token from embed page and construct URL."""
        embed_url = construct_embed_url(video_id)
        response = session.get(embed_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Referer': 'https://101karategames.club.hotmart.com/'
        })
        
        if response.status_code == 200:
            content = response.text
            token = extract_auth_token(content)
            if token:
                print("Found hdntl token in embed page")
                url = construct_video_url(video_id, token)
                print(f"Constructed URL with token from embed page: {url}")
                return url
        return None