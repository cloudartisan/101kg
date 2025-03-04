# 101 Karate Games Video Downloader

![Tests](https://github.com/cloudartisan/101kg/workflows/Python%20Tests/badge.svg)

This repository contains Python modules to automate the login, extraction, and download of videos from Hotmart's 101 Karate Games platform.

## Features
- Automates login to Hotmart
- Extracts video URL from lesson pages using advanced techniques
- Supports MP4 and HLS (.m3u8) downloads
- Uses Selenium for browser automation
- Handles cookie policy popups and other overlays
- Comprehensive test suite for reliability

## Prerequisites
- Python 3 installed
- Google Chrome installed
- WebDriver (managed automatically via `webdriver-manager`)
- `ffmpeg` installed (for HLS video downloads)

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/cloudartisan/101kg.git
   cd 101kg
   ```
2. Create a virtual environment:
   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage
1. **Run the script with your login credentials**:
   ```sh
   ./101kg.py --email your_email@example.com --password your_password
   ```

   Or if you prefer using python directly:
   ```sh
   python 101kg.py --email your_email@example.com --password your_password
   ```

2. **Downloaded videos** will be saved in the `videos/` directory.

### Command Line Options

- `--email`: Your Hotmart email/username (required)
- `--password`: Your Hotmart password (required)
- `--log-level`: Logging level - debug, info, warning, error (default: info)
- `--no-log-file`: Disable logging to file
- `--verbose`: Use the same log level for console as for the log file
- `--headless`: Run browser in headless mode

## Project Structure
- `101kg.py` - Main entry point script
- `browser_manager.py` - Browser initialization and management
- `logger.py` - Logging configuration and utilities
- `url_extractor.py` - Specialized URL extraction logic
- `url_utils.py` - Shared URL utility functions
- `video_downloader.py` - Core downloader class handling authentication and video extraction

## Development

### Running Tests

To run the unit tests:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_url_utils.py

# Run tests by marker
pytest -m "not slow"
```

## Notes
- The script logs in, navigates to the lesson page, extracts the video URL, and downloads it.
- If the video is in `.m3u8` format, `ffmpeg` is required to convert it to MP4.
- This script is for personal use only and should not be used to distribute copyrighted material.

## Troubleshooting
- Ensure that your Hotmart credentials are correct.
- If Chrome or WebDriver issues arise, update them:
  ```sh
  pip install --upgrade selenium webdriver-manager
  ```
- If login fails, Hotmart may have changed its authentication flow, requiring script adjustments.
- For cookie popup issues, the script includes automatic handling - if this fails, please report the issue.
- Run with `--log-level debug` for detailed logs to help troubleshoot issues.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.