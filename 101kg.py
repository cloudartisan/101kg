#!/usr/bin/env python3
"""
101 Karate Games Video Downloader

Main entry point script for downloading videos from Hotmart's 101 Karate Games platform.
Uses the VideoDownloader class to handle authentication, video extraction, and download.
"""
import argparse
import sys
import time
from video_downloader import VideoDownloader

# Import the logger module
import logger


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Download videos from 101 Karate Games')
    parser.add_argument('--email', help='Your Hotmart email/username', required=True)
    parser.add_argument('--password', help='Your Hotmart password', required=True)
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error'], 
                        default='info', help='Logging level (for file logging)')
    parser.add_argument('--no-log-file', action='store_true', 
                        help='Disable logging to file')
    parser.add_argument('--verbose', action='store_true',
                        help='Use the same log level for console as for the log file')
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
    
    # Initialize downloader
    downloader = VideoDownloader(args.email, args.password)
    start_time = time.time()
    
    try:
        # Attempt login
        logger.info("Logging in to Hotmart")
        if not downloader.login():
            logger.error("Failed to login. Exiting...")
            return 1
        
        # Download all lessons
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