import re
import unicodedata
from pathlib import Path

from app.core.logger import get_logger

logger = get_logger(__name__)

MAX_FILENAME_LENGTH = 200
UNSAFE_CHARS_PATTERN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WHITESPACE_PATTERN = re.compile(r"\s+")


class FileManager:
    """Handles file system operations including sanitization and path validation."""

    def sanitize_filename(self, name: str, extension: str) -> str:
        """Sanitizes a filename by removing unsafe characters and normalizing unicode.

        Args:
            name: The raw filename without extension.
            extension: The file extension without the leading dot.

        Returns:
            A sanitized filename safe for use on all major file systems.
        """
        normalized = unicodedata.normalize("NFKD", name)
        cleaned = UNSAFE_CHARS_PATTERN.sub("", normalized)
        cleaned = WHITESPACE_PATTERN.sub(" ", cleaned).strip()
        cleaned = cleaned.strip(".")

        if not cleaned:
            cleaned = "download"

        if len(cleaned) > MAX_FILENAME_LENGTH:
            cleaned = cleaned[:MAX_FILENAME_LENGTH].rstrip()

        filename = f"{cleaned}.{extension}"
        logger.debug("Sanitized filename: '%s' -> '%s'", name, filename)
        return filename

    def build_output_path(
        self, title: str, video_id: str, extension: str, output_dir: Path
    ) -> Path:
        """Builds a safe output file path following the naming convention.

        Args:
            title: The video title.
            video_id: The YouTube video ID.
            extension: The file extension without dot.
            output_dir: The target output directory.

        Returns:
            A fully resolved, safe output Path.
        """
        base_name = f"{title}_[{video_id}]"
        filename = self.sanitize_filename(base_name, extension)
        output_path = output_dir.resolve() / filename

        self._validate_path_safety(output_path, output_dir)
        return output_path

    def ensure_directory(self, path: Path) -> Path:
        """Creates a directory if it doesn't exist.

        Args:
            path: The directory path to ensure.

        Returns:
            The resolved directory Path.
        """
        resolved = path.resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        logger.debug("Ensured directory exists: %s", resolved)
        return resolved

    def get_file_size(self, path: Path) -> int | None:
        """Gets the size of a file in bytes.

        Args:
            path: The file path.

        Returns:
            The file size in bytes, or None if the file doesn't exist.
        """
        if path.exists():
            return path.stat().st_size
        return None

    def _validate_path_safety(self, file_path: Path, base_dir: Path) -> None:
        """Validates that a file path doesn't escape the base directory.

        Args:
            file_path: The target file path to validate.
            base_dir: The base directory that should contain the file.

        Raises:
            ValueError: If the file path would escape the base directory.
        """
        resolved_file = file_path.resolve()
        resolved_base = base_dir.resolve()

        if not str(resolved_file).startswith(str(resolved_base)):
            logger.error(
                "Path traversal attempt detected: %s escapes %s",
                resolved_file,
                resolved_base,
            )
            raise ValueError(
                f"Path traversal detected: {resolved_file} is outside {resolved_base}"
            )
