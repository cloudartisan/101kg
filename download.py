import os
import time
import requests
import m3u8
import ffmpeg
import argparse
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from url_extractor import URLExtractor


class VideoDownloader:
    """
    Main class for downloading videos from Hotmart platform.
    Handles authentication, navigation, URL extraction, and video downloading.
    """
    
    def __init__(self, email, password):
        """
        Initialize the downloader with user credentials.
        
        Args:
            email (str): User's email for Hotmart login
            password (str): User's password for Hotmart login
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
        
        # Initialize browser
        self._setup_browser()
    
    def _setup_browser(self):
        """Set up the Chrome browser with appropriate options and cookies."""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Set initial cookies to prevent popups
        self.driver.get(self.base_url)
        self._set_initial_cookies()
    
    def _set_initial_cookies(self):
        """Set initial cookies to prevent popups and improve user experience."""
        cookie_settings = [
            {'name': 'cookie-policy-accepted', 'value': 'true', 'domain': '.hotmart.com'},
            {'name': 'cookie-policy-preferences', 'value': 'true', 'domain': '.hotmart.com'},
            {'name': 'hotmart-cookie-policy', 'value': 'accepted', 'domain': '.hotmart.com'}
        ]
        
        for cookie in cookie_settings:
            self.driver.add_cookie(cookie)

    def login(self):
        """
        Login to Hotmart platform and transfer cookies to requests session.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            self.driver.get(self.login_url)
            wait = WebDriverWait(self.driver, 20)
            
            # Wait for page to load completely
            time.sleep(5)
            
            # Fill login form
            email_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[type='email']"))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            
            password_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            password_field.clear()
            password_field.send_keys(self.password)
            
            login_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-login[data-test='submit']"))
            )
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)

            # Transfer cookies from Selenium to requests session
            self._transfer_cookies_to_session()

            return True
            
        except Exception as e:
            print(f"Login failed: {str(e)}")
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
            print(f"Attempting to get video URL from API for video ID: {video_id}")
            
            # Use the URLExtractor's get_url_from_api method
            return URLExtractor.get_url_from_api(video_id, self.session, jwt_token)
            
        except Exception as e:
            print(f"Error getting URL from API: {str(e)}")
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
            print(f"\nNavigating to lesson page: {lesson_url}")
            self.driver.get(lesson_url)
            time.sleep(8)  # Increased wait time for page to fully load
            
            video_urls = []
            wait = WebDriverWait(self.driver, 15)
            
            # Find the iframe
            print("Looking for video iframe...")
            iframe = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='cf-embed.play.hotmart.com']"))
            )
            
            # Extract video ID and JWT token from iframe src
            iframe_src = iframe.get_attribute('src')
            print(f"Found iframe with src: {iframe_src}")
            
            video_id = URLExtractor.extract_video_id_from_iframe(iframe_src)
            print(f"Found video ID: {video_id}")
            
            if not video_id:
                print("Failed to extract video ID from iframe src")
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
            print(f"Failed to load lesson page: {error_msg}")
            return []
    
    def _extract_jwt_token(self, iframe_src):
        """Extract JWT token from iframe src if present."""
        jwt_token = None
        if 'jwtToken=' in iframe_src:
            print("Found JWT token in iframe src, might help with authentication")
            jwt_token = iframe_src.split('jwtToken=')[1].split('&')[0]
        return jwt_token
    
    def _try_jwt_token_approach(self, video_id, jwt_token):
        """Try to get video URL using JWT token."""
        if not jwt_token:
            return []
            
        video_urls = []
        
        # Try to get the video directly using the JWT token as authentication
        print("Trying to use JWT token to get a direct URL...")
        direct_jwt_url = f"https://cf-embed.play.hotmart.com/video/{video_id}/play?jwt={jwt_token}"
        response = self.session.get(direct_jwt_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
            'Accept': 'application/json',
            'Origin': 'https://cf-embed.play.hotmart.com',
            'Referer': f'https://cf-embed.play.hotmart.com/embed/{video_id}'
        })
        
        if response.status_code == 200:
            try:
                data = response.json()
                if 'url' in data:
                    print(f"Successfully retrieved URL using JWT token: {data['url']}")
                    video_urls.append(("", data['url']))
                    return video_urls
            except:
                pass
        
        # If direct API call fails, try to load the embed page with the JWT token
        print("Direct API call failed. Trying to load embed page with JWT token...")
        embed_url = f"https://cf-embed.play.hotmart.com/embed/{video_id}?jwt={jwt_token}"
        
        # Load the embed page in the browser to capture network requests
        print(f"Loading embed page in browser: {embed_url}")
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
        print(f"Found {len(network_requests)} network requests to Hotmart CDN")
        
        # Look for m3u8 URLs with hdntl token
        for request in network_requests:
            print(f"Network request: {request}")
            if 'hdntl=' in request and '.m3u8' in request:
                print(f"Found m3u8 URL with hdntl token: {request}")
                video_urls.append(("", request))
                return video_urls
        
        # If we didn't find a direct m3u8 URL, look for any URL with hdntl token
        for request in network_requests:
            if 'hdntl=' in request:
                print(f"Found URL with hdntl token: {request}")
                # Extract the hdntl token
                hdntl_pattern = r'hdntl=exp=[0-9]+~acl=\/\*~data=hdntl~hmac=[a-f0-9]+'
                matches = re.findall(hdntl_pattern, request)
                
                if matches:
                    token = matches[0]
                    direct_url = f"https://vod-akm.play.hotmart.com/video/{video_id}/hls/{video_id}-audio=2756-video=2292536.m3u8?{token}"
                    print(f"Constructed URL with token from network request: {direct_url}")
                    video_urls.append(("", direct_url))
                    return video_urls
        
        return []
    
    def _try_api_approach(self, video_id, jwt_token):
        """Try to get video URL using API methods."""
        print("Trying API method to get video URL...")
        api_url = self.get_video_url_from_api(video_id, jwt_token)
        if api_url:
            print(f"Using API URL: {api_url}")
            return [("", api_url)]
        return []
    
    def _try_javascript_extraction(self, lesson_url, video_id, jwt_token):
        """Try to extract video URL using JavaScript injection."""
        print("API method failed. Switching to iframe for JavaScript extraction...")
        
        # Navigate back to the lesson page
        self.driver.get(lesson_url)
        time.sleep(5)
        
        # Find the iframe again
        wait = WebDriverWait(self.driver, 15)
        iframe = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='cf-embed.play.hotmart.com']"))
        )
        
        self.driver.switch_to.frame(iframe)
        
        # Use the extraction script from the URLExtractor module
        print("Executing URL extraction script...")
        script = URLExtractor.get_extraction_script()
        
        # Execute script and wait for URL
        result = self.driver.execute_script(script)
        
        # Add JWT token to the result if we have it
        if jwt_token and isinstance(result, dict) and 'jwtToken' not in result:
            result['jwtToken'] = jwt_token
            print(f"Added JWT token to extraction result")
        
        print("Processing extraction results...")
        # Process the result using the URLExtractor, passing the session for API fallback
        video_urls = URLExtractor.process_extraction_result(result, self.session)
        
        # Switch back to main frame
        self.driver.switch_to.default_content()
        
        return video_urls
    
    def _try_direct_embed_approach(self, video_id, jwt_token, lesson_url):
        """Try to get video URL directly from the embed page."""
        print("No video URLs found using standard methods. Trying direct embed page approach...")
        
        # Try to get the URL directly from the embed page
        embed_url = f"https://cf-embed.play.hotmart.com/embed/{video_id}"
        if jwt_token:
            embed_url += f"?jwt={jwt_token}"
        print(f"Fetching embed page: {embed_url}")
        
        response = self.session.get(embed_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Referer': lesson_url
        })
        
        if response.status_code != 200:
            return []
            
        content = response.text
        video_urls = []
        
        # Try to find hdntl token with regex pattern matching the format in examples
        hdntl_pattern = r'hdntl=exp=[0-9]+~acl=\/\*~data=hdntl~hmac=[a-f0-9]+'
        matches = re.findall(hdntl_pattern, content)
        
        if matches:
            token = matches[0]
            print(f"Found hdntl token with regex: {token}")
            direct_url = f"https://vod-akm.play.hotmart.com/video/{video_id}/hls/{video_id}-audio=2756-video=2292536.m3u8?{token}"
            print(f"Constructed URL with token from regex: {direct_url}")
            video_urls.append(("", direct_url))
            return video_urls
        elif 'hdntl=' in content:
            print("Found hdntl token in embed page")
            token_start = content.find('hdntl=')
            if token_start > 0:
                token_end = content.find('"', token_start)
                if token_end < 0:
                    token_end = content.find("'", token_start)
                if token_end > 0:
                    token = content[token_start:token_end]
                    direct_url = f"https://vod-akm.play.hotmart.com/video/{video_id}/hls/{video_id}-audio=2756-video=2292536.m3u8?{token}"
                    print(f"Constructed URL with token from embed page: {direct_url}")
                    video_urls.append(("", direct_url))
                    return video_urls
        
        return []
    
    def _try_network_requests_approach(self, video_id, jwt_token):
        """Try to extract video URL from network requests."""
        print("Still no URL found. Trying to extract from network requests...")
        
        # Navigate to the embed page directly
        embed_url = f"https://cf-embed.play.hotmart.com/embed/{video_id}"
        if jwt_token:
            embed_url += f"?jwt={jwt_token}"
        print(f"Loading embed page in browser: {embed_url}")
        
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
                print(f"Found request with hdntl token: {request}")
                # Extract the token
                hdntl_pattern = r'hdntl=exp=[0-9]+~acl=\/\*~data=hdntl~hmac=[a-f0-9]+'
                matches = re.findall(hdntl_pattern, request)
                
                if matches:
                    token = matches[0]
                    direct_url = f"https://vod-akm.play.hotmart.com/video/{video_id}/hls/{video_id}-audio=2756-video=2292536.m3u8?{token}"
                    print(f"Constructed URL with token from network request: {direct_url}")
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
                self._download_hls(video_url, filename)
            else:
                self._download_mp4(video_url, filename)
            return True
            
        except Exception as e:
            print(f"Download failed: {str(e)}")
            return False

    def _download_mp4(self, video_url, filename):
        """
        Download direct MP4 video.
        
        Args:
            video_url (str): URL of the MP4 video
            filename (str): Filename to save the video as
        """
        response = requests.get(video_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        filepath = os.path.join(self.download_dir, f"{filename}.mp4")
        block_size = 1024  # 1 Kibibyte
        
        with open(filepath, 'wb') as file:
            for data in response.iter_content(block_size):
                file.write(data)

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
            print(f"Downloading HLS stream: {video_url}")
            
            # Set headers based on what we saw in the network requests
            headers = {
                'Origin': 'https://cf-embed.play.hotmart.com',
                'Referer': 'https://cf-embed.play.hotmart.com/',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            # Use our session to load the playlist
            print("Fetching playlist...")
            playlist_response = self.session.get(video_url, headers=headers)
            if not playlist_response.ok:
                print(f"Failed to load playlist: {playlist_response.status_code}")
                print(f"Response: {playlist_response.text}")
                raise Exception(f"Failed to load playlist: {playlist_response.status_code}")
                
            print("Parsing playlist...")
            playlist = m3u8.loads(playlist_response.text)
            output_path = os.path.join(self.download_dir, f"{filename}.mp4")
            
            # Extract auth token and cookies for ffmpeg
            headers_arg = self._prepare_ffmpeg_headers(video_url)
            
            # Try primary ffmpeg method
            try:
                self._download_with_ffmpeg_python(video_url, output_path, headers_arg)
            except Exception as e:
                print(f"Primary ffmpeg method failed: {str(e)}")
                self._download_with_ffmpeg_subprocess(video_url, output_path)
            
        except Exception as e:
            print(f"HLS download failed: {str(e)}")
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
        print(f"Starting ffmpeg download to {output_path}...")
        stream = ffmpeg.input(
            video_url,
            headers=headers_arg
        )
        stream = ffmpeg.output(stream, output_path)
        ffmpeg.run(stream, overwrite_output=True)
        print(f"Download completed: {output_path}")
    
    def _download_with_ffmpeg_subprocess(self, video_url, output_path):
        """Download video using direct ffmpeg subprocess call as fallback."""
        print("Trying alternative download method with subprocess...")
        cookie_header = '; '.join([f"{c.name}={c.value}" for c in self.session.cookies])
        
        cmd = [
            'ffmpeg', '-y',
            '-headers', f"Origin: https://cf-embed.play.hotmart.com\r\nReferer: https://cf-embed.play.hotmart.com/\r\nCookie: {cookie_header}",
            '-i', video_url,
            '-c', 'copy',
            output_path
        ]
        
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Alternative method failed: {result.stderr}")
            raise Exception(f"Alternative download method failed: {result.returncode}")
        
        print(f"Alternative download completed: {output_path}")

    def close(self):
        """Close the browser."""
        self.driver.quit()

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
            print(f"Failed to get lesson title: {str(e)}")
            return "lesson"

    def get_all_lessons(self):
        """
        Get all lesson hashes and titles from the navigation menu.
        
        Returns:
            list: List of dictionaries with lesson hash and title
        """
        try:
            # Wait for the lesson navigation to load
            wait = WebDriverWait(self.driver, 10)
            lessons = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-page-hash]"))
            )
            
            lesson_data = []
            for lesson in lessons:
                hash = lesson.get_attribute('data-page-hash')
                title = lesson.find_element(By.CSS_SELECTOR, '.navigation-page-title').text.strip()
                lesson_data.append({'hash': hash, 'title': title})
                
            return lesson_data
        except Exception as e:
            print(f"Failed to get lessons: {str(e)}")
            return []

    def download_all_lessons(self):
        """Download videos from all lessons."""
        lessons = self.get_all_lessons()
        
        for i, lesson in enumerate(lessons, 1):
            try:
                print(f"\nProcessing lesson {i}/{len(lessons)}: {lesson['title']}")
                
                # Navigate to lesson using hash
                lesson_url = f"{self.base_url}/lesson/{lesson['hash']}"
                video_urls = self.extract_video_url(lesson_url)
                
                if not video_urls:
                    print(f"No videos found for lesson: {lesson['title']}")
                    continue
                
                for part_suffix, video_url in video_urls:
                    # Create filename from lesson number, title and part
                    filename = f"{i:03d}_{lesson['title']}"
                    if part_suffix:
                        filename = f"{filename}_{part_suffix}"
                    
                    if self.download_video(video_url, filename):
                        print(f"Successfully downloaded: {filename}")
                    else:
                        print(f"Failed to download: {filename}")
                    
            except Exception as e:
                print(f"Error processing lesson {lesson['title']}: {str(e)}")
                continue


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Download videos from 101 Karate Games')
    parser.add_argument('--email', help='Your Hotmart email/username', required=True)
    parser.add_argument('--password', help='Your Hotmart password', required=True)
    args = parser.parse_args()
    
    downloader = VideoDownloader(args.email, args.password)
    
    try:
        if not downloader.login():
            print("Failed to login. Exiting...")
            return
            
        downloader.download_all_lessons()
            
    finally:
        downloader.close()


if __name__ == "__main__":
    main() 