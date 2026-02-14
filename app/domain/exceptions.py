class DjdanetError(Exception):
    """Base exception for all djdanet errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class InvalidURLError(DjdanetError):
    """Raised when the provided URL is not a valid YouTube URL."""


class InvalidFormatError(DjdanetError):
    """Raised when the requested format is not supported."""


class DownloadError(DjdanetError):
    """Raised when a download operation fails."""


class ConversionError(DjdanetError):
    """Raised when audio/video conversion fails."""


class NetworkError(DjdanetError):
    """Raised when a network-related error occurs."""
