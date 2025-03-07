"""
Browser Management Module for 101kg

This module handles browser initialization, configuration, and common browser operations.
It provides a consistent interface for working with the browser across different modules.
"""
import time
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Import logger
import logger
log = logger


class BrowserManager:
    """
    Manages browser initialization and provides common browser interaction methods.
    """

    def __init__(self, headless=False, user_data_dir=None, browser_type="chrome", browser_profile=None):
        """
        Initialize the browser manager.

        Args:
            headless (bool): Whether to run browser in headless mode
            user_data_dir (str, optional): Path to user data directory for Chrome profile
            browser_type (str): The browser to use ("chrome" or "firefox")
            browser_profile (str, optional): Path to browser profile with extensions
        """
        self.driver = None
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.browser_profile = browser_profile
        self.browser_type = browser_type.lower()
        self.base_url = "https://101karategames.club.hotmart.com"

    def initialize(self):
        """
        Initialize the browser with appropriate settings.

        Returns:
            webdriver.Chrome/Firefox: Initialized WebDriver
        """
        if self.browser_type == "firefox":
            # Configure Firefox options and initialize
            options = self._configure_firefox_options()
            self.driver = self._initialize_firefox_driver(options)
        else:
            # Configure Chrome options and initialize
            options = self._configure_chrome_options()
            self.driver = self._initialize_chrome_driver(options)

        # Set window size and initialize cookies
        if self.driver:
            self.driver.set_window_size(1366, 768)
            self._set_initial_cookies()

        return self.driver

    def _configure_chrome_options(self):
        """
        Configure Chrome options for optimal video streaming and automation.

        Returns:
            webdriver.ChromeOptions: Configured options
        """
        chrome_options = webdriver.ChromeOptions()

        # Basic options for better automation
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Set headless mode if requested
        if self.headless:
            chrome_options.add_argument("--headless=new")
            # Additional options for headless mode to ensure proper video playback
            chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
            # Removed "--mute-audio" to ensure audio is captured

        # Set user data directory if provided
        if self.user_data_dir:
            chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")

        # Add user agent to ensure compatibility
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")

        return chrome_options

    def _configure_firefox_options(self):
        """
        Configure Firefox options for optimal video streaming and automation.
        
        Returns:
            webdriver.FirefoxOptions: Configured options
        """
        firefox_options = webdriver.FirefoxOptions()
        
        # Basic options for better automation
        firefox_options.set_preference("browser.download.folderList", 2)
        firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
        firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", 
                                      "video/mp4,video/x-matroska,video/webm,video/ogg,application/octet-stream,application/vnd.apple.mpegurl")
        firefox_options.set_preference("media.volume_scale", "1.0")  # Enable audio (was 0.0)
        firefox_options.set_preference("media.autoplay.default", 0)  # Allow autoplay
        firefox_options.set_preference("media.autoplay.blocking_policy", 0)  # Don't block autoplay
        
        # Set headless mode if requested
        if self.headless:
            firefox_options.add_argument("--headless")
        
        # Set Firefox profile if provided
        # Note: We don't use set_preference for profile as it doesn't work correctly
        # Instead, the profile is loaded directly in the _initialize_firefox_driver method
        
        # Add user agent to ensure compatibility
        firefox_options.set_preference("general.useragent.override", 
                                     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/117.0")
        
        return firefox_options
        
    def _initialize_firefox_driver(self, options):
        """
        Initialize Firefox driver with multiple fallback methods.
        
        Args:
            options (webdriver.FirefoxOptions): Firefox options
            
        Returns:
            webdriver.Firefox: Firefox WebDriver instance or None if initialization fails
        """
        driver = None
        
        # Method 1: Try with browser profile if provided
        if self.browser_profile:
            try:
                log.debug(f"Attempting to initialize Firefox driver with profile: {self.browser_profile}")
                from selenium.webdriver.firefox.service import Service as FirefoxService
                
                # Use the Firefox profile that has the Video Downloader Helper extension installed
                from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
                
                # Create a Firefox profile object
                firefox_profile = FirefoxProfile(self.browser_profile)
                
                # Add special preferences to ensure extensions are enabled
                firefox_profile.set_preference("xpinstall.signatures.required", False)
                firefox_profile.set_preference("extensions.autoDisableScopes", 0)
                
                # Create a driver with this profile
                driver = webdriver.Firefox(firefox_profile=firefox_profile, options=options)
                
                # Log info about installed extensions
                try:
                    # Check for the Video Downloader Helper specifically
                    extensions_script = """
                    return {
                        hasDownloadHelper: Boolean(document.querySelector(
                            "#net_downloadhelper_toolbar, .net-downloadhelper-button, [title*='Download Helper'], #wrapper-downloadhelper-net_downloadhelper_toolbar"
                        ))
                    };
                    """
                    # Navigate to about:blank to execute the script
                    driver.get("about:blank")
                    time.sleep(1)
                    extensions_info = driver.execute_script(extensions_script)
                    
                    if extensions_info.get('hasDownloadHelper'):
                        log.info("Video Downloader Helper extension detected in Firefox")
                    else:
                        log.warning("Video Downloader Helper extension NOT found in Firefox profile")
                except Exception as e:
                    log.warning(f"Could not check for Video Downloader Helper extension: {e}")
                log.info("Successfully initialized Firefox driver with provided profile")
                return driver
            except Exception as e:
                log.warning(f"Failed to create Firefox driver with profile: {e}")
        
        # Method 2: Try system Firefox with GeckoDriverManager
        try:
            log.debug("Attempting to initialize Firefox driver with GeckoDriverManager")
            from selenium.webdriver.firefox.service import Service as FirefoxService
            from webdriver_manager.firefox import GeckoDriverManager
            
            service = FirefoxService(executable_path=GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)
            log.info("Successfully initialized Firefox driver with GeckoDriverManager")
            return driver
        except Exception as e:
            log.warning(f"Failed to create Firefox driver with GeckoDriverManager: {e}")
        
        # Method 3: Try standard Firefox path by OS
        try:
            log.debug("Attempting to initialize Firefox driver with standard OS path")
            from selenium.webdriver.firefox.service import Service as FirefoxService
            
            # Determine driver path based on operating system
            if platform.system() == "Darwin":  # macOS
                driver_path = "/usr/local/bin/geckodriver"
            elif platform.system() == "Linux":
                driver_path = "/usr/bin/geckodriver"
            else:  # Windows
                driver_path = "C:\\Program Files\\Mozilla Firefox\\geckodriver.exe"
                
            service = FirefoxService(executable_path=driver_path)
            driver = webdriver.Firefox(service=service, options=options)
            log.info("Successfully initialized Firefox driver with standard OS path")
            return driver
        except Exception as e:
            log.error(f"All Firefox driver initialization methods failed: {e}", exc_info=True)
            return None
    
    def _initialize_chrome_driver(self, options):
        """
        Initialize Chrome driver with multiple fallback methods.

        Args:
            options (webdriver.ChromeOptions): Chrome options

        Returns:
            webdriver.Chrome: Chrome WebDriver instance or None if initialization fails
        """
        driver = None

        # Method 1: Try system Chrome
        try:
            log.debug("Attempting to initialize Chrome driver with system Chrome")
            driver = webdriver.Chrome(options=options)
            log.info("Successfully initialized Chrome driver with system Chrome")
            return driver
        except Exception as e:
            log.warning(f"Failed to create Chrome driver with default settings: {e}")

        # Method 2: Try using ChromeDriverManager
        try:
            log.debug("Attempting to initialize Chrome driver with ChromeDriverManager")
            from selenium.webdriver.chrome.service import Service as ChromeService
            from webdriver_manager.chrome import ChromeDriverManager

            # Get the driver path but don't automatically install
            driver_path = ChromeDriverManager().install()

            # If the path contains THIRD_PARTY_NOTICES, adjust to find the actual executable
            if "THIRD_PARTY_NOTICES" in driver_path:
                import os
                driver_dir = os.path.dirname(driver_path)
                for file in os.listdir(driver_dir):
                    if file.startswith("chromedriver") and not file.endswith(".zip") and not file.endswith(".md"):
                        driver_path = os.path.join(driver_dir, file)
                        break

            service = ChromeService(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            log.info("Successfully initialized Chrome driver with ChromeDriverManager")
            return driver
        except Exception as e:
            log.warning(f"Failed to create Chrome driver with ChromeDriverManager: {e}")

        # Method 3: Try standard Chrome path by OS
        try:
            log.debug("Attempting to initialize Chrome driver with standard OS path")
            from selenium.webdriver.chrome.service import Service as ChromeService

            # Determine driver path based on operating system
            if platform.system() == "Darwin":  # macOS
                driver_path = "/usr/local/bin/chromedriver"
            elif platform.system() == "Linux":
                driver_path = "/usr/bin/chromedriver"
            else:  # Windows
                driver_path = "C:\\Program Files\\Google\\Chrome\\Application\\chromedriver.exe"

            service = ChromeService(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            log.info("Successfully initialized Chrome driver with standard OS path")
            return driver
        except Exception as e:
            log.error(f"All Chrome driver initialization methods failed: {e}", exc_info=True)
            return None

    def _set_initial_cookies(self):
        """Set initial cookies to prevent popups and improve user experience."""
        try:
            log.debug("Setting initial cookies")
            self.driver.get(self.base_url)
            time.sleep(2)  # Wait for page to load

            cookie_settings = [
                {'name': 'cookie-policy-accepted', 'value': 'true', 'domain': '.hotmart.com'},
                {'name': 'cookie-policy-preferences', 'value': 'true', 'domain': '.hotmart.com'},
                {'name': 'hotmart-cookie-policy', 'value': 'accepted', 'domain': '.hotmart.com'}
            ]

            for cookie in cookie_settings:
                try:
                    self.driver.add_cookie(cookie)
                    log.debug(f"Added cookie: {cookie['name']}")
                except Exception as e:
                    log.warning(f"Could not add cookie {cookie['name']}: {str(e)}")
        except Exception as e:
            log.warning(f"Error setting initial cookies: {e}")

    def handle_cookie_policy_popup(self, timeout=3):
        """
        Handle cookie policy popup if it exists by clicking on accept buttons.

        Args:
            timeout (int): Maximum time to wait for popup elements (seconds)

        Returns:
            bool: True if popup was handled, False otherwise
        """
        try:
            log.info("Checking for cookie policy popup")
            # Wait only a short time since we don't want to slow things down if there's no popup
            wait = WebDriverWait(self.driver, timeout)

            # First try by ID
            try:
                # Check if the cookie policy container exists
                cookie_container = self.driver.find_element(By.ID, "hotmart-cookie-policy")
                if cookie_container.is_displayed():
                    log.info("Found cookie policy popup, attempting to accept...")
                    return self._try_accept_cookie_buttons(cookie_container)
            except Exception:
                pass

            # Try with specific text "This site uses cookies"
            try:
                log.info("Looking for 'This site uses cookies' dialog")
                
                # Try direct approach - look for the OK button directly
                try:
                    log.info("Looking for cookie OK button directly")
                    ok_buttons = self.driver.find_elements(By.XPATH, "//button[text()='OK' or text()='Ok' or text()='ok']")
                    if len(ok_buttons) > 0:
                        log.info(f"Found {len(ok_buttons)} OK buttons directly")
                        for button in ok_buttons:
                            try:
                                if button.is_displayed():
                                    log.info("Found visible OK button, clicking it")
                                    self.driver.execute_script("arguments[0].click();", button)
                                    log.info("Clicked OK button")
                                    time.sleep(1)
                                    return True
                            except Exception as e:
                                log.info(f"Error with OK button: {e}")
                except Exception as e:
                    log.info(f"Error searching for OK buttons: {e}")
                
                # Try multiple patterns to find the cookie dialog text
                cookie_text_elements = self.driver.find_elements(By.XPATH, 
                    "//*[contains(text(), 'This site uses cookies') or contains(text(), 'site uses cookies') or contains(text(), 'cookies are important')]")
                
                # Also try looking for the text in divs with cookie/modal classes
                if len(cookie_text_elements) == 0:
                    log.info("Trying to find cookie dialog by class and content")
                    cookie_text_elements = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class, 'cookie') or contains(@class, 'modal')]//p[contains(text(), 'cookie') or contains(text(), 'Cookie')]")
                
                log.info(f"Found {len(cookie_text_elements)} elements containing cookie-related text")
                
                # Dump page source for debugging if no elements found
                if len(cookie_text_elements) == 0:
                    log.info("No cookie dialog found, dumping some page content for debugging")
                    try:
                        page_body = self.driver.find_element(By.TAG_NAME, "body").text
                        if len(page_body) > 1000:
                            page_snippet = page_body[:1000] + "..."
                        else:
                            page_snippet = page_body
                        log.info(f"Page content snippet: {page_snippet}")
                        
                        # If we see the cookie text in the page but couldn't find it with XPath, try JavaScript
                        if "This site uses cookies" in page_body or "site uses cookies" in page_body:
                            log.info("Cookie text found in page body, trying JavaScript approach")
                            result = self.driver.execute_script("""
                                // Try to find and click OK button for cookie consent
                                var buttons = document.querySelectorAll('button');
                                for (var i = 0; i < buttons.length; i++) {
                                    if (buttons[i].textContent.trim().toUpperCase() === 'OK') {
                                        console.log('Found OK button via JS');
                                        buttons[i].click();
                                        return true;
                                    }
                                }
                                return false;
                            """)
                            if result:
                                log.info("Successfully clicked OK button via JavaScript")
                                return True
                    except Exception as e:
                        log.info(f"Could not get page content: {e}")
                for element in cookie_text_elements:
                    # Try to find the parent dialog container
                    try:
                        dialog_container = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'cookie') or contains(@class, 'dialog') or contains(@class, 'modal')]")
                        if dialog_container.is_displayed():
                            log.info("Found 'This site uses cookies' dialog, attempting to accept...")
                            
                            # First look for an OK button
                            ok_buttons = dialog_container.find_elements(By.XPATH, 
                                ".//button[contains(text(), 'OK') or contains(text(), 'Ok') or contains(text(), 'ok')]")
                            
                            log.info(f"Found {len(ok_buttons)} OK buttons in dialog")
                            for button in ok_buttons:
                                if button.is_displayed():
                                    log.info("Found visible OK button, clicking it")
                                    self.driver.execute_script("arguments[0].click();", button)
                                    log.info("Clicked OK button on cookie dialog")
                                    time.sleep(1)
                                    return True
                            
                            # If no OK button found, try other accept buttons
                            return self._try_accept_cookie_buttons(dialog_container)
                    except Exception:
                        continue
            except Exception:
                pass
                
            # Try other common cookie consent popup classes/IDs
            cookie_selectors = [
                ".cookie-notice", "#cookie-notice", ".cookie-banner", "#cookie-banner",
                ".cookie-consent", "#cookie-consent", ".cookie-policy", "#cookie-policy"
            ]

            for selector in cookie_selectors:
                try:
                    cookie_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if cookie_element.is_displayed():
                        log.debug(f"Found cookie element with selector: {selector}")
                        return self._try_accept_cookie_buttons(cookie_element)
                except Exception:
                    continue

            # Use JavaScript as a last resort
            return self._try_javascript_cookie_handling()

        except Exception as e:
            log.warning(f"Error handling cookie popup: {str(e)}")
            return False

    def _try_accept_cookie_buttons(self, container):
        """
        Try to find and click accept buttons within a container.

        Args:
            container: WebElement containing cookie consent buttons

        Returns:
            bool: True if a button was clicked, False otherwise
        """
        # Try different accept button selectors
        selectors = [
            "button.accept-button", "button.accept", "button.agree",
            ".accept-cookies-button", "button[data-action='accept']",
            ".cookie-accept-button", "#acceptCookies", 
            "button:contains('OK')", "button.ok", "#okButton", "[aria-label='OK']"
        ]

        for selector in selectors:
            try:
                accept_button = container.find_element(By.CSS_SELECTOR, selector)
                if accept_button.is_displayed():
                    self.driver.execute_script("arguments[0].click();", accept_button)
                    log.debug(f"Clicked cookie accept button with selector: {selector}")
                    time.sleep(1)  # Wait for the popup to disappear
                    return True
            except Exception:
                continue

        return False

    def _try_javascript_cookie_handling(self):
        """
        Try to handle cookie popups using JavaScript.

        Returns:
            bool: True if JavaScript handled the popup, False otherwise
        """
        result = self.driver.execute_script("""
            // Try to handle cookie banners by common class/ID names
            var banners = [
                'cookie-banner', 'cookie-notice', 'cookie-policy', 'cookie-consent',
                'cookie-popup', 'cookie-message', 'cookie-notification', 'cookie-alert'
            ];

            // Try to find and click accept buttons in any of these containers
            for (var i = 0; i < banners.length; i++) {
                var elements = document.getElementsByClassName(banners[i]);
                if (elements.length === 0) {
                    elements = [document.getElementById(banners[i])];
                }

                for (var j = 0; j < elements.length; j++) {
                    if (elements[j]) {
                        var buttons = elements[j].querySelectorAll('button, .btn, a.accept, a.agree');
                        for (var k = 0; k < buttons.length; k++) {
                            if (buttons[k].innerText.toLowerCase().includes('accept') || 
                                buttons[k].innerText.toLowerCase().includes('agree') ||
                                buttons[k].innerText.toLowerCase().includes('aceitar') ||
                                buttons[k].innerText.toLowerCase().includes('ok')) {
                                buttons[k].click();
                                return true;
                            }
                        }
                    }
                }
            }

            // If we reach here, try to just hide any cookie policy containers
            var policy = document.getElementById('hotmart-cookie-policy');
            if (policy) {
                policy.style.display = 'none';
                policy.style.visibility = 'hidden';
                policy.style.zIndex = '-999999';
                return true;
            }

            return false;
        """)

        return bool(result)

    def wait_for_element(self, by, value, timeout=10, condition="presence"):
        """
        Wait for an element to be available in the DOM.

        Args:
            by (selenium.webdriver.common.by.By): The method to locate the element
            value (str): The locator value
            timeout (int): Maximum time to wait (seconds)
            condition (str): Type of wait condition: "presence", "visible", or "clickable"

        Returns:
            WebElement: The element if found, None otherwise
        """
        try:
            wait = WebDriverWait(self.driver, timeout)

            if condition == "visible":
                return wait.until(EC.visibility_of_element_located((by, value)))
            elif condition == "clickable":
                return wait.until(EC.element_to_be_clickable((by, value)))
            else:  # default to presence
                return wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            log.warning(f"Timeout waiting for element: {value} (condition: {condition})")
            return None
        except Exception as e:
            log.warning(f"Error waiting for element {value}: {e}")
            return None
    
    def wait_for_elements(self, by, value, timeout=10, condition="presence"):
        """
        Wait for multiple elements to be available in the DOM.

        Args:
            by (selenium.webdriver.common.by.By): The method to locate the elements
            value (str): The locator value
            timeout (int): Maximum time to wait (seconds)
            condition (str): Type of wait condition: "presence" or "visible"

        Returns:
            list: List of WebElements if found, empty list otherwise
        """
        try:
            wait = WebDriverWait(self.driver, timeout)

            if condition == "visible":
                return wait.until(EC.visibility_of_all_elements_located((by, value)))
            else:  # default to presence
                return wait.until(EC.presence_of_all_elements_located((by, value)))
        except TimeoutException:
            log.warning(f"Timeout waiting for elements: {value} (condition: {condition})")
            return []
        except Exception as e:
            log.warning(f"Error waiting for elements {value}: {e}")
            return []

    def execute_javascript(self, script, *args):
        """
        Execute JavaScript in the browser.

        Args:
            script (str): JavaScript code to execute
            *args: Arguments to pass to the script

        Returns:
            Any: Result of the JavaScript execution
        """
        try:
            return self.driver.execute_script(script, *args)
        except Exception as e:
            log.warning(f"Error executing JavaScript: {e}")
            return None

    def close(self):
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                log.debug("Browser closed successfully")
            except Exception as e:
                log.warning(f"Error closing browser: {e}")