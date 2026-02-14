from typing import Protocol

from app.domain.entities import DownloadRequest, DownloadResult


class DownloaderProtocol(Protocol):
    """Interface for video download implementations."""

    def download(self, request: DownloadRequest) -> DownloadResult:
        """Downloads a video according to the request specification.

        Args:
            request: The download request containing URL, format, and options.

        Returns:
            A DownloadResult with the outcome of the operation.
        """
        ...


class ProgressCallback(Protocol):
    """Interface for progress reporting during downloads."""

    def on_progress(self, downloaded_bytes: int, total_bytes: int | None) -> None:
        """Called when download progress is updated.

        Args:
            downloaded_bytes: Number of bytes downloaded so far.
            total_bytes: Total file size in bytes, or None if unknown.
        """
        ...

    def on_status(self, message: str) -> None:
        """Called when a status message should be displayed.

        Args:
            message: The status message to display.
        """
        ...


class FileManagerProtocol(Protocol):
    """Interface for file system operations."""

    def sanitize_filename(self, name: str, extension: str) -> str:
        """Sanitizes a filename for safe file system usage.

        Args:
            name: The raw filename.
            extension: The file extension without dot.

        Returns:
            A sanitized, safe filename.
        """
        ...
