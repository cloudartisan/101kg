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
    
    def __init__(self, headless=False, user_data_dir=None):
        """
        Initialize the browser manager.
        
        Args:
            headless (bool): Whether to run browser in headless mode
            user_data_dir (str, optional): Path to user data directory for Chrome profile
        """
        self.driver = None
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.base_url = "https://101karategames.club.hotmart.com"
        
    def initialize(self):
        """
        Initialize the browser with appropriate settings.
        
        Returns:
            webdriver.Chrome: Initialized Chrome WebDriver
        """
        # Configure Chrome options
        options = self._configure_chrome_options()
        
        # Try multiple methods to initialize Chrome driver
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
            chrome_options.add_argument("--mute-audio")
        
        # Set user data directory if provided
        if self.user_data_dir:
            chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
        
        # Add user agent to ensure compatibility
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
        
        return chrome_options
    
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
            log.debug("Checking for cookie policy popup")
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
            ".cookie-accept-button", "#acceptCookies"
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
                                buttons[k].innerText.toLowerCase().includes('aceitar')) {
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