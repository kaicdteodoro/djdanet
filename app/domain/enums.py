from enum import Enum


class Format(str, Enum):
    """Supported output formats."""

    MP3 = "mp3"
    MP4 = "mp4"


class Quality(str, Enum):
    """Supported video quality presets."""

    BEST = "best"
    Q720P = "720p"
    Q480P = "480p"
    Q360P = "360p"
    Q240P = "240p"


class Status(str, Enum):
    """Download status states."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"
