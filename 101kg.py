#!/usr/bin/env python3
"""
101 Karate Games Video Downloader

Main entry point script for downloading videos from Hotmart's 101 Karate Games platform.
Uses the VideoDownloader class to handle authentication, video extraction, and download.
"""
import argparse
import sys
import time
import os
import json
from getpass import getpass
from video_downloader import VideoDownloader

# Import the logger module
import logger


def load_config(config_path=None):
    """Load configuration from a JSON file or create one if it doesn't exist."""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    
    config = {}
    
    # Try to load existing config
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"Loaded configuration from {config_path}")
        except Exception as e:
            print(f"Error loading config: {str(e)}")
    
    # Prompt for missing credentials if interactive
    if sys.stdin.isatty():
        if 'email' not in config or not config['email']:
            config['email'] = input("Enter your Hotmart email: ")
        
        if 'password' not in config or not config['password']:
            config['password'] = getpass("Enter your Hotmart password: ")
        
        # Save config if it was modified
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f)
            os.chmod(config_path, 0o600)  # Make the file readable only by the owner
            print(f"Configuration saved to {config_path}")
        except Exception as e:
            print(f"Error saving config: {str(e)}")
    
    return config


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Download videos from 101 Karate Games')
    parser.add_argument('--email', help='Your Hotmart email/username')
    parser.add_argument('--password', help='Your Hotmart password')
    parser.add_argument('--config', help='Path to config file with credentials')
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error'], 
                        default='info', help='Logging level (for file logging)')
    parser.add_argument('--no-log-file', action='store_true', 
                        help='Disable logging to file')
    parser.add_argument('--verbose', action='store_true',
                        help='Use the same log level for console as for the log file')
    parser.add_argument('--headless', action='store_true',
                        help='Run browser in headless mode')
    
    # Add specific download options
    parser.add_argument('--list', action='store_true', 
                        help='List available videos without downloading')
    parser.add_argument('--single', type=str, 
                        help='Download a single video by name or number')
    parser.add_argument('--url', type=str, 
                        help='Direct download URL for a video')
    parser.add_argument('--output', type=str, 
                        help='Output filename for single download')
    parser.add_argument('--indexes', type=str, 
                        help='Comma-separated list of video indexes to download')
    
    args = parser.parse_args()

    # Set up logging
    log_levels = {
        'debug': logger.DEBUG,
        'info': logger.INFO,
        'warning': logger.WARNING,
        'error': logger.ERROR
    }
    # Use the specified log level for the file, but keep INFO level for console by default
    # unless verbose mode is enabled
    console_level = log_levels[args.log_level] if args.verbose else log_levels['info']

    logger.setup_logger(
        level=log_levels[args.log_level],
        log_to_file=not args.no_log_file,
        console_level=console_level
    )

    logger.info("Starting 101 Karate Games downloader")
    
    # Load config if specified
    config = {}
    if args.config or not (args.email and args.password):
        config = load_config(args.config)
    
    # Command line args override config file
    email = args.email or config.get('email')
    password = args.password or config.get('password')
    
    # Ensure we have credentials
    if not email or not password:
        logger.error("Email and password are required. Use --email/--password options or a config file.")
        return 1

    # Initialize downloader
    downloader = VideoDownloader(email, password, headless=args.headless)
    start_time = time.time()

    try:
        # Attempt login
        logger.info("Logging in to Hotmart")
        if not downloader.login():
            logger.error("Failed to login. Exiting...")
            return 1
        
        # Handle direct URL download
        if args.url:
            output_name = args.output or "downloaded_video"
            logger.info(f"Downloading from URL to {output_name}")
            if downloader.download_video(args.url, output_name):
                logger.info(f"Successfully downloaded: {output_name}")
            else:
                logger.error(f"Failed to download from URL: {args.url}")
            return 0

        # List all lessons
        logger.info("Fetching lesson list")
        lessons = downloader.get_all_lessons()
        
        if not lessons:
            logger.error("No lessons found. Please check your account and try again.")
            return 1
        
        logger.info(f"Found {len(lessons)} lessons:")
        for i, lesson in enumerate(lessons, 1):
            logger.info(f"{i}. {lesson['title']} (hash: {lesson['hash']})")
        
        # Just list mode
        if args.list:
            return 0
        
        # Single video download
        if args.single:
            found = False
            for i, lesson in enumerate(lessons, 1):
                # Match by index or name (case insensitive)
                if args.single.lower() in lesson['title'].lower() or args.single == str(i):
                    found = True
                    logger.info(f"Downloading {lesson['title']}...")
                    lesson_url = f"{downloader.base_url}/lesson/{lesson['hash']}"
                    video_urls = downloader.extract_video_url(lesson_url)
                    
                    if not video_urls:
                        logger.error(f"No videos found for {lesson['title']}")
                        continue
                    
                    for part_idx, (part_suffix, video_url) in enumerate(video_urls, 1):
                        filename = args.output or f"{i:03d}_{lesson['title']}"
                        if part_suffix:
                            filename = f"{filename}_{part_suffix}"
                        
                        if downloader.download_video(video_url, filename):
                            logger.info(f"Successfully downloaded: {filename}")
                        else:
                            logger.error(f"Failed to download: {filename}")
                    break
            
            if not found:
                logger.error(f"No lesson found matching '{args.single}'")
            return 0 if found else 1
        
        # Download videos by index
        if args.indexes:
            try:
                indexes = [int(i.strip()) for i in args.indexes.split(',')]
                success_count = 0
                fail_count = 0
                
                for idx in indexes:
                    if 1 <= idx <= len(lessons):
                        lesson = lessons[idx-1]
                        logger.info(f"Downloading {lesson['title']}...")
                        lesson_url = f"{downloader.base_url}/lesson/{lesson['hash']}"
                        video_urls = downloader.extract_video_url(lesson_url)
                        
                        if not video_urls:
                            logger.error(f"No videos found for {lesson['title']}")
                            fail_count += 1
                            continue
                        
                        for part_idx, (part_suffix, video_url) in enumerate(video_urls, 1):
                            filename = f"{idx:03d}_{lesson['title']}"
                            if part_suffix:
                                filename = f"{filename}_{part_suffix}"
                            
                            if downloader.download_video(video_url, filename):
                                logger.info(f"Successfully downloaded: {filename}")
                                success_count += 1
                            else:
                                logger.error(f"Failed to download: {filename}")
                                fail_count += 1
                    else:
                        logger.error(f"Invalid index: {idx}")
                        fail_count += 1
                
                logger.info(f"Download summary: {success_count} successes, {fail_count} failures")
                return 0 if success_count > 0 else 1
            except ValueError:
                logger.error(f"Invalid index format: {args.indexes}")
                return 1

        # Download all videos
        logger.info("Starting download of all lessons")
        downloader.download_all_lessons()

        # Log completion
        elapsed_time = time.time() - start_time
        logger.info(f"Download completed successfully in {elapsed_time:.2f} seconds")
        return 0

    except KeyboardInterrupt:
        logger.warning("Download interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return 1
    finally:
        logger.info("Closing browser and cleaning up")
        downloader.close()


if __name__ == "__main__":
    sys.exit(main())