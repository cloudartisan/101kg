#!/usr/bin/env python3
"""
Firefox Configuration Checker

This tool helps verify Firefox is properly configured with the Video Downloader Helper extension.
"""
import time
import sys
import os
import argparse
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

def check_firefox_configuration(browser_profile_path=None):
    """
    Check Firefox configuration and Video Downloader Helper extension.
    
    Args:
        browser_profile_path (str, optional): Path to Firefox profile
    """
    print("Checking Firefox configuration...")
    
    # Try to detect Firefox
    firefox_binary_paths = [
        "/Applications/Firefox.app/Contents/MacOS/firefox",  # macOS
        "C:\\Program Files\\Mozilla Firefox\\firefox.exe",   # Windows
        "/usr/bin/firefox"                                   # Linux
    ]
    
    firefox_found = False
    for path in firefox_binary_paths:
        if os.path.exists(path):
            print(f"✅ Firefox found at: {path}")
            firefox_found = True
            break
    
    if not firefox_found:
        print("❌ Firefox not found in standard locations. Please install Firefox or provide its location.")
        return False
    
    # Check for profiles
    if browser_profile_path:
        if os.path.exists(browser_profile_path):
            print(f"✅ Specified Firefox profile found at: {browser_profile_path}")
        else:
            print(f"❌ Specified Firefox profile not found at: {browser_profile_path}")
            return False
    else:
        print("ℹ️ No Firefox profile path provided. Will use default profile.")
        
        # Try to detect profiles directory
        profile_locations = [
            os.path.expanduser("~/Library/Application Support/Firefox/Profiles/"),  # macOS
            os.path.expanduser("~/.mozilla/firefox/"),                              # Linux
            os.path.expanduser("~/AppData/Roaming/Mozilla/Firefox/Profiles/")       # Windows
        ]
        
        profiles_dir_found = False
        for profile_dir in profile_locations:
            if os.path.exists(profile_dir):
                print(f"✅ Firefox profiles directory found at: {profile_dir}")
                profiles_dir_found = True
                print(f"ℹ️ Detected profiles:")
                for entry in os.listdir(profile_dir):
                    if os.path.isdir(os.path.join(profile_dir, entry)):
                        print(f"   - {entry}")
                break
        
        if not profiles_dir_found:
            print("⚠️ Firefox profiles directory not found in standard locations.")
    
    # Launch Firefox and check for Video Downloader Helper
    try:
        print("\nAttempting to launch Firefox to check for Video Downloader Helper extension...")
        
        options = Options()
        
        if browser_profile_path:
            firefox_profile = FirefoxProfile(browser_profile_path)
            firefox_profile.set_preference("xpinstall.signatures.required", False)
            firefox_profile.set_preference("extensions.autoDisableScopes", 0)
            driver = webdriver.Firefox(firefox_profile=firefox_profile, options=options)
        else:
            driver = webdriver.Firefox(options=options)
        
        print("✅ Successfully launched Firefox")
        
        # Navigate to Mozilla's extension page
        driver.get("about:addons")
        time.sleep(3)
        
        # Click on "Extensions" in the sidebar
        try:
            extensions_link = driver.find_element(By.CSS_SELECTOR, "[name='extension']")
            extensions_link.click()
            time.sleep(2)
            print("✅ Navigated to Extensions page")
        except Exception as e:
            print(f"⚠️ Could not navigate to Extensions page: {e}")
        
        # Check for Video Downloader Helper extension
        page_source = driver.page_source.lower()
        
        if "video downloadhelper" in page_source or "video download helper" in page_source:
            print("✅ Video Downloader Helper extension is INSTALLED!")
            
            # Check if the extension is enabled
            try:
                # Check toolbar for extension icon
                driver.get("about:blank")
                time.sleep(2)
                
                extension_icon = driver.find_element(By.CSS_SELECTOR, 
                    "#net_downloadhelper_toolbar, .net-downloadhelper-button, [title*='Download Helper'], #wrapper-downloadhelper-net_downloadhelper_toolbar"
                )
                print("✅ Video Downloader Helper toolbar icon is visible")
                
                # Get extension version if possible
                driver.get("about:addons")
                time.sleep(2)
                
                try:
                    extension_card = driver.find_element(By.CSS_SELECTOR, 
                        "[class*='downloadhelper'], [title*='Download Helper']"
                    )
                    version_elem = extension_card.find_element(By.CSS_SELECTOR, ".version")
                    if version_elem:
                        print(f"✅ Video Downloader Helper version: {version_elem.text}")
                except:
                    print("ℹ️ Could not determine extension version")
                
            except Exception as e:
                print(f"⚠️ Video Downloader Helper installed but icon not visible in toolbar: {e}")
        else:
            print("❌ Video Downloader Helper extension is NOT installed!")
            print("\nPlease install the Video Downloader Helper extension from:")
            print("https://addons.mozilla.org/en-US/firefox/addon/video-downloadhelper/")
        
        # Close the browser
        driver.quit()
        print("\nFirefox check completed.")
        
    except Exception as e:
        print(f"❌ Error launching Firefox: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Check Firefox configuration for 101kg downloader")
    parser.add_argument("--profile", type=str, help="Path to Firefox profile with Video Downloader Helper")
    args = parser.parse_args()
    
    print("101kg Firefox Configuration Checker")
    print("===================================")
    
    success = check_firefox_configuration(args.profile)
    
    if success:
        print("\nTo use Firefox with the 101kg downloader, run:")
        if args.profile:
            print(f"python 101kg.py --browser firefox --browser-profile \"{args.profile}\"")
        else:
            print("python 101kg.py --browser firefox")
    else:
        print("\nPlease resolve the issues above before using Firefox with the 101kg downloader.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())