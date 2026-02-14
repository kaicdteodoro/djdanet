import argparse
import sys
from pathlib import Path

from app.cli.formatters import (
    RichProgressCallback,
    print_error,
    print_header,
    print_info,
    print_success,
)
from app.core.config import get_settings
from app.core.logger import get_logger
from app.domain.entities import DownloadRequest
from app.domain.exceptions import DjdanetError
from app.services.downloader import VideoDownloader
from app.services.file_manager import FileManager
from app.utils.validators import validate_format, validate_quality, validate_url

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Builds the CLI argument parser.

    Returns:
        A configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="djdanet",
        description="Professional YouTube downloader - MP3 and MP4 with maximum quality",
    )

    parser.add_argument(
        "url",
        type=str,
        help="YouTube URL or video ID (e.g. dQw4w9WgXcQ)",
    )
    parser.add_argument(
        "format",
        type=str,
        choices=["mp3", "mp4"],
        help="Output format (mp3 or mp4)",
    )
    parser.add_argument(
        "--quality",
        type=str,
        default="best",
        help="Video quality: best, 720p, 480p, 360p, 240p (default: best)",
    )
    parser.add_argument(
        "--playlist",
        action="store_true",
        default=False,
        help="Download entire playlist",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override output directory",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable verbose/debug logging",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=None,
        help="Number of retry attempts (default: 3)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Download timeout in seconds (default: 300)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI application.

    Args:
        argv: Command line arguments. Uses sys.argv if None.

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = get_settings()

    if args.verbose:
        settings.log_level = "DEBUG"

    print_header()

    try:
        url = validate_url(args.url)
        output_format = validate_format(args.format)
        quality = validate_quality(args.quality)
    except DjdanetError as exc:
        print_error(exc.message)
        logger.error("Validation error: %s", exc.message)
        return 1

    output_dir = args.output_dir or settings.output_dir
    max_retries = args.max_retries or settings.max_retries
    timeout = args.timeout or settings.download_timeout

    request = DownloadRequest(
        url=url,
        output_format=output_format,
        quality=quality,
        output_dir=output_dir,
        is_playlist=args.playlist,
        max_retries=max_retries,
        timeout=timeout,
    )

    print_info(f"URL: {request.url}")
    print_info(f"Format: {request.output_format.value.upper()}")
    print_info(f"Quality: {request.quality.value}")
    print_info(f"Output: {request.output_dir}")

    file_manager = FileManager()
    progress = RichProgressCallback()
    downloader = VideoDownloader(
        settings=settings,
        file_manager=file_manager,
        progress_callback=progress,
    )

    try:
        progress.start()
        result = downloader.download(request)
        progress.stop()

        if result.is_success:
            print_success(result)
            return 0

        print_error(result.error_message or "Download failed")
        return 1

    except DjdanetError as exc:
        progress.stop()
        print_error(exc.message)
        logger.error("Download error: %s", exc.message)
        return 1
    except KeyboardInterrupt:
        progress.stop()
        print_error("Download cancelled by user")
        logger.info("Download cancelled by user")
        return 1
    except Exception as exc:
        progress.stop()
        print_error(f"Unexpected error: {exc}")
        logger.exception("Unexpected error occurred")
        return 1


if __name__ == "__main__":
    sys.exit(main())
