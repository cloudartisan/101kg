# 101 Karate Games Video Downloader

![Tests](https://github.com/cloudartisan/101kg/workflows/Python%20Tests/badge.svg)

This repository contains Python modules to automate the login, extraction, and download of videos from Hotmart's 101 Karate Games platform. For personal use only, of course. It requires a paid login.

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
1. **First Time Run** (creates a config file with your credentials):
   ```sh
   python 101kg.py
   ```
   This will prompt for your email and password and store them securely in `config.json`.

2. **Run with Command Line Credentials** (alternative to config file):
   ```sh
   python 101kg.py --email your_email@example.com --password your_password
   ```

3. **Downloaded videos** will be saved in the `videos/` directory.

### Command Line Options

#### Authentication Options:
- `--email`: Your Hotmart email/username
- `--password`: Your Hotmart password
- `--config`: Path to config file with credentials (default: config.json in script directory)

#### Logging Options:
- `--log-level`: Logging level - debug, info, warning, error (default: info)
- `--no-log-file`: Disable logging to file
- `--verbose`: Use the same log level for console as for the log file
- `--headless`: Run browser in headless mode

#### Download Selection Options:
- `--list`: List available videos without downloading anything
- `--single NAME_OR_NUMBER`: Download a specific video by name or index number
- `--url DIRECT_URL`: Download from a direct video URL
- `--output FILENAME`: Specify output filename for downloads
- `--indexes "1,3,5"`: Download specific videos by index numbers (comma-separated list)

### Example Commands

```sh
# List all available videos
python 101kg.py --list

# Download a specific video by name (substring match, case-insensitive)
python 101kg.py --single "Clock Game"

# Download a specific video by index number
python 101kg.py --single 1

# Download from a direct URL
python 101kg.py --url "https://vod-akm.play.hotmart.com/video/..." --output "clock_game"

# Download multiple specific videos by index
python 101kg.py --indexes "1,3,5"

# Enable debug logging
python 101kg.py --log-level debug

# Run in headless mode
python 101kg.py --headless
```

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

# Run tests and check for failing tests (look for FAILED in output)
pytest -v | grep FAILED || echo "All tests passed"

# Generate coverage report for all modules
pytest --cov=.

# Get module-specific coverage reports
pytest --cov=url_extractor
pytest --cov=browser_manager
pytest --cov=video_downloader

# Generate detailed coverage report with line numbers of missing coverage
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_url_utils.py

# Run specific test class or method
pytest tests/test_url_extractor.py::TestJavaScriptGeneration
pytest tests/test_url_extractor.py::TestJavaScriptGeneration::test_resolution_script

# Run tests in verbose mode to see individual test results
pytest -v

# Generate HTML coverage report (creates htmlcov directory)
pytest --cov=. --cov-report=html
```

### Current Test Coverage Summary

```
Name                       Stmts   Miss  Cover
----------------------------------------------
101kg.py                     95     35    63%
browser_manager.py          186     21    89%
check_firefox.py             14      2    86%
logger.py                    42      0   100%
url_extractor.py            212      9    96%
url_utils.py                 76      2    97%
video_downloader.py        1034    380    63%
tests/__init__.py             0      0   100%
tests/conftest.py            60      0   100%
tests/test_101kg.py          59      0   100%
tests/test_audio.py          40      0   100%
tests/test_browser_manager.py  140      0   100%
tests/test_logger.py        107      1    99%
tests/test_url_extractor.py  280      0   100%
tests/test_url_utils.py       91      0   100%
tests/test_video_downloader.py  498      0   100%
----------------------------------------------
TOTAL                      2934    450    85%
```

Key modules and their coverage:
- **url_extractor.py**: 96% coverage (212 statements, 9 missed)
- **url_utils.py**: 97% coverage (76 statements, 2 missed)
- **browser_manager.py**: 89% coverage (186 statements, 21 missed)
- **logger.py**: 100% coverage (42 statements, 0 missed)
- **video_downloader.py**: 63% coverage (1034 statements, 380 missed)

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

### Advanced Debugging
If you encounter download issues with a specific video:

1. First list the available videos:
   ```sh
   python 101kg.py --list
   ```
   Note the index of the problematic video.

2. Try downloading it directly:
   ```sh
   python 101kg.py --single 3 --log-level debug
   ```

3. If you have a specific URL to test:
   ```sh
   python 101kg.py --url "https://vod-akm.play.hotmart.com/video/..." --output "test_video" --log-level debug
   ```

4. The script will attempt multiple download methods in sequence:
   - Helper approach (mimics browser download helper extensions)
   - Direct page navigation and video extraction
   - Browser-based download with authenticated session
   - Standard HTTP methods with token authentication
   - Direct video recording via browser (as last resort)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
