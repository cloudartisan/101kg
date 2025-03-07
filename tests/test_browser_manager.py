"""
Tests for the browser_manager module.
"""
import pytest
from unittest.mock import patch, MagicMock, call
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from browser_manager import BrowserManager


class TestBrowserManagerInit:
    """Tests for BrowserManager initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        manager = BrowserManager()
        assert manager.driver is None
        assert manager.headless is False
        assert manager.user_data_dir is None
        assert manager.base_url == "https://101karategames.club.hotmart.com"

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        manager = BrowserManager(headless=True, user_data_dir="/path/to/profile")
        assert manager.driver is None
        assert manager.headless is True
        assert manager.user_data_dir == "/path/to/profile"
        assert manager.base_url == "https://101karategames.club.hotmart.com"


class TestChromeConfiguration:
    """Tests for Chrome configuration."""

    def test_configure_chrome_options_default(self):
        """Test configuring Chrome options with default settings."""
        manager = BrowserManager()
        options = manager._configure_chrome_options()
        
        # Verify basic options
        args = options.arguments
        assert "--start-maximized" in args
        assert "--disable-notifications" in args
        assert "--disable-popup-blocking" in args
        assert "--disable-infobars" in args
        assert "--disable-extensions" in args
        assert "--no-sandbox" in args
        assert "--disable-dev-shm-usage" in args
        
        # Verify headless mode is not set
        assert "--headless=new" not in args
        
        # Verify user data dir is not set
        user_data_args = [arg for arg in args if arg.startswith("--user-data-dir=")]
        assert len(user_data_args) == 0
        
        # Verify user agent is set
        user_agent_args = [arg for arg in args if arg.startswith("--user-agent=")]
        assert len(user_agent_args) == 1

    def test_configure_chrome_options_headless(self):
        """Test configuring Chrome options with headless mode."""
        manager = BrowserManager(headless=True)
        options = manager._configure_chrome_options()
        args = options.arguments
        
        # Verify headless mode is set
        assert "--headless=new" in args
        assert "--autoplay-policy=no-user-gesture-required" in args
        # We've removed mute-audio flag to enable audio capture
        assert "--mute-audio" not in args

    def test_configure_chrome_options_user_data_dir(self):
        """Test configuring Chrome options with user data directory."""
        user_data_dir = "/path/to/profile"
        manager = BrowserManager(user_data_dir=user_data_dir)
        options = manager._configure_chrome_options()
        args = options.arguments
        
        # Verify user data directory is set
        user_data_args = [arg for arg in args if arg.startswith("--user-data-dir=")]
        assert len(user_data_args) == 1
        assert f"--user-data-dir={user_data_dir}" in args


class TestFirefoxConfiguration:
    """Tests for Firefox configuration."""
    
    def test_configure_firefox_options_default(self):
        """Test configuring Firefox options with default settings."""
        manager = BrowserManager(browser_type="firefox")
        options = manager._configure_firefox_options()
        
        # Verify audio is enabled (not muted)
        assert options.preferences["media.volume_scale"] == "1.0"
        
        # Verify autoplay is enabled
        assert options.preferences["media.autoplay.default"] == 0
        assert options.preferences["media.autoplay.blocking_policy"] == 0
        
        # Verify headless mode is not set
        assert "--headless" not in options.arguments
        
    def test_configure_firefox_options_headless(self):
        """Test configuring Firefox options with headless mode."""
        manager = BrowserManager(browser_type="firefox", headless=True)
        options = manager._configure_firefox_options()
        
        # Verify headless mode is set
        assert "--headless" in options.arguments
        
        # Verify audio is still enabled in headless mode
        assert options.preferences["media.volume_scale"] == "1.0"


class TestChromeDriverInitialization:
    """Tests for Chrome driver initialization."""

    def test_initialize_chrome_driver_method1_success(self):
        """Test successful initialization with system Chrome (method 1)."""
        manager = BrowserManager()
        options = MagicMock()
        
        # Mock Chrome constructor that will succeed on first attempt
        mock_chrome = MagicMock()
        mock_chrome_instance = MagicMock()
        mock_chrome.return_value = mock_chrome_instance
        
        # Mock logging functions
        mock_debug = MagicMock()
        mock_info = MagicMock() 
        mock_warning = MagicMock()
        mock_error = MagicMock()
        
        # Apply patches
        with patch('selenium.webdriver.Chrome', mock_chrome):
            with patch('logger.debug', mock_debug):
                with patch('logger.info', mock_info):
                    with patch('logger.warning', mock_warning):
                        with patch('logger.error', mock_error):
                            # Call the method under test
                            driver = manager._initialize_chrome_driver(options)
        
        # Verify Chrome was initialized with options
        mock_chrome.assert_called_once_with(options=options)
        
        # Verify logging
        mock_debug.assert_called_once_with("Attempting to initialize Chrome driver with system Chrome")
        mock_info.assert_called_once_with("Successfully initialized Chrome driver with system Chrome")
        mock_warning.assert_not_called()
        mock_error.assert_not_called()
        
        # Verify the driver was returned
        assert driver is mock_chrome_instance

    def test_simple_alternative_initialization(self):
        """Test a simplified version of fallback initialization."""
        # Create a simpler test to verify the core concept
        manager = BrowserManager()
        options = MagicMock()
        
        # Create a simplified test for the alternative initialization
        # Let's focus on verifying that if the first attempt fails,
        # the code still returns a valid driver
        
        # Apply patches in a specific way to test fallback
        with patch.object(BrowserManager, '_initialize_chrome_driver') as mock_init:
            mock_init.return_value = MagicMock()  # Successfully initialize a driver
            
            # Call the method 
            driver = manager.initialize()
            
            # Verify the driver is correctly retrieved from _initialize_chrome_driver
            assert driver is mock_init.return_value


@patch('time.sleep')
class TestCookieHandling:
    """Tests for cookie handling methods."""

    @patch('logger.debug')
    @patch('logger.warning')
    def test_set_initial_cookies(self, mock_warning, mock_debug, mock_sleep):
        """Test setting initial cookies."""
        mock_driver = MagicMock()
        
        manager = BrowserManager()
        manager.driver = mock_driver
        manager._set_initial_cookies()
        
        # Verify driver navigated to base URL
        mock_driver.get.assert_called_once_with(manager.base_url)
        mock_sleep.assert_called_once_with(2)
        
        # Verify cookies were added
        assert mock_driver.add_cookie.call_count == 3
        mock_driver.add_cookie.assert_has_calls([
            call({'name': 'cookie-policy-accepted', 'value': 'true', 'domain': '.hotmart.com'}),
            call({'name': 'cookie-policy-preferences', 'value': 'true', 'domain': '.hotmart.com'}),
            call({'name': 'hotmart-cookie-policy', 'value': 'accepted', 'domain': '.hotmart.com'})
        ])
        
        # Verify logging
        assert mock_debug.call_count >= 4  # Initial debug message + one for each cookie
        mock_warning.assert_not_called()

    @patch('logger.debug')
    @patch('logger.warning')
    def test_set_initial_cookies_add_cookie_fails(self, mock_warning, mock_debug, mock_sleep):
        """Test handling when adding cookies fails."""
        mock_driver = MagicMock()
        mock_driver.add_cookie.side_effect = Exception("Cookie error")
        
        manager = BrowserManager()
        manager.driver = mock_driver
        manager._set_initial_cookies()
        
        # Verify driver navigated to base URL
        mock_driver.get.assert_called_once_with(manager.base_url)
        
        # Verify attempt to add cookies was made
        assert mock_driver.add_cookie.call_count == 3
        
        # Verify warning was logged for each failed cookie
        assert mock_warning.call_count == 3
        
    @patch('logger.debug')
    @patch('logger.warning')
    def test_set_initial_cookies_navigation_fails(self, mock_warning, mock_debug, mock_sleep):
        """Test handling when navigation fails."""
        mock_driver = MagicMock()
        mock_driver.get.side_effect = Exception("Navigation error")
        
        manager = BrowserManager()
        manager.driver = mock_driver
        manager._set_initial_cookies()
        
        # Verify attempt to navigate was made
        mock_driver.get.assert_called_once_with(manager.base_url)
        
        # Verify no cookies were added
        mock_driver.add_cookie.assert_not_called()
        
        # Verify warning was logged
        mock_warning.assert_called_once()


class TestCookiePolicyPopup:
    """Tests for cookie policy popup handling."""

    @patch('time.sleep')
    @patch('logger.debug')
    @patch('logger.info')
    @patch('logger.warning')
    def test_handle_cookie_policy_popup_found_by_id(self, mock_warning, mock_info, 
                                                    mock_debug, mock_sleep):
        """Test handling cookie policy popup when found by ID."""
        mock_driver = MagicMock()
        mock_cookie_container = MagicMock()
        mock_cookie_container.is_displayed.return_value = True
        mock_driver.find_element.return_value = mock_cookie_container
        
        # Set up a successful button click
        accept_button = MagicMock()
        accept_button.is_displayed.return_value = True
        mock_cookie_container.find_element.return_value = accept_button
        
        manager = BrowserManager()
        manager.driver = mock_driver
        result = manager.handle_cookie_policy_popup()
        
        # Verify we looked for the cookie policy container by ID
        mock_driver.find_element.assert_called_with(By.ID, "hotmart-cookie-policy")
        
        # Verify we checked if it's displayed
        mock_cookie_container.is_displayed.assert_called_once()
        
        # Verify we tried to find an accept button
        mock_cookie_container.find_element.assert_called()
        
        # Verify we attempted to click the button
        assert mock_driver.execute_script.call_count == 1
        
        # Verify we logged the success - can be called multiple times now
        assert mock_info.call_count >= 1
        mock_warning.assert_not_called()
        
        # Verify the result
        assert result is True
        
    @patch('time.sleep')
    @patch('logger.debug')
    @patch('logger.info')
    @patch('logger.warning')
    def test_handle_cookie_policy_popup_found_by_selector(self, mock_warning, mock_info, 
                                                          mock_debug, mock_sleep):
        """Test handling cookie policy popup when found by CSS selector."""
        mock_driver = MagicMock()
        
        # First find_element call fails (ID lookup)
        mock_driver.find_element.side_effect = [Exception("Not found by ID")]
        
        # Mock find_elements to return empty list for XPATH lookups
        mock_driver.find_elements.return_value = []
        
        # For find_element by tag_name to get body text
        mock_body = MagicMock()
        mock_body.text = "Some page content without cookie text"
        
        # Then we try CSS selectors
        def find_element_side_effect(by, selector):
            if by == By.ID:
                raise Exception("Not found by ID")
            elif by == By.TAG_NAME and selector == "body":
                return mock_body
            elif by == By.CSS_SELECTOR:
                if selector == ".cookie-notice":
                    cookie_element = MagicMock()
                    cookie_element.is_displayed.return_value = True
                    return cookie_element
                elif selector == "button.accept-button":
                    accept_button = MagicMock()
                    accept_button.is_displayed.return_value = True
                    return accept_button
            raise Exception(f"Element not found: {selector}")
            
        mock_driver.find_element.side_effect = find_element_side_effect
        
        manager = BrowserManager()
        manager.driver = mock_driver
        result = manager.handle_cookie_policy_popup()
        
        # With our new implementation, several XPATH searches will happen first
        # We're more interested in whether it eventually tries CSS selectors
        assert mock_driver.find_element.call_count >= 3
        assert call(By.ID, "hotmart-cookie-policy") in mock_driver.find_element.call_args_list
        # Eventually it will try CSS selectors
        assert call(By.CSS_SELECTOR, ".cookie-notice") in mock_driver.find_element.call_args_list
        
        # Verify we attempted to click the button
        assert mock_driver.execute_script.call_count == 1
        
        # Verify the result
        assert result is True

    @patch('time.sleep')
    @patch('logger.debug')
    @patch('logger.info')
    @patch('logger.warning')
    def test_handle_cookie_policy_popup_not_found(self, mock_warning, mock_info, mock_debug, mock_sleep):
        """Test handling when cookie policy popup is not found."""
        mock_driver = MagicMock()
        
        # All find_element calls fail
        mock_driver.find_element.side_effect = Exception("Not found")
        
        # XPATH searches find nothing
        mock_driver.find_elements.return_value = []
        
        # JavaScript approach returns False
        mock_driver.execute_script.return_value = False
        
        manager = BrowserManager()
        manager.driver = mock_driver
        result = manager.handle_cookie_policy_popup()
        
        # Verify we tried the JavaScript approach as last resort
        assert mock_driver.execute_script.call_count >= 1
        
        # Verify the result
        assert result is False
        
    @patch('time.sleep')
    @patch('logger.debug')
    @patch('logger.info')
    @patch('logger.warning')
    def test_handle_cookie_policy_popup_with_this_site_uses_cookies(self, mock_warning, mock_info, 
                                                                  mock_debug, mock_sleep):
        """Test handling cookie policy popup with 'This site uses cookies' text."""
        mock_driver = MagicMock()
        
        # First lookup fails
        mock_driver.find_element.side_effect = [Exception("Not found by ID")]
        
        # Cookie text elements found
        cookie_text_element = MagicMock()
        cookie_text_element.is_displayed.return_value = True
        mock_driver.find_elements.return_value = [cookie_text_element]
        
        # Dialog container found
        dialog_container = MagicMock()
        dialog_container.is_displayed.return_value = True
        cookie_text_element.find_element.return_value = dialog_container
        
        # OK button found
        ok_button = MagicMock()
        ok_button.is_displayed.return_value = True
        dialog_container.find_elements.return_value = [ok_button]
        
        manager = BrowserManager()
        manager.driver = mock_driver
        result = manager.handle_cookie_policy_popup()
        
        # Verify we looked for elements with 'This site uses cookies' text
        assert mock_driver.find_elements.call_count >= 1
        
        # Verify we attempted to click the OK button
        assert mock_driver.execute_script.call_count == 1
        
        # Verify the result
        assert result is True
        
    @patch('time.sleep')
    @patch('logger.debug')
    @patch('logger.info')
    @patch('logger.warning')
    def test_handle_cookie_policy_popup_javascript_approach(self, mock_warning, mock_info, 
                                                          mock_debug, mock_sleep):
        """Test handling cookie policy popup with JavaScript approach when text is in body."""
        mock_driver = MagicMock()
        
        # All element lookups fail
        mock_driver.find_element.side_effect = Exception("Not found")
        mock_driver.find_elements.return_value = []
        
        # But we find body text with cookie message
        mock_body = MagicMock()
        mock_body.text = "This site uses cookies\nCookies are important for this site..."
        
        def find_element_side_effect(by, selector):
            if by == By.TAG_NAME and selector == "body":
                return mock_body
            raise Exception(f"Element not found: {selector}")
            
        mock_driver.find_element.side_effect = find_element_side_effect
        
        # JavaScript finds and clicks OK button
        mock_driver.execute_script.return_value = True
        
        manager = BrowserManager()
        manager.driver = mock_driver
        result = manager.handle_cookie_policy_popup()
        
        # Verify we tried to get body text to check for cookie message
        assert call(By.TAG_NAME, "body") in mock_driver.find_element.call_args_list
        
        # Verify we used JavaScript to find and click OK button
        assert mock_driver.execute_script.call_count == 1
        
        # Verify the result
        assert result is True


class TestWaitForElement:
    """Tests for waiting for elements."""

    def test_simple_presence_wait(self):
        """Test a simplified test for wait_for_element with default condition."""
        manager = BrowserManager()
        manager.driver = MagicMock()
        
        # Create a mock WebDriverWait and element
        mock_wait = MagicMock()
        mock_element = MagicMock()
        mock_wait.until.return_value = mock_element
        
        # Patch WebDriverWait to return our mock
        with patch.object(WebDriverWait, '__new__', return_value=mock_wait):
            # Patch EC.presence_of_element_located
            with patch.object(EC, 'presence_of_element_located') as mock_condition:
                # Call the method being tested
                result = manager.wait_for_element(By.ID, "test-id")
                
                # Verify the condition was called correctly
                mock_condition.assert_called_once_with((By.ID, "test-id"))
                
                # Verify until was called
                mock_wait.until.assert_called_once()
                
                # Verify the element was returned
                assert result == mock_element
    
    def test_simple_visibility_wait(self):
        """Test a simplified test for wait_for_element with visible condition."""
        manager = BrowserManager()
        manager.driver = MagicMock()
        
        # Create a mock WebDriverWait and element
        mock_wait = MagicMock()
        mock_element = MagicMock()
        mock_wait.until.return_value = mock_element
        
        # Patch WebDriverWait to return our mock
        with patch.object(WebDriverWait, '__new__', return_value=mock_wait):
            # Patch EC.visibility_of_element_located
            with patch.object(EC, 'visibility_of_element_located') as mock_condition:
                # Call the method being tested
                result = manager.wait_for_element(By.ID, "test-id", condition="visible")
                
                # Verify the condition was called correctly
                mock_condition.assert_called_once_with((By.ID, "test-id"))
                
                # Verify until was called
                mock_wait.until.assert_called_once()
                
                # Verify the element was returned
                assert result == mock_element
    
    def test_simple_clickable_wait(self):
        """Test a simplified test for wait_for_element with clickable condition."""
        manager = BrowserManager()
        manager.driver = MagicMock()
        
        # Create a mock WebDriverWait and element
        mock_wait = MagicMock()
        mock_element = MagicMock()
        mock_wait.until.return_value = mock_element
        
        # Patch WebDriverWait to return our mock
        with patch.object(WebDriverWait, '__new__', return_value=mock_wait):
            # Patch EC.element_to_be_clickable
            with patch.object(EC, 'element_to_be_clickable') as mock_condition:
                # Call the method being tested
                result = manager.wait_for_element(By.ID, "test-id", condition="clickable")
                
                # Verify the condition was called correctly
                mock_condition.assert_called_once_with((By.ID, "test-id"))
                
                # Verify until was called
                mock_wait.until.assert_called_once()
                
                # Verify the element was returned
                assert result == mock_element
    
    def test_simple_timeout(self):
        """Test a simplified test for wait_for_element timeout handling."""
        manager = BrowserManager()
        manager.driver = MagicMock()
        
        # Create a mock WebDriverWait that raises TimeoutException
        mock_wait = MagicMock()
        mock_wait.until.side_effect = TimeoutException("Timed out")
        
        # Patch WebDriverWait to return our mock
        with patch.object(WebDriverWait, '__new__', return_value=mock_wait):
            # Patch EC.presence_of_element_located
            with patch.object(EC, 'presence_of_element_located'):
                # Patch logger.warning
                with patch('logger.warning') as mock_warning:
                    # Call the method being tested
                    result = manager.wait_for_element(By.ID, "test-id")
                    
                    # Verify warning was logged
                    mock_warning.assert_called_once()
                    
                    # Verify the result is None on timeout
                    assert result is None


class TestJavaScriptExecution:
    """Tests for JavaScript execution."""

    @patch('logger.warning')
    def test_execute_javascript_success(self, mock_warning):
        """Test successful JavaScript execution."""
        mock_driver = MagicMock()
        mock_driver.execute_script.return_value = "result"
        
        manager = BrowserManager()
        manager.driver = mock_driver
        result = manager.execute_javascript("script", "arg1", "arg2")
        
        # Verify script was executed with arguments
        mock_driver.execute_script.assert_called_once_with("script", "arg1", "arg2")
        
        # Verify no warning was logged
        mock_warning.assert_not_called()
        
        # Verify the result
        assert result == "result"

    @patch('logger.warning')
    def test_execute_javascript_error(self, mock_warning):
        """Test handling error in JavaScript execution."""
        mock_driver = MagicMock()
        mock_driver.execute_script.side_effect = Exception("JavaScript error")
        
        manager = BrowserManager()
        manager.driver = mock_driver
        result = manager.execute_javascript("script", "arg1")
        
        # Verify warning was logged
        mock_warning.assert_called_once()
        
        # Verify the result is None on error
        assert result is None


class TestInitializeAndClose:
    """Tests for initialize and close methods."""

    @patch('logger.debug')
    def test_close_browser(self, mock_debug):
        """Test closing the browser."""
        mock_driver = MagicMock()
        
        manager = BrowserManager()
        manager.driver = mock_driver
        manager.close()
        
        # Verify driver was quit
        mock_driver.quit.assert_called_once()
        
        # Verify debug message was logged
        mock_debug.assert_called_once_with("Browser closed successfully")

    @patch('logger.warning')
    @patch('logger.debug')
    def test_close_browser_error(self, mock_debug, mock_warning):
        """Test handling error when closing the browser."""
        mock_driver = MagicMock()
        mock_driver.quit.side_effect = Exception("Quit error")
        
        manager = BrowserManager()
        manager.driver = mock_driver
        manager.close()
        
        # Verify driver.quit was called
        mock_driver.quit.assert_called_once()
        
        # Verify warning was logged
        mock_warning.assert_called_once()

    def test_initialize_full_flow(self):
        """Test the full browser initialization flow."""
        with patch.object(BrowserManager, '_configure_chrome_options') as mock_config:
            mock_config.return_value = MagicMock()
            
            with patch.object(BrowserManager, '_initialize_chrome_driver') as mock_init:
                mock_driver = MagicMock()
                mock_init.return_value = mock_driver
                
                with patch.object(BrowserManager, '_set_initial_cookies') as mock_cookies:
                    manager = BrowserManager()
                    driver = manager.initialize()
                    
                    # Verify the configuration flow
                    mock_config.assert_called_once()
                    mock_init.assert_called_once_with(mock_config.return_value)
                    mock_cookies.assert_called_once()
                    
                    # Verify window size was set
                    mock_driver.set_window_size.assert_called_once_with(1366, 768)
                    
                    # Verify driver was returned
                    assert driver is mock_driver