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

# Try importing logger module, fall back to simple print function if unavailable
try:
    import logger
except ImportError:
    # Create a simple fallback logger
    class LogLevel:
        DEBUG = 10
        INFO = 20
        WARNING = 30
        ERROR = 40
    
    class FallbackLogger:
        DEBUG = LogLevel.DEBUG
        INFO = LogLevel.INFO
        WARNING = LogLevel.WARNING
        ERROR = LogLevel.ERROR
        
        @staticmethod
        def setup_logger(level=LogLevel.INFO, log_to_file=True):
            print(f"Using fallback logger (level: {level})")
            return FallbackLogger
            
        @staticmethod
        def debug(msg, *args, **kwargs): 
            print(f"DEBUG: {msg}")
            
        @staticmethod
        def info(msg, *args, **kwargs): 
            print(f"INFO: {msg}")
            
        @staticmethod
        def warning(msg, *args, **kwargs): 
            print(f"WARNING: {msg}")
            
        @staticmethod
        def error(msg, *args, **kwargs): 
            print(f"ERROR: {msg}")
            exc_info = kwargs.get('exc_info', False)
            if exc_info:
                import traceback
                traceback.print_exc()
    
    logger = FallbackLogger


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Download videos from 101 Karate Games')
    parser.add_argument('--email', help='Your Hotmart email/username', required=True)
    parser.add_argument('--password', help='Your Hotmart password', required=True)
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error'], 
                        default='info', help='Logging level')
    parser.add_argument('--no-log-file', action='store_true', 
                        help='Disable logging to file')
    args = parser.parse_args()
    
    # Set up logging
    log_levels = {
        'debug': logger.DEBUG,
        'info': logger.INFO,
        'warning': logger.WARNING,
        'error': logger.ERROR
    }
    logger.setup_logger(
        level=log_levels[args.log_level],
        log_to_file=not args.no_log_file
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