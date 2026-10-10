from pathlib import Path

import pytest

from app.domain.enums import Format, Quality
from app.domain.exceptions import InvalidAudioFileError, InvalidFormatError, InvalidURLError
from app.utils.validators import (
    validate_format,
    validate_input_file,
    validate_quality,
    validate_semitones,
    validate_url,
)


class TestValidateUrl:
    def test_valid_watch_url(self) -> None:
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert validate_url(url) == url

    def test_valid_short_url(self) -> None:
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert validate_url(url) == url

    def test_valid_playlist_url(self) -> None:
        url = "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
        assert validate_url(url) == url

    def test_valid_shorts_url(self) -> None:
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        assert validate_url(url) == url

    def test_valid_music_url(self) -> None:
        url = "https://music.youtube.com/watch?v=dQw4w9WgXcQ"
        assert validate_url(url) == url

    def test_valid_video_id(self) -> None:
        assert validate_url("dQw4w9WgXcQ") == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_valid_video_id_with_dash(self) -> None:
        assert validate_url("oCYsBtsCiw8") == "https://www.youtube.com/watch?v=oCYsBtsCiw8"

    def test_valid_video_id_strips_whitespace(self) -> None:
        assert validate_url("  dQw4w9WgXcQ  ") == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(InvalidURLError):
            validate_url("https://example.com/video")

    def test_empty_url_raises(self) -> None:
        with pytest.raises(InvalidURLError):
            validate_url("")

    def test_invalid_short_string_raises(self) -> None:
        with pytest.raises(InvalidURLError):
            validate_url("abc")

    def test_strips_whitespace(self) -> None:
        url = "  https://youtu.be/dQw4w9WgXcQ  "
        assert validate_url(url) == url.strip()


class TestValidateFormat:
    def test_mp3(self) -> None:
        assert validate_format("mp3") == Format.MP3

    def test_mp4(self) -> None:
        assert validate_format("mp4") == Format.MP4

    def test_uppercase(self) -> None:
        assert validate_format("MP3") == Format.MP3

    def test_invalid_raises(self) -> None:
        with pytest.raises(InvalidFormatError):
            validate_format("wav")


class TestValidateQuality:
    def test_best(self) -> None:
        assert validate_quality("best") == Quality.BEST

    def test_720p(self) -> None:
        assert validate_quality("720p") == Quality.Q720P

    def test_invalid_raises(self) -> None:
        with pytest.raises(InvalidFormatError):
            validate_quality("4k")


class TestValidateInputFile:
    def test_existing_file_returns_resolved_path(self, tmp_path: Path) -> None:
        audio_file = tmp_path / "song.mp3"
        audio_file.write_bytes(b"data")
        assert validate_input_file(str(audio_file)) == audio_file.resolve()

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(InvalidAudioFileError, match="File not found"):
            validate_input_file(str(tmp_path / "missing.mp3"))

    def test_directory_raises(self, tmp_path: Path) -> None:
        with pytest.raises(InvalidAudioFileError, match="Not a file"):
            validate_input_file(str(tmp_path))

    def test_empty_path_raises(self) -> None:
        with pytest.raises(InvalidAudioFileError, match="cannot be empty"):
            validate_input_file("")


class TestValidateSemitones:
    def test_negative_value_accepted(self) -> None:
        assert validate_semitones(-1.0) == -1.0

    def test_positive_value_accepted(self) -> None:
        assert validate_semitones(2.0) == 2.0

    def test_zero_raises(self) -> None:
        with pytest.raises(InvalidFormatError, match="cannot be zero"):
            validate_semitones(0)

    def test_out_of_range_raises(self) -> None:
        with pytest.raises(InvalidFormatError, match="within"):
            validate_semitones(25.0)
