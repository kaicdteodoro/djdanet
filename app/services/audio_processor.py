import subprocess
from pathlib import Path

from app.core.logger import get_logger
from app.domain.entities import PitchShiftRequest, PitchShiftResult
from app.domain.enums import Status
from app.domain.exceptions import PitchShiftError

logger = get_logger(__name__)

SEMITONE_RATIO = 2 ** (1 / 12)


class AudioProcessor:
    """Applies audio transformations to existing local files via ffmpeg."""

    def shift_pitch(self, request: PitchShiftRequest) -> PitchShiftResult:
        """Shifts the pitch of an audio file while preserving tempo.

        Uses ffmpeg's rubberband filter so playback speed/duration is unchanged.

        Args:
            request: The pitch-shift request with input path and semitone offset.

        Returns:
            A PitchShiftResult with the outcome of the operation.

        Raises:
            PitchShiftError: If ffmpeg is unavailable or processing fails.
        """
        logger.info(
            "Shifting pitch: input=%s, semitones=%s, output=%s",
            request.input_path,
            request.semitones,
            request.output_path,
        )

        command = self._build_command(request)

        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=request.timeout,
            )
        except subprocess.CalledProcessError as exc:
            raise PitchShiftError(f"ffmpeg failed: {exc.stderr.strip()}") from exc
        except subprocess.TimeoutExpired as exc:
            raise PitchShiftError(
                f"ffmpeg timed out after {request.timeout}s"
            ) from exc
        except FileNotFoundError as exc:
            raise PitchShiftError("ffmpeg executable not found") from exc

        file_size = self._get_file_size(request.output_path)
        logger.info(
            "Pitch shift completed: %s (%s bytes)", request.output_path.name, file_size
        )

        return PitchShiftResult(
            input_path=request.input_path,
            output_path=request.output_path,
            semitones=request.semitones,
            status=Status.COMPLETED,
            file_size_bytes=file_size,
        )

    def _build_command(self, request: PitchShiftRequest) -> list[str]:
        """Builds the ffmpeg command line for a pitch-shift request.

        Args:
            request: The pitch-shift request.

        Returns:
            The ffmpeg command as a list of arguments.
        """
        pitch_factor = SEMITONE_RATIO**request.semitones

        return [
            "ffmpeg",
            "-y",
            "-i",
            str(request.input_path),
            "-af",
            f"rubberband=pitch={pitch_factor:.6f}",
            "-c:a",
            "libmp3lame",
            "-b:a",
            request.audio_bitrate,
            str(request.output_path),
        ]

    def _get_file_size(self, path: Path) -> int | None:
        """Gets the size of a file in bytes.

        Args:
            path: The file path.

        Returns:
            The file size in bytes, or None if the file doesn't exist.
        """
        if path.exists():
            return path.stat().st_size
        return None
