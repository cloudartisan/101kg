"""
URL Extractor Module for Hotmart Video Downloads

This module contains the functionality to extract video URLs from Hotmart's video player.
It's separated to make the code more maintainable and to preserve working URL extraction logic.
"""
import requests

class URLExtractor:
    @staticmethod
    def get_extraction_script():
        """
        Returns the JavaScript code that intercepts network requests to find video URLs.
        
        This script:
        1. Intercepts fetch requests
        2. Looks for video URLs from the Hotmart CDN
        3. Extracts and constructs proper m3u8 URLs with auth tokens
        
        Returns:
            str: JavaScript code as a string
        """
        return """
        return new Promise((resolve) => {
            console.log('Starting URL extraction script...');
            let foundUrl = null;
            let allUrls = [];
            let masterUrl = null;
            let videoId = null;
            let authToken = null;
            let jwtToken = null;
            
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
            
            // Look for auth token in the page
            try {
                console.log('Searching for auth token in page...');
                const pageContent = document.documentElement.innerHTML;
                
                // Look for hdntl token with the specific format from examples
                const hdntlRegex = /hdntl=exp=[0-9]+~acl=\/\*~data=hdntl~hmac=[a-f0-9]+/g;
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
                        // Try to match the specific format from examples
                        const hdntlRegex = /hdntl=exp=[0-9]+~acl=\/\*~data=hdntl~hmac=[a-f0-9]+/g;
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
                                const hdntlRegex = /hdntl=exp=[0-9]+~acl=\/\*~data=hdntl~hmac=[a-f0-9]+/g;
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
    
    @staticmethod
    def extract_video_id_from_iframe(iframe_src):
        """
        Extracts the video ID from the iframe source URL.
        
        Args:
            iframe_src (str): The src attribute of the iframe
            
        Returns:
            str: The extracted video ID
        """
        try:
            return iframe_src.split('/embed/')[1].split('?')[0]
        except (IndexError, AttributeError):
            return None
    
    @staticmethod
    def process_extraction_result(result, session=None):
        """
        Process the result from the JavaScript extraction.
        
        Args:
            result (dict): The result from executing the JavaScript
            session (requests.Session, optional): Session with authentication cookies
            
        Returns:
            list: List of tuples (part_suffix, video_url)
        """
        video_urls = []
        
        if isinstance(result, dict):
            # Print all URLs for debugging
            print(f"Found {len(result.get('allUrls', []))} URLs in network requests")
            for url in result.get('allUrls', []):
                print(f"  {url}")
                
            # Add the found URL if available (highest priority)
            if result.get('foundUrl'):
                print(f"\nFound URL with auth token: {result['foundUrl']}")
                video_urls.append(("", result['foundUrl']))
                return video_urls
                
            # If we have video ID and auth token, construct a URL
            elif result.get('videoId') and result.get('authToken'):
                video_id = result['videoId']
                auth_token = result['authToken']
                url = f"https://vod-akm.play.hotmart.com/video/{video_id}/hls/{video_id}-audio=2756-video=2292536.m3u8?{auth_token}"
                print(f"\nConstructed URL with video ID and auth token: {url}")
                video_urls.append(("", url))
                return video_urls
                
            # If we have video ID and JWT token, try to get the URL from the API
            elif result.get('videoId') and result.get('jwtToken') and session:
                video_id = result['videoId']
                jwt_token = result['jwtToken']
                print(f"\nTrying to get URL using JWT token and video ID: {video_id}")
                
                # Use the get_url_from_api method with the JWT token
                api_url = URLExtractor.get_url_from_api(video_id, session, jwt_token)
                if api_url:
                    print(f"Successfully retrieved URL from API: {api_url}")
                    video_urls.append(("", api_url))
                    return video_urls
                
            # Fallback to master playlist if available
            elif result.get('masterUrl'):
                print(f"\nUsing master playlist as fallback: {result['masterUrl']}")
                video_urls.append(("", result['masterUrl']))
                return video_urls
                
            # Last resort: try to get URL via API if we have video ID and session
            elif result.get('videoId') and session:
                print(f"\nAttempting to get URL via API for video ID: {result['videoId']}")
                api_url = URLExtractor.get_url_from_api(result['videoId'], session)
                if api_url:
                    print(f"Successfully retrieved URL from API: {api_url}")
                    video_urls.append(("", api_url))
                    return video_urls
                    
            # If we still don't have a URL but have a video ID, try a direct construction
            elif result.get('videoId'):
                video_id = result['videoId']
                # Try a simpler URL format as absolute last resort
                direct_url = f"https://vod-akm.play.hotmart.com/video/{video_id}/hls/{video_id}-audio=2756-video=2292536.m3u8"
                print(f"\nConstructing direct URL from video ID (last resort): {direct_url}")
                video_urls.append(("", direct_url))
                
        return video_urls
    
    @staticmethod
    def get_url_from_api(video_id, session, jwt_token=None):
        """
        Attempt to get the video URL directly from the Hotmart API.
        
        Args:
            video_id (str): The video ID
            session (requests.Session): Session with authentication cookies
            jwt_token (str, optional): JWT token for authentication
            
        Returns:
            str: The video URL if successful, None otherwise
        """
        try:
            # If we have a JWT token, try to use it first
            if jwt_token:
                print(f"Trying to get URL using JWT token for video ID: {video_id}")
                jwt_api_url = f"https://cf-embed.play.hotmart.com/video/{video_id}/play?jwt={jwt_token}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Origin': 'https://cf-embed.play.hotmart.com',
                    'Referer': f'https://cf-embed.play.hotmart.com/embed/{video_id}'
                }
                
                response = session.get(jwt_api_url, headers=headers)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if 'url' in data:
                            print(f"Got URL using JWT token: {data['url']}")
                            return data['url']
                    except:
                        print("Failed to parse JWT API response")
            
            # First try the player API
            player_api_url = f"https://api-player.hotmart.com/v1/content/video/{video_id}/play"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
                'Accept': 'application/json',
                'Origin': 'https://cf-embed.play.hotmart.com',
                'Referer': 'https://cf-embed.play.hotmart.com/'
            }
            
            response = session.get(player_api_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if 'url' in data:
                    print(f"Got URL from player API: {data['url']}")
                    return data['url']
            
            # Then try the club API
            club_api_url = f"https://api-club.hotmart.com/hot-club-api/rest/v3/content/video/{video_id}/play"
            response = session.get(club_api_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if 'url' in data:
                    print(f"Got URL from club API: {data['url']}")
                    return data['url']
            
            # Try the direct embed API
            embed_api_url = f"https://cf-embed.play.hotmart.com/video/{video_id}/play"
            response = session.get(embed_api_url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
                'Accept': 'application/json',
                'Origin': 'https://cf-embed.play.hotmart.com',
                'Referer': f'https://cf-embed.play.hotmart.com/embed/{video_id}'
            })
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'url' in data:
                        print(f"Got URL from embed API: {data['url']}")
                        return data['url']
                except:
                    print("Failed to parse embed API response")
            
            # Try to get the token from the embed page
            embed_url = f"https://cf-embed.play.hotmart.com/embed/{video_id}"
            response = session.get(embed_url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml',
                'Referer': 'https://101karategames.club.hotmart.com/'
            })
            
            if response.status_code == 200:
                content = response.text
                if 'hdntl=' in content:
                    print("Found hdntl token in embed page")
                    token_start = content.find('hdntl=')
                    if token_start > 0:
                        token_end = content.find('"', token_start)
                        if token_end < 0:
                            token_end = content.find("'", token_start)
                        if token_end > 0:
                            token = content[token_start:token_end]
                            url = f"https://vod-akm.play.hotmart.com/video/{video_id}/hls/{video_id}-audio=2756-video=2292536.m3u8?{token}"
                            print(f"Constructed URL with token from embed page: {url}")
                            return url
            
            return None
        except Exception as e:
            print(f"Error getting URL from API: {str(e)}")
            return None