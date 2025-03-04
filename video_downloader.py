"""
Video Downloader Module for Hotmart Platform

This module provides the VideoDownloader class which handles authentication,
navigation, URL extraction, and video downloading from Hotmart platform.
"""
import os
import time
import requests
import m3u8
import ffmpeg
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from url_extractor import URLExtractor
from url_utils import (
    HOTMART_CDN_BASE,
    HOTMART_EMBED_BASE,
    HDNTL_PATTERN,
    extract_video_id_from_iframe,
    extract_jwt_token,
    extract_auth_token,
    construct_video_url,
    construct_embed_url
)
from browser_manager import BrowserManager

# Import the logger module
import logger
log = logger


class VideoDownloader:
    """
    Main class for downloading videos from Hotmart platform.
    Handles authentication, navigation, URL extraction, and video downloading.
    """

    def __init__(self, email, password, headless=False):
        """
        Initialize the downloader with user credentials.

        Args:
            email (str): User's email for Hotmart login
            password (str): User's password for Hotmart login
            headless (bool): Whether to run the browser in headless mode
        """
        # URLs and credentials
        self.base_url = "https://101karategames.club.hotmart.com"
        self.login_url = "https://101karategames.club.hotmart.com/login"
        self.email = email
        self.password = password

        # Setup download directory
        self.download_dir = "videos"
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        # Initialize HTTP session
        self.session = requests.Session()

        # Initialize browser manager
        self.browser_manager = BrowserManager(headless=headless)
        self.driver = self.browser_manager.initialize()

        if not self.driver:
            raise Exception("Failed to initialize browser")

    def login(self):
        """
        Login to Hotmart platform and transfer cookies to requests session.

        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            log.info("Navigating to login page")
            self.driver.get(self.login_url)
            wait = WebDriverWait(self.driver, 30)  # Increased timeout

            # Wait for page to load completely
            time.sleep(8)  # Increased wait time

            # Handle cookie policy popup if it exists
            self.browser_manager.handle_cookie_policy_popup()

            # Fill login form - use more generic selectors with better waits
            log.info("Filling login credentials")
            email_field = self.browser_manager.wait_for_element(
                By.CSS_SELECTOR, 
                "input[type='text'], input[type='email'], input.form-control",
                condition="clickable"
            )
            if not email_field:
                raise Exception("Email field not found")

            email_field.clear()
            email_field.send_keys(self.email)

            password_field = self.browser_manager.wait_for_element(
                By.CSS_SELECTOR, 
                "input[type='password']",
                condition="clickable"
            )
            if not password_field:
                raise Exception("Password field not found")

            password_field.clear()
            password_field.send_keys(self.password)

            # Make sure cookie popups are handled again before clicking
            self.browser_manager.handle_cookie_policy_popup()

            # Try different button selectors to handle possible variations
            log.info("Attempting to click login button")
            login_successful = False

            # First try the specific selector with JavaScript click to bypass any overlays
            login_button = self.browser_manager.wait_for_element(
                By.CSS_SELECTOR, 
                "button.btn-login[data-test='submit']"
            )
            if login_button:
                self.driver.execute_script("arguments[0].click();", login_button)
                login_successful = True

            # If first attempt failed, try generic selectors
            if not login_successful:
                log.debug("Could not find specific login button, trying alternative selectors")
                login_button = self.browser_manager.wait_for_element(
                    By.CSS_SELECTOR,
                    "button[type='submit'], button.btn-primary, button.login-button"
                )
                if login_button:
                    self.driver.execute_script("arguments[0].click();", login_button)
                    login_successful = True

            # If still failed, try by text content
            if not login_successful:
                log.debug("Still couldn't find login button, trying by XPath")
                login_button = self.browser_manager.wait_for_element(
                    By.XPATH,
                    "//button[contains(text(), 'Login') or contains(text(), 'Entrar') or contains(text(), 'Sign in')]"
                )
                if login_button:
                    self.driver.execute_script("arguments[0].click();", login_button)
                    login_successful = True

            if not login_successful:
                raise Exception("Could not find or click login button")

            # Wait for login to complete
            log.info("Waiting for login to complete")
            time.sleep(10)  # Increased wait time

            # Transfer cookies from Selenium to requests session
            self._transfer_cookies_to_session()
            log.info("Login successful")

            return True

        except Exception as e:
            log.error(f"Login failed: {str(e)}", exc_info=True)
            return False

    def _transfer_cookies_to_session(self):
        """Transfer cookies from Selenium to requests session."""
        for cookie in self.driver.get_cookies():
            self.session.cookies.set(
                name=cookie['name'],
                value=cookie['value'],
                domain=cookie.get('domain', ''),
                path=cookie.get('path', '/')
            )

    def get_video_parts(self):
        """
        Get all video parts in the current lesson.

        Returns:
            list: List of video part elements, or empty list if none found
        """
        try:
            wait = WebDriverWait(self.driver, 10)
            parts = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.playlist-media"))
            )
            return parts
        except Exception:
            # Return empty list if no parts found (single video lesson)
            return []

    def get_video_url_from_api(self, video_id, jwt_token=None):
        """
        Try to get the video URL directly from the Hotmart API.

        Args:
            video_id (str): The video ID
            jwt_token (str, optional): JWT token for authentication

        Returns:
            str: The video URL if successful, None otherwise
        """
        try:
            log.debug(f"Attempting to get video URL from API for video ID: {video_id}")

            # Use the URLExtractor's get_url_from_api method
            result = URLExtractor.get_url_from_api(video_id, self.session, jwt_token)
            if result:
                log.debug(f"API returned URL: {result[:100]}...")
            else:
                log.debug("API did not return a URL")
            return result

        except Exception as e:
            log.error(f"Error getting URL from API: {str(e)}", exc_info=True)
            return None

    def extract_video_url(self, lesson_url):
        """
        Extract video URL(s) from lesson page.

        Args:
            lesson_url (str): URL of the lesson page

        Returns:
            list: List of tuples (part_suffix, video_url)
        """
        try:
            log.info(f"Navigating to lesson page: {lesson_url}")
            self.driver.get(lesson_url)
            time.sleep(8)  # Increased wait time for page to fully load

            video_urls = []
            wait = WebDriverWait(self.driver, 15)

            # Find the iframe
            log.info("Looking for video iframe in page")
            iframe = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='cf-embed.play.hotmart.com']"))
            )

            # Extract video ID and JWT token from iframe src
            iframe_src = iframe.get_attribute('src')
            log.info(f"Found iframe with src")
            log.debug(f"Iframe src: {iframe_src[:100]}...")

            video_id = URLExtractor.extract_video_id_from_iframe(iframe_src)
            log.debug(f"Found video ID: {video_id}")

            if not video_id:
                log.error("Failed to extract video ID from iframe src")
                return []

            # Extract JWT token if present
            jwt_token = self._extract_jwt_token(iframe_src)

            # Try different methods to get the video URL
            video_urls = self._try_jwt_token_approach(video_id, jwt_token)
            if video_urls:
                return video_urls

            video_urls = self._try_api_approach(video_id, jwt_token)
            if video_urls:
                return video_urls

            video_urls = self._try_javascript_extraction(lesson_url, video_id, jwt_token)
            if video_urls:
                return video_urls

            video_urls = self._try_direct_embed_approach(video_id, jwt_token, lesson_url)
            if video_urls:
                return video_urls

            video_urls = self._try_network_requests_approach(video_id, jwt_token)
            if video_urls:
                return video_urls

            return []

        except Exception as e:
            error_msg = str(e).split('\n')[0] if str(e) else "Unknown error"
            log.error(f"Failed to load lesson page: {error_msg}", exc_info=True)
            return []

    def _extract_jwt_token(self, iframe_src):
        """Extract JWT token from iframe src if present."""
        jwt_token = extract_jwt_token(iframe_src)
        if jwt_token:
            log.debug("Found JWT token in iframe src, might help with authentication")
            log.debug(f"JWT token: {jwt_token[:15]}...")
        return jwt_token

    def _try_jwt_token_approach(self, video_id, jwt_token):
        """Try to get video URL using JWT token."""
        if not jwt_token:
            return []

        video_urls = []

        # Try to get the video directly using the JWT token as authentication
        log.debug("Trying to use JWT token to get a direct URL")
        direct_jwt_url = f"https://cf-embed.play.hotmart.com/video/{video_id}/play?jwt={jwt_token}"
        log.debug(f"JWT direct URL: {direct_jwt_url[:80]}...")
        response = self.session.get(direct_jwt_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
            'Accept': 'application/json',
            'Origin': 'https://cf-embed.play.hotmart.com',
            'Referer': f'{HOTMART_EMBED_BASE}/{video_id}'
        })

        if response.status_code == 200:
            try:
                data = response.json()
                if 'url' in data:
                    log.info("Successfully retrieved URL using JWT token")
                    log.debug(f"URL from JWT token: {data['url'][:100]}...")
                    video_urls.append(("", data['url']))
                    return video_urls
            except:
                pass

        # If direct API call fails, try to load the embed page with the JWT token
        log.info("Direct API call failed. Trying to load embed page with JWT token")
        embed_url = construct_embed_url(video_id, jwt_token)

        # Load the embed page in the browser to capture network requests
        log.debug(f"Loading embed page in browser for network request capture")
        self.driver.get(embed_url)
        time.sleep(5)  # Wait for page to load

        # Execute JavaScript to get all network requests
        script = """
        var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {};
        var network = performance.getEntries() || [];
        return network.filter(function(entry) {
            return entry.name.indexOf('vod-akm.play.hotmart.com') !== -1;
        }).map(function(entry) {
            return entry.name;
        });
        """

        network_requests = self.driver.execute_script(script)
        log.debug(f"Found {len(network_requests)} network requests to Hotmart CDN")

        # Look for m3u8 URLs with hdntl token
        for request in network_requests:
            log.debug(f"Network request found: {request[:100]}...")
            if 'hdntl=' in request and '.m3u8' in request:
                log.info("Found m3u8 URL with hdntl token")
                video_urls.append(("", request))
                return video_urls

        # If we didn't find a direct m3u8 URL, look for any URL with hdntl token
        for request in network_requests:
            if 'hdntl=' in request:
                log.debug("Found URL with hdntl token")
                log.debug(f"Token URL: {request[:100]}...")
                # Extract the hdntl token
                token = extract_auth_token(request)

                if token:
                    direct_url = construct_video_url(video_id, token)
                    log.info("Successfully constructed URL with token from network request")
                    log.debug(f"URL: {direct_url[:100]}...")
                    video_urls.append(("", direct_url))
                    return video_urls

        return []

    def _try_api_approach(self, video_id, jwt_token):
        """Try to get video URL using API methods."""
        log.info("Trying API method to get video URL")
        api_url = self.get_video_url_from_api(video_id, jwt_token)
        if api_url:
            log.info("Successfully retrieved URL from API")
            log.debug(f"Using API URL: {api_url[:100]}...")
            return [("", api_url)]
        return []

    def _try_javascript_extraction(self, lesson_url, video_id, jwt_token):
        """Try to extract video URL using JavaScript injection."""
        log.info("API method failed. Switching to iframe for JavaScript extraction")

        # Navigate back to the lesson page
        self.driver.get(lesson_url)
        time.sleep(5)

        # Handle any cookie policy popups before interacting with the page
        self.browser_manager.handle_cookie_policy_popup()

        # Find the iframe again
        wait = WebDriverWait(self.driver, 15)
        iframe = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='cf-embed.play.hotmart.com']"))
        )

        # Use JavaScript to ensure the iframe is visible and not covered by anything
        self.driver.execute_script("""
            // Make sure the iframe is fully visible and not covered by overlays
            var iframe = arguments[0];
            iframe.scrollIntoView({behavior: 'smooth', block: 'center'});

            // Remove any overlays that might cover the iframe
            var overlays = document.querySelectorAll('.overlay, .modal, .popup, .cookie-policy, #hotmart-cookie-policy');
            for (var i = 0; i < overlays.length; i++) {
                overlays[i].style.display = 'none';
                overlays[i].style.visibility = 'hidden';
                overlays[i].style.zIndex = -1;
            }
        """, iframe)

        # Wait a bit after removing overlays
        time.sleep(1)

        # Now switch to the iframe
        self.driver.switch_to.frame(iframe)

        # Use the extraction script from the URLExtractor module
        log.debug("Executing URL extraction script")
        script = URLExtractor.get_extraction_script()

        # Execute script and wait for URL
        result = self.driver.execute_script(script)

        # Add JWT token to the result if we have it
        if jwt_token and isinstance(result, dict) and 'jwtToken' not in result:
            result['jwtToken'] = jwt_token
            log.debug("Added JWT token to extraction result")

        log.debug("Processing extraction results")
        # Process the result using the URLExtractor, passing the session for API fallback
        video_urls = URLExtractor.process_extraction_result(result, self.session)

        # Switch back to main frame
        self.driver.switch_to.default_content()

        return video_urls

    def _try_direct_embed_approach(self, video_id, jwt_token, lesson_url):
        """Try to get video URL directly from the embed page."""
        log.info("No video URLs found using standard methods. Trying direct embed page approach")

        # Try to get the URL directly from the embed page
        embed_url = construct_embed_url(video_id, jwt_token)
        log.debug("Fetching embed page content directly")
        log.debug(f"Embed URL: {embed_url}")

        response = self.session.get(embed_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Referer': lesson_url
        })

        if response.status_code != 200:
            return []

        content = response.text
        video_urls = []

        # Try to find hdntl token using our extraction utility
        token = extract_auth_token(content)

        if token:
            log.debug("Found hdntl token in embed page content")
            log.debug(f"Token: {token[:50] if len(token) > 50 else token}...")
            direct_url = construct_video_url(video_id, token)
            log.info("Successfully constructed URL with token from embed page")
            log.debug(f"URL: {direct_url[:100]}...")
            video_urls.append(("", direct_url))
            return video_urls

        return []

    def _try_network_requests_approach(self, video_id, jwt_token):
        """Try to extract video URL from network requests."""
        log.info("Still no URL found. Trying to extract from network requests")

        # Navigate to the embed page directly
        embed_url = construct_embed_url(video_id, jwt_token)
        log.debug("Loading embed page in browser for network monitoring")
        log.debug(f"Embed URL: {embed_url}")

        self.driver.get(embed_url)
        time.sleep(5)  # Wait for page to load

        # Execute JavaScript to get network requests
        script = """
        var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {};
        var network = performance.getEntries() || [];
        return network.filter(function(entry) {
            return entry.name.indexOf('hdntl=') !== -1;
        }).map(function(entry) {
            return entry.name;
        });
        """

        network_requests = self.driver.execute_script(script)
        video_urls = []

        for request in network_requests:
            if 'hdntl=' in request:
                log.debug("Found network request with hdntl token")
                log.debug(f"Request: {request[:100]}...")
                # Extract the token
                token = extract_auth_token(request)

                if token:
                    log.debug(f"Extracted token: {token[:50] if len(token) > 50 else token}...")
                    direct_url = construct_video_url(video_id, token)
                    log.info("Successfully constructed URL with token from network request")
                    log.debug(f"URL: {direct_url[:100]}...")
                    video_urls.append(("", direct_url))
                    return video_urls

        return []

    def download_video(self, video_url, filename):
        """
        Download video from URL.

        Args:
            video_url (str): URL of the video to download
            filename (str): Filename to save the video as

        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            # Check if video is HLS stream
            if video_url.endswith('.m3u8'):
                log.info(f"Detected HLS stream format for {filename}")
                self._download_hls(video_url, filename)
            else:
                log.info(f"Detected MP4 format for {filename}")
                self._download_mp4(video_url, filename)
            return True

        except Exception as e:
            log.error(f"Download failed for {filename}: {str(e)}", exc_info=True)
            return False

    def _download_mp4(self, video_url, filename):
        """
        Download direct MP4 video.

        Args:
            video_url (str): URL of the MP4 video
            filename (str): Filename to save the video as
        """
        # Use authenticated session instead of direct requests
        headers = {
            'Origin': 'https://cf-embed.play.hotmart.com',
            'Referer': 'https://cf-embed.play.hotmart.com/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        log.debug(f"Downloading MP4 using authenticated session: {video_url[:100]}...")
        response = self.session.get(video_url, stream=True, headers=headers)
        
        if response.status_code != 200:
            log.error(f"MP4 download failed with status code: {response.status_code}")
            log.error(f"Response headers: {dict(response.headers)}")
            raise Exception(f"MP4 download failed: HTTP {response.status_code}")
            
        total_size = int(response.headers.get('content-length', 0))
        log.debug(f"Content length: {total_size} bytes")

        filepath = os.path.join(self.download_dir, f"{filename}.mp4")
        block_size = 1024  # 1 Kibibyte

        with open(filepath, 'wb') as file:
            for data in response.iter_content(block_size):
                file.write(data)
                
        log.info(f"MP4 download completed: {filepath}")

    def _download_hls(self, video_url, filename):
        """
        Download and convert HLS stream.

        Args:
            video_url (str): URL of the HLS stream
            filename (str): Filename to save the video as

        Raises:
            Exception: If download fails
        """
        try:
            log.info(f"Starting HLS stream download for {filename}")
            log.debug(f"HLS URL: {video_url[:100]}...")

            # Set headers based on what we saw in the network requests
            headers = {
                'Origin': 'https://cf-embed.play.hotmart.com',
                'Referer': 'https://cf-embed.play.hotmart.com/',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            # Use our session to load the playlist
            log.debug("Fetching M3U8 playlist")
            playlist_response = self.session.get(video_url, headers=headers)
            if not playlist_response.ok:
                log.error(f"Failed to load playlist: {playlist_response.status_code}")
                log.error(f"Response: {playlist_response.text}")
                raise Exception(f"Failed to load playlist: {playlist_response.status_code}")

            log.debug("Parsing M3U8 playlist")
            playlist = m3u8.loads(playlist_response.text)
            output_path = os.path.join(self.download_dir, f"{filename}.mp4")
            log.debug(f"Output path: {output_path}")

            # Extract auth token and cookies for ffmpeg
            headers_arg = self._prepare_ffmpeg_headers(video_url)

            # Try primary ffmpeg method
            try:
                log.debug("Using primary ffmpeg-python method for download")
                self._download_with_ffmpeg_python(video_url, output_path, headers_arg)
            except Exception as e:
                log.warning(f"Primary ffmpeg method failed: {str(e)}")
                log.debug("Falling back to ffmpeg subprocess method")
                self._download_with_ffmpeg_subprocess(video_url, output_path)

        except Exception as e:
            log.error(f"HLS download failed for {filename}: {str(e)}", exc_info=True)
            raise

    def _prepare_ffmpeg_headers(self, video_url):
        """Prepare headers for ffmpeg including cookies and auth token."""
        # Get cookies from session as string
        cookie_header = '; '.join([f"{c.name}={c.value}" for c in self.session.cookies])

        # Extract auth token from URL if present
        auth_header = ""
        if 'hdntl=' in video_url:
            auth_token = video_url.split('hdntl=')[1]
            if '&' in auth_token:
                auth_token = auth_token.split('&')[0]
            auth_header = f"'hdntl: {auth_token}'"
        elif 'hdnts=' in video_url:
            auth_token = video_url.split('hdnts=')[1]
            if '&' in auth_token:
                auth_token = auth_token.split('&')[0]
            auth_header = f"'hdnts: {auth_token}'"

        return f"'Origin: https://cf-embed.play.hotmart.com' 'Referer: https://cf-embed.play.hotmart.com/' 'Cookie: {cookie_header}' {auth_header}"

    def _download_with_ffmpeg_python(self, video_url, output_path, headers_arg):
        """Download video using ffmpeg-python library."""
        log.debug(f"Starting ffmpeg download to {output_path}")
        stream = ffmpeg.input(
            video_url,
            headers=headers_arg
        )
        stream = ffmpeg.output(stream, output_path)
        log.debug("Running ffmpeg with parameters")
        ffmpeg.run(stream, overwrite_output=True)
        log.info(f"Download completed: {output_path}")

    def _download_with_ffmpeg_subprocess(self, video_url, output_path):
        """Download video using direct ffmpeg subprocess call as fallback."""
        log.debug("Using ffmpeg subprocess method as fallback")
        cookie_header = '; '.join([f"{c.name}={c.value}" for c in self.session.cookies])

        cmd = [
            'ffmpeg', '-y',
            '-headers', f"Origin: https://cf-embed.play.hotmart.com\r\nReferer: https://cf-embed.play.hotmart.com/\r\nCookie: {cookie_header}",
            '-i', video_url,
            '-c', 'copy',
            output_path
        ]

        log.debug(f"FFmpeg command: {' '.join(cmd[:3])} [...headers omitted...] {' '.join(cmd[-4:])}")

        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log.error(f"FFmpeg subprocess failed with code {result.returncode}")
            log.debug(f"FFmpeg stderr: {result.stderr[:1000]}...")
            raise Exception(f"Alternative download method failed: {result.returncode}")

        log.info(f"FFmpeg subprocess download completed: {output_path}")

    def close(self):
        """Close the browser."""
        self.browser_manager.close()

    def get_lesson_title(self):
        """
        Extract lesson title from page.

        Returns:
            str: Cleaned lesson title, or "lesson" if not found
        """
        try:
            title_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1, .lesson-title"))
            )
            title = title_element.text.strip()
            # Clean the title to make it filesystem-friendly
            title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            return title or "lesson"
        except Exception as e:
            log.warning(f"Failed to get lesson title: {str(e)}")
            return "lesson"

    def get_all_lessons(self):
        """
        Get all lesson hashes and titles from the navigation menu.

        Returns:
            list: List of dictionaries with lesson hash and title
        """
        try:
            log.info("Finding all lessons from navigation menu")

            # Wait for the lesson navigation to load
            wait = WebDriverWait(self.driver, 10)
            lessons = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-page-hash]"))
            )

            lesson_data = []
            log.debug(f"Found {len(lessons)} lesson elements in navigation")

            for i, lesson in enumerate(lessons):
                hash = lesson.get_attribute('data-page-hash')
                title = lesson.find_element(By.CSS_SELECTOR, '.navigation-page-title').text.strip()
                lesson_data.append({'hash': hash, 'title': title})

            log.info(f"Successfully extracted data for {len(lesson_data)} lessons")
            return lesson_data
        except Exception as e:
            log.error("Failed to get lessons", exc_info=True)
            return []

    def download_all_lessons(self):
        """Download videos from all lessons."""
        lessons = self.get_all_lessons()
        log.info(f"Found {len(lessons)} lessons to download")

        for i, lesson in enumerate(lessons, 1):
            try:
                lesson_title = lesson['title']
                log.info(f"Processing lesson {i}/{len(lessons)}: {lesson_title}")

                # Navigate to lesson using hash
                lesson_url = f"{self.base_url}/lesson/{lesson['hash']}"
                log.debug(f"Lesson URL: {lesson_url}")

                video_urls = self.extract_video_url(lesson_url)

                if not video_urls:
                    log.warning(f"No videos found for lesson: {lesson_title}")
                    continue

                log.info(f"Found {len(video_urls)} video parts for lesson: {lesson_title}")

                for part_idx, (part_suffix, video_url) in enumerate(video_urls, 1):
                    # Create filename from lesson number, title and part
                    filename = f"{i:03d}_{lesson_title}"
                    if part_suffix:
                        filename = f"{filename}_{part_suffix}"

                    log.info(f"Downloading part {part_idx}/{len(video_urls)}: {filename}")
                    log.debug(f"Video URL: {video_url[:100]}...")

                    if self.download_video(video_url, filename):
                        log.info(f"Successfully downloaded: {filename}")
                    else:
                        log.error(f"Failed to download: {filename}")

            except Exception as e:
                log.error(f"Error processing lesson {lesson['title']}", exc_info=True)
                continue