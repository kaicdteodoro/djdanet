import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.domain.entities import PitchShiftRequest
from app.domain.enums import Status
from app.domain.exceptions import PitchShiftError
from app.services.audio_processor import SEMITONE_RATIO, AudioProcessor


class TestBuildCommand:
    def setup_method(self) -> None:
        self.processor = AudioProcessor()

    def test_includes_rubberband_filter_with_pitch_factor(self, tmp_path: Path) -> None:
        request = PitchShiftRequest(
            input_path=tmp_path / "in.mp3",
            output_path=tmp_path / "out.mp3",
            semitones=-1.0,
        )
        command = self.processor._build_command(request)

        expected_factor = SEMITONE_RATIO**-1.0
        assert command[0] == "ffmpeg"
        assert f"rubberband=pitch={expected_factor:.6f}" in command
        assert str(request.input_path) in command
        assert str(request.output_path) in command

    def test_uses_configured_bitrate(self, tmp_path: Path) -> None:
        request = PitchShiftRequest(
            input_path=tmp_path / "in.mp3",
            output_path=tmp_path / "out.mp3",
            semitones=-1.0,
            audio_bitrate="192k",
        )
        command = self.processor._build_command(request)
        assert "192k" in command


class TestShiftPitch:
    def setup_method(self) -> None:
        self.processor = AudioProcessor()

    def test_success_returns_completed_result(self, tmp_path: Path) -> None:
        input_path = tmp_path / "in.mp3"
        output_path = tmp_path / "out.mp3"
        input_path.write_bytes(b"fake audio")
        request = PitchShiftRequest(
            input_path=input_path, output_path=output_path, semitones=-1.0
        )

        def fake_run(*args: object, **kwargs: object) -> MagicMock:
            output_path.write_bytes(b"shifted audio")
            return MagicMock(returncode=0)

        with patch("subprocess.run", side_effect=fake_run) as mock_run:
            result = self.processor.shift_pitch(request)

        mock_run.assert_called_once()
        assert result.status == Status.COMPLETED
        assert result.is_success is True
        assert result.file_size_bytes == len(b"shifted audio")

    def test_ffmpeg_failure_raises_pitch_shift_error(self, tmp_path: Path) -> None:
        request = PitchShiftRequest(
            input_path=tmp_path / "in.mp3",
            output_path=tmp_path / "out.mp3",
            semitones=-1.0,
        )
        error = subprocess.CalledProcessError(1, "ffmpeg", stderr="boom")

        with patch("subprocess.run", side_effect=error), pytest.raises(
            PitchShiftError, match="ffmpeg failed"
        ):
            self.processor.shift_pitch(request)

    def test_timeout_raises_pitch_shift_error(self, tmp_path: Path) -> None:
        request = PitchShiftRequest(
            input_path=tmp_path / "in.mp3",
            output_path=tmp_path / "out.mp3",
            semitones=-1.0,
            timeout=5,
        )
        error = subprocess.TimeoutExpired("ffmpeg", 5)

        with patch("subprocess.run", side_effect=error), pytest.raises(
            PitchShiftError, match="timed out"
        ):
            self.processor.shift_pitch(request)

    def test_missing_ffmpeg_raises_pitch_shift_error(self, tmp_path: Path) -> None:
        request = PitchShiftRequest(
            input_path=tmp_path / "in.mp3",
            output_path=tmp_path / "out.mp3",
            semitones=-1.0,
        )

        with patch("subprocess.run", side_effect=FileNotFoundError()), pytest.raises(
            PitchShiftError, match="ffmpeg executable not found"
        ):
            self.processor.shift_pitch(request)
