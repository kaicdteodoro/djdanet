import time
from pathlib import Path
from typing import Any

import yt_dlp

from app.core.config import Settings
from app.core.logger import get_logger
from app.domain.entities import DownloadRequest, DownloadResult, Video
from app.domain.enums import Format, Quality, Status
from app.domain.exceptions import ConversionError, DownloadError, NetworkError
from app.domain.protocols import ProgressCallback
from app.services.file_manager import FileManager

logger = get_logger(__name__)


class VideoDownloader:
    """Core download service that uses yt-dlp to fetch YouTube videos."""

    def __init__(
        self,
        settings: Settings,
        file_manager: FileManager,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Initializes the downloader with dependencies.

        Args:
            settings: Application settings instance.
            file_manager: File manager for path operations.
            progress_callback: Optional callback for progress reporting.
        """
        self._settings = settings
        self._file_manager = file_manager
        self._progress_callback = progress_callback

    def download(self, request: DownloadRequest) -> DownloadResult:
        """Downloads a video according to the request specification.

        Args:
            request: The download request containing URL, format, and options.

        Returns:
            A DownloadResult with the outcome of the operation.
        """
        logger.info(
            "Starting download: url=%s, format=%s, quality=%s",
            request.url,
            request.output_format.value,
            request.quality.value,
        )

        output_dir = self._file_manager.ensure_directory(request.output_dir)

        # Extract metadata first (without stream URLs) to build the output path
        video_info = self._extract_info(request.url, request.timeout)
        video = self._build_video_entity(video_info)

        output_path = self._file_manager.build_output_path(
            title=video.title,
            video_id=video.video_id,
            extension=request.output_format.value,
            output_dir=output_dir,
        )

        last_error: Exception | None = None
        for attempt in range(1, request.max_retries + 1):
            try:
                logger.info("Download attempt %d/%d", attempt, request.max_retries)
                self._execute_download(request, output_path)

                file_size = self._file_manager.get_file_size(output_path)
                logger.info(
                    "Download completed: %s (%s bytes)",
                    output_path.name,
                    file_size,
                )

                return DownloadResult(
                    video=video,
                    output_format=request.output_format,
                    output_path=output_path,
                    status=Status.COMPLETED,
                    file_size_bytes=file_size,
                )
            except NetworkError:
                last_error = NetworkError(
                    f"Network error on attempt {attempt}/{request.max_retries}"
                )
                if attempt < request.max_retries:
                    wait = 2**attempt
                    logger.warning("Network error, retrying in %ds...", wait)
                    time.sleep(wait)
            except (DownloadError, ConversionError) as exc:
                last_error = exc
                if attempt < request.max_retries:
                    wait = 2**attempt
                    logger.warning(
                        "Error: %s. Retrying in %ds...", exc.message, wait
                    )
                    time.sleep(wait)

        error_msg = str(last_error) if last_error else "Unknown error"
        logger.error("All download attempts failed: %s", error_msg)

        return DownloadResult(
            video=video,
            output_format=request.output_format,
            output_path=output_path,
            status=Status.FAILED,
            error_message=error_msg,
        )

    def _extract_info(self, url: str, timeout: int) -> dict[str, Any]:
        """Extracts video metadata without downloading.

        Args:
            url: The YouTube video URL.
            timeout: Socket timeout in seconds.

        Returns:
            A dictionary containing video metadata from yt-dlp.

        Raises:
            NetworkError: If there's a connection or network issue.
            DownloadError: If metadata extraction fails.
        """
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": timeout,
            "extract_flat": False,
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info: dict[str, Any] = ydl.extract_info(url, download=False) or {}
                if not info:
                    raise DownloadError(f"Could not extract info from: {url}")
                logger.debug("Extracted info for: %s", info.get("title", "unknown"))
                return info
        except yt_dlp.utils.DownloadError as exc:
            error_str = str(exc).lower()
            if any(
                keyword in error_str
                for keyword in ("network", "connection", "timeout", "urlopen")
            ):
                raise NetworkError(f"Network error extracting info: {exc}") from exc
            raise DownloadError(f"Failed to extract video info: {exc}") from exc

    def _build_video_entity(self, info: dict[str, Any]) -> Video:
        """Builds a Video entity from yt-dlp info dictionary.

        Args:
            info: The yt-dlp info dictionary.

        Returns:
            A Video entity populated with metadata.
        """
        return Video(
            url=info.get("webpage_url", info.get("url", "")),
            video_id=info.get("id", "unknown"),
            title=info.get("title", "unknown"),
            duration=info.get("duration"),
            uploader=info.get("uploader"),
            thumbnail_url=info.get("thumbnail"),
        )

    def _execute_download(
        self,
        request: DownloadRequest,
        output_path: Path,
    ) -> None:
        """Executes the actual download and conversion via a fresh extract+download.

        Uses a single extract_info call with download=True so that yt-dlp
        resolves stream URLs and downloads in one session, avoiding 403 errors
        from expired URLs.

        Args:
            request: The download request.
            output_path: The target output file path.

        Raises:
            DownloadError: If the download fails.
            ConversionError: If post-processing/conversion fails.
            NetworkError: If there's a network issue during download.
        """
        opts = self._build_ydl_options(request, output_path)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(request.url, download=True)
        except yt_dlp.utils.PostProcessingError as exc:
            raise ConversionError(f"Conversion failed: {exc}") from exc
        except yt_dlp.utils.DownloadError as exc:
            error_str = str(exc).lower()
            if any(
                keyword in error_str
                for keyword in ("network", "connection", "timeout", "urlopen")
            ):
                raise NetworkError(f"Network error during download: {exc}") from exc
            raise DownloadError(f"Download failed: {exc}") from exc

    def _build_ydl_options(
        self, request: DownloadRequest, output_path: Path
    ) -> dict[str, Any]:
        """Builds yt-dlp options based on the download request.

        Args:
            request: The download request with format and quality.
            output_path: The target output file path.

        Returns:
            A dictionary of yt-dlp options.
        """
        # Output template: use the exact path we computed
        outtmpl = str(output_path.with_suffix(".%(ext)s"))

        opts: dict[str, Any] = {
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "socket_timeout": request.timeout,
            "noplaylist": not request.is_playlist,
            "overwrites": True,
            "progress_hooks": [self._progress_hook],
        }

        if request.output_format == Format.MP3:
            opts.update(self._mp3_options())
        else:
            opts.update(self._mp4_options(request.quality))

        return opts

    def _mp3_options(self) -> dict[str, Any]:
        """Returns yt-dlp options for MP3 extraction.

        Returns:
            A dictionary of yt-dlp options for MP3 output.
        """
        return {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                },
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
                {
                    "key": "EmbedThumbnail",
                },
            ],
            "writethumbnail": True,
        }

    def _mp4_options(self, quality: Quality) -> dict[str, Any]:
        """Returns yt-dlp options for MP4 download.

        Args:
            quality: The desired video quality.

        Returns:
            A dictionary of yt-dlp options for MP4 output.
        """
        format_str = self._quality_to_format_string(quality)

        return {
            "format": format_str,
            "merge_output_format": "mp4",
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                },
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
            ],
            "postprocessor_args": {
                "FFmpegVideoConvertor": [
                    "-c:v", self._settings.preferred_codec_video,
                    "-c:a", self._settings.preferred_codec_audio,
                ],
            },
        }

    def _quality_to_format_string(self, quality: Quality) -> str:
        """Converts a Quality enum to a yt-dlp format selection string.

        Args:
            quality: The desired quality level.

        Returns:
            A yt-dlp format selection string.
        """
        quality_map: dict[Quality, str] = {
            Quality.BEST: "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            Quality.Q720P: "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]",
            Quality.Q480P: "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]",
            Quality.Q360P: "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best[height<=360]",
            Quality.Q240P: "bestvideo[height<=240][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=240]+bestaudio/best[height<=240]",
        }
        return quality_map.get(quality, quality_map[Quality.BEST])

    def _progress_hook(self, data: dict[str, Any]) -> None:
        """Hook called by yt-dlp to report download progress.

        Args:
            data: Progress data dictionary from yt-dlp.
        """
        if self._progress_callback is None:
            return

        status = data.get("status", "")

        if status == "downloading":
            downloaded = data.get("downloaded_bytes", 0)
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            self._progress_callback.on_progress(downloaded, total)
        elif status == "finished":
            self._progress_callback.on_status("Download finished, processing...")
        elif status == "error":
            self._progress_callback.on_status("Error during download")
