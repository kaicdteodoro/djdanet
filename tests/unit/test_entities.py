from pathlib import Path

from app.domain.entities import DownloadResult, PitchShiftResult, Video
from app.domain.enums import Format, Status


class TestVideo:
    def test_display_title(self) -> None:
        video = Video(
            url="https://youtube.com/watch?v=abc123",
            video_id="abc123",
            title="My Video",
        )
        assert video.display_title == "My Video [abc123]"


class TestDownloadResult:
    def test_is_success_completed(self) -> None:
        result = DownloadResult(
            video=Video(url="", video_id="x", title="t"),
            output_format=Format.MP3,
            output_path=Path("/tmp/test.mp3"),
            status=Status.COMPLETED,
        )
        assert result.is_success is True

    def test_is_success_failed(self) -> None:
        result = DownloadResult(
            video=Video(url="", video_id="x", title="t"),
            output_format=Format.MP3,
            output_path=Path("/tmp/test.mp3"),
            status=Status.FAILED,
        )
        assert result.is_success is False


class TestPitchShiftResult:
    def test_is_success_completed(self) -> None:
        result = PitchShiftResult(
            input_path=Path("/tmp/in.mp3"),
            output_path=Path("/tmp/out.mp3"),
            semitones=-1.0,
            status=Status.COMPLETED,
        )
        assert result.is_success is True

    def test_is_success_failed(self) -> None:
        result = PitchShiftResult(
            input_path=Path("/tmp/in.mp3"),
            output_path=Path("/tmp/out.mp3"),
            semitones=-1.0,
            status=Status.FAILED,
        )
        assert result.is_success is False
