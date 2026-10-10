import argparse
import sys
from pathlib import Path

from app.cli.formatters import (
    RichProgressCallback,
    print_error,
    print_header,
    print_info,
    print_pitch_success,
    print_success,
)
from app.core.config import get_settings
from app.core.logger import get_logger
from app.domain.entities import DownloadRequest, PitchShiftRequest
from app.domain.exceptions import DjdanetError
from app.services.audio_processor import AudioProcessor
from app.services.downloader import VideoDownloader
from app.services.file_manager import FileManager
from app.utils.validators import (
    validate_format,
    validate_input_file,
    validate_quality,
    validate_semitones,
    validate_url,
)

logger = get_logger(__name__)

KNOWN_COMMANDS = frozenset({"download", "pitch"})


def build_parser() -> argparse.ArgumentParser:
    """Builds the CLI argument parser.

    Returns:
        A configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="djdanet",
        description="Professional YouTube downloader - MP3 and MP4 with maximum quality",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_download_subparser(subparsers)
    _add_pitch_subparser(subparsers)

    return parser


def _add_download_subparser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    """Registers the 'download' subcommand.

    Args:
        subparsers: The subparsers action to attach the subcommand to.
    """
    download = subparsers.add_parser(
        "download", help="Download a YouTube video as MP3 or MP4"
    )
    download.add_argument(
        "url",
        type=str,
        help="YouTube URL or video ID (e.g. dQw4w9WgXcQ)",
    )
    download.add_argument(
        "format",
        type=str,
        choices=["mp3", "mp4"],
        help="Output format (mp3 or mp4)",
    )
    download.add_argument(
        "--quality",
        type=str,
        default="best",
        help="Video quality: best, 720p, 480p, 360p, 240p (default: best)",
    )
    download.add_argument(
        "--playlist",
        action="store_true",
        default=False,
        help="Download entire playlist",
    )
    download.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override output directory",
    )
    download.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable verbose/debug logging",
    )
    download.add_argument(
        "--max-retries",
        type=int,
        default=None,
        help="Number of retry attempts (default: 3)",
    )
    download.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Download timeout in seconds (default: 300)",
    )
    download.add_argument(
        "--cookies-from-browser",
        type=str,
        default=None,
        help="Extract cookies from a local browser (chrome, firefox, edge, ...) "
        "to bypass YouTube's bot/age checks",
    )


def _add_pitch_subparser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    """Registers the 'pitch' subcommand.

    Args:
        subparsers: The subparsers action to attach the subcommand to.
    """
    pitch = subparsers.add_parser(
        "pitch", help="Shift the pitch of an existing local audio file"
    )
    pitch.add_argument(
        "file",
        type=str,
        help="Path to the local audio file to pitch-shift",
    )
    pitch.add_argument(
        "--semitones",
        type=float,
        default=-1.0,
        help="Semitones to shift; negative lowers pitch (default: -1, i.e. meio tom abaixo)",
    )
    pitch.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Override output file path",
    )
    pitch.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable verbose/debug logging",
    )
    pitch.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Processing timeout in seconds (default: 300)",
    )


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI application.

    Args:
        argv: Command line arguments. Uses sys.argv if None.

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    raw_args = sys.argv[1:] if argv is None else list(argv)
    raw_args = _with_default_command(raw_args)

    parser = build_parser()
    args = parser.parse_args(raw_args)

    print_header()

    if args.command == "pitch":
        return _run_pitch(args)
    return _run_download(args)


def _with_default_command(raw_args: list[str]) -> list[str]:
    """Prepends the 'download' subcommand when none was given, for backward compatibility.

    Args:
        raw_args: The raw CLI arguments as passed by the user.

    Returns:
        The arguments with an explicit subcommand as the first element.
    """
    if raw_args and raw_args[0] in KNOWN_COMMANDS:
        return raw_args
    if raw_args and raw_args[0] in ("-h", "--help"):
        return raw_args
    return ["download", *raw_args]


def _run_download(args: argparse.Namespace) -> int:
    """Runs the download workflow.

    Args:
        args: Parsed CLI arguments for the 'download' subcommand.

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    settings = get_settings()
    if args.verbose:
        settings.log_level = "DEBUG"

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
        cookies_from_browser=args.cookies_from_browser,
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


def _run_pitch(args: argparse.Namespace) -> int:
    """Runs the pitch-shift workflow.

    Args:
        args: Parsed CLI arguments for the 'pitch' subcommand.

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    settings = get_settings()
    if args.verbose:
        settings.log_level = "DEBUG"

    try:
        input_path = validate_input_file(args.file)
        semitones = validate_semitones(args.semitones)
    except DjdanetError as exc:
        print_error(exc.message)
        logger.error("Validation error: %s", exc.message)
        return 1

    file_manager = FileManager()
    output_path = args.output or file_manager.build_pitch_output_path(
        input_path, semitones
    )
    timeout = args.timeout or settings.download_timeout

    request = PitchShiftRequest(
        input_path=input_path,
        output_path=output_path,
        semitones=semitones,
        audio_bitrate=settings.audio_bitrate,
        timeout=timeout,
    )

    print_info(f"Input: {request.input_path}")
    print_info(f"Semitones: {request.semitones:+g}")
    print_info(f"Output: {request.output_path}")

    processor = AudioProcessor()

    try:
        result = processor.shift_pitch(request)
        print_pitch_success(result)
        return 0
    except DjdanetError as exc:
        print_error(exc.message)
        logger.error("Pitch shift error: %s", exc.message)
        return 1
    except KeyboardInterrupt:
        print_error("Pitch shift cancelled by user")
        logger.info("Pitch shift cancelled by user")
        return 1
    except Exception as exc:
        print_error(f"Unexpected error: {exc}")
        logger.exception("Unexpected error occurred")
        return 1


if __name__ == "__main__":
    sys.exit(main())
