# djdanet

Professional CLI tool for downloading YouTube videos in MP3 or MP4 format with maximum quality.

## Features

- Download YouTube videos as MP3 (320kbps) or MP4 (H.264/AAC)
- Rich progress bars and formatted output
- Automatic retry with exponential backoff
- File name sanitization and path safety
- Containerized with Docker
- Clean Architecture ready for API expansion

## Quick Start (Docker)

```bash
# Copy environment file
cp .env.example .env

# Build
docker compose build

# Download as MP3
docker compose run --rm djdanet "https://youtube.com/watch?v=VIDEO_ID" mp3

# Download as MP4
docker compose run --rm djdanet "https://youtube.com/watch?v=VIDEO_ID" mp4

# Download with specific quality
docker compose run --rm djdanet "https://youtube.com/watch?v=VIDEO_ID" mp4 --quality 720p
```

## Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run
python -m app.cli.main "https://youtube.com/watch?v=VIDEO_ID" mp3

# Run tests
pytest

# Lint and type check
ruff check app/ tests/
mypy app/
```

## CLI Usage

```
djdanet URL FORMAT [OPTIONS]

Positional arguments:
  url                   YouTube video or playlist URL
  format                Output format: mp3 or mp4

Options:
  --quality QUALITY     Video quality: best, 720p, 480p, 360p, 240p (default: best)
  --playlist            Download entire playlist
  --output-dir PATH     Override output directory
  --verbose, -v         Enable debug logging
  --max-retries N       Number of retry attempts (default: 3)
  --timeout SECONDS     Download timeout in seconds (default: 300)
```

## Project Structure

```
app/
  core/       - Configuration and logging
  domain/     - Entities, enums, exceptions, protocols
  services/   - Download and file management logic
  cli/        - CLI entry point and formatters
  utils/      - URL and format validators
```

## Requirements

- Python 3.12+
- ffmpeg (included in Docker image)
