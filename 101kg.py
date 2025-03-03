#!/usr/bin/env python3
"""
101 Karate Games Video Downloader

Main entry point script for downloading videos from Hotmart's 101 Karate Games platform.
Uses the VideoDownloader class to handle authentication, video extraction, and download.
"""
import argparse
from video_downloader import VideoDownloader


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
