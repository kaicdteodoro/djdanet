import re

from app.domain.enums import Format, Quality
from app.domain.exceptions import InvalidFormatError, InvalidURLError

YOUTUBE_URL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"^https?://(www\.)?youtube\.com/watch\?v=[\w-]{11}"
    ),
    re.compile(
        r"^https?://(www\.)?youtube\.com/playlist\?list=[\w-]+"
    ),
    re.compile(
        r"^https?://youtu\.be/[\w-]{11}"
    ),
    re.compile(
        r"^https?://(www\.)?youtube\.com/shorts/[\w-]{11}"
    ),
    re.compile(
        r"^https?://music\.youtube\.com/watch\?v=[\w-]{11}"
    ),
]

VIDEO_ID_PATTERN: re.Pattern[str] = re.compile(r"^[\w-]{11}$")


def validate_url(url: str) -> str:
    """Validates a YouTube URL or video ID and returns a full URL.

    Accepts either a full YouTube URL or a bare 11-character video ID.
    When a video ID is provided, it is expanded to a full YouTube URL.

    Args:
        url: A YouTube URL or video ID.

    Returns:
        A validated full YouTube URL.

    Raises:
        InvalidURLError: If the input is not a valid YouTube URL or video ID.
    """
    cleaned = url.strip()
    if not cleaned:
        raise InvalidURLError("URL/ID cannot be empty")

    if VIDEO_ID_PATTERN.match(cleaned):
        return f"https://www.youtube.com/watch?v={cleaned}"

    for pattern in YOUTUBE_URL_PATTERNS:
        if pattern.match(cleaned):
            return cleaned

    raise InvalidURLError(f"Invalid YouTube URL or video ID: {cleaned}")


def validate_format(fmt: str) -> Format:
    """Validates and converts a format string to a Format enum.

    Args:
        fmt: The format string (e.g., "mp3", "mp4").

    Returns:
        The corresponding Format enum value.

    Raises:
        InvalidFormatError: If the format string is not supported.
    """
    try:
        return Format(fmt.lower().strip())
    except ValueError:
        valid = ", ".join(f.value for f in Format)
        raise InvalidFormatError(
            f"Unsupported format '{fmt}'. Valid formats: {valid}"
        ) from None


def validate_quality(quality: str) -> Quality:
    """Validates and converts a quality string to a Quality enum.

    Args:
        quality: The quality string (e.g., "best", "720p").

    Returns:
        The corresponding Quality enum value.

    Raises:
        InvalidFormatError: If the quality string is not recognized.
    """
    try:
        return Quality(quality.lower().strip())
    except ValueError:
        valid = ", ".join(q.value for q in Quality)
        raise InvalidFormatError(
            f"Unsupported quality '{quality}'. Valid options: {valid}"
        ) from None
