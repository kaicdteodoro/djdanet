from dataclasses import dataclass, field
from pathlib import Path

from app.domain.enums import Format, Quality, Status


@dataclass
class Video:
    """Represents a YouTube video with its metadata."""

    url: str
    video_id: str
    title: str
    duration: int | None = None
    uploader: str | None = None
    thumbnail_url: str | None = None

    @property
    def display_title(self) -> str:
        """Returns a display-friendly title."""
        return f"{self.title} [{self.video_id}]"


@dataclass
class DownloadRequest:
    """Represents a request to download a video."""

    url: str
    output_format: Format
    quality: Quality = Quality.BEST
    output_dir: Path = field(default_factory=lambda: Path("downloads"))
    is_playlist: bool = False
    max_retries: int = 3
    timeout: int = 300


@dataclass
class DownloadResult:
    """Represents the result of a download operation."""

    video: Video
    output_format: Format
    output_path: Path
    status: Status
    file_size_bytes: int | None = None
    error_message: str | None = None

    @property
    def is_success(self) -> bool:
        """Returns True if the download completed successfully."""
        return self.status == Status.COMPLETED
