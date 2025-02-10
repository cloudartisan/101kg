import os
import time
import requests
import m3u8
import ffmpeg
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse
import argparse

class VideoDownloader:
    def __init__(self, email, password):
        self.base_url = "https://101karategames.club.hotmart.com"
        self.login_url = "https://101karategames.club.hotmart.com/login"
        self.email = email
        self.password = password
        self.download_dir = "videos"
        
        # Create videos directory if it doesn't exist
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        
        # Initialize Chrome driver
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Set initial cookies to prevent popups
        self.driver.get(self.base_url)
        self.driver.add_cookie({
            'name': 'cookie-policy-accepted',
            'value': 'true',
            'domain': '.hotmart.com'
        })
        self.driver.add_cookie({
            'name': 'cookie-policy-preferences',
            'value': 'true',
            'domain': '.hotmart.com'
        })
        self.driver.add_cookie({
            'name': 'hotmart-cookie-policy',
            'value': 'accepted',
            'domain': '.hotmart.com'
        })

    def login(self):
        """Login to Hotmart platform"""
        try:
            self.driver.get(self.login_url)
            wait = WebDriverWait(self.driver, 20)
            
            # Wait for page to load completely
            time.sleep(5)
            
            # Wait for and fill email field
            email_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[type='email']"))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            
            # Wait for and fill password field
            password_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Use the specific button selector
            login_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-login[data-test='submit']"))
            )
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)

            return True
            
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def get_video_parts(self):
        """Get all video parts in the current lesson"""
        try:
            wait = WebDriverWait(self.driver, 10)
            parts = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.playlist-media"))
            )
            return parts
        except Exception:
            # Return empty list if no parts found (single video lesson)
            return []

    def extract_video_url(self, lesson_url):
        """Extract video URL(s) from lesson page"""
        try:
            self.driver.get(lesson_url)
            time.sleep(5)  # Wait for page load
            video_urls = []
            wait = WebDriverWait(self.driver, 10)
            
            try:
                # Handle notification popup if present
                try:
                    notification = self.driver.find_element(By.CSS_SELECTOR, ".notification-authorize")
                    if notification.is_displayed():
                        dont_show_button = self.driver.find_element(By.CSS_SELECTOR, ".btn-notification-hide")
                        dont_show_button.click()
                        time.sleep(1)
                except:
                    pass  # No notification popup
                
                # Handle cookie policy popup if present
                try:
                    cookie_policy = self.driver.find_element(By.CSS_SELECTOR, ".cookie-alert-container-header")
                    if cookie_policy.is_displayed():
                        accept_button = self.driver.find_element(By.CSS_SELECTOR, ".cookie-policy-accept-all")
                        self.driver.execute_script("arguments[0].click();", accept_button)
                        time.sleep(1)
                except:
                    pass  # No cookie policy popup

                # Wait for either playlist or video to be present
                wait.until(lambda driver: 
                    len(driver.find_elements(By.CSS_SELECTOR, ".playlist-media")) > 0 or 
                    len(driver.find_elements(By.TAG_NAME, "video")) > 0
                )
                
                # Check for multiple parts
                parts = self.driver.find_elements(By.CSS_SELECTOR, ".playlist-media")
                
                if len(parts) > 0:
                    print(f"Found {len(parts)} video parts")
                    # Multiple parts exist
                    for i, part in enumerate(parts, 1):
                        try:
                            print(f"Processing part {i}")
                            # Scroll part into view and click
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", part)
                            time.sleep(1)
                            self.driver.execute_script("arguments[0].click();", part)
                            time.sleep(3)
                            
                            # Wait for video element and get source
                            video_element = wait.until(
                                EC.presence_of_element_located((By.TAG_NAME, "video"))
                            )
                            video_url = video_element.get_attribute("src")
                            if video_url:
                                video_urls.append((f"part{i}", video_url))
                                print(f"Found video URL for part {i}")
                            else:
                                print(f"No source URL found for part {i}")
                                
                        except Exception as e:
                            error_msg = str(e).split('\n')[0] if str(e) else "Unknown error"
                            print(f"Failed to get video URL for part {i}: {error_msg}")
                            
                else:
                    print("Looking for single video")
                    try:
                        # Single video lesson - wait for video element
                        video_element = wait.until(
                            EC.presence_of_element_located((By.TAG_NAME, "video"))
                        )
                        video_url = video_element.get_attribute("src")
                        if video_url:
                            video_urls.append(("", video_url))
                            print("Found single video URL")
                        else:
                            print("No source URL found for video")
                    except Exception as e:
                        error_msg = str(e).split('\n')[0] if str(e) else "Unknown error"
                        print(f"Failed to get single video: {error_msg}")
                
                return video_urls
                
            except Exception as e:
                error_msg = str(e).split('\n')[0] if str(e) else "Unknown error"
                print(f"Error processing video elements: {error_msg}")
                return []
            
        except Exception as e:
            error_msg = str(e).split('\n')[0] if str(e) else "Unknown error"
            print(f"Failed to load lesson page: {error_msg}")
            return []

    def download_video(self, video_url, filename):
        """Download video from URL"""
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
        """Download direct MP4 video"""
        response = requests.get(video_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        filepath = os.path.join(self.download_dir, f"{filename}.mp4")
        block_size = 1024  # 1 Kibibyte
        
        with open(filepath, 'wb') as file:
            for data in response.iter_content(block_size):
                file.write(data)

    def _download_hls(self, video_url, filename):
        """Download and convert HLS stream"""
        playlist = m3u8.load(video_url)
        
        # Get highest quality stream
        stream_url = playlist.playlists[0].uri if playlist.playlists else video_url
        
        output_path = os.path.join(self.download_dir, f"{filename}.mp4")
        
        # Use ffmpeg to download and convert HLS to MP4
        stream = ffmpeg.input(stream_url)
        stream = ffmpeg.output(stream, output_path)
        ffmpeg.run(stream)

    def close(self):
        """Close the browser"""
        self.driver.quit()

    def get_lesson_title(self):
        """Extract lesson title from page"""
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
        """Get all lesson hashes and titles from the navigation menu"""
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
        """Download videos from all lessons"""
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
    parser = argparse.ArgumentParser(description='Download videos from 101 Karate Games')
    parser.add_argument('--email', help='Your Hotmart email/username', required=True)
    parser.add_argument('--password', help='Your Hotmart password', required=True)
    args = parser.parse_args()
    
    downloader = VideoDownloader(args.email, args.password)
    
    try:
        # Login to platform
        if not downloader.login():
            print("Failed to login. Exiting...")
            return
            
        # Download all lessons
        downloader.download_all_lessons()
            
    finally:
        downloader.close()

if __name__ == "__main__":
    main() 