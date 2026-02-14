import pytest
from pathlib import Path

from app.services.file_manager import FileManager


class TestSanitizeFilename:
    def setup_method(self) -> None:
        self.fm = FileManager()

    def test_basic_sanitization(self) -> None:
        result = self.fm.sanitize_filename("My Video Title", "mp3")
        assert result == "My Video Title.mp3"

    def test_removes_unsafe_characters(self) -> None:
        result = self.fm.sanitize_filename('Video: "Best" <Ever>', "mp4")
        assert ":" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result

    def test_collapses_whitespace(self) -> None:
        result = self.fm.sanitize_filename("Video   with   spaces", "mp3")
        assert "   " not in result

    def test_empty_name_fallback(self) -> None:
        result = self.fm.sanitize_filename("", "mp3")
        assert result == "download.mp3"

    def test_truncates_long_names(self) -> None:
        long_name = "A" * 300
        result = self.fm.sanitize_filename(long_name, "mp3")
        assert len(result) <= 205  # 200 + ".mp3" + margin

    def test_strips_dots(self) -> None:
        result = self.fm.sanitize_filename("...hidden...", "mp4")
        assert not result.startswith(".")


class TestBuildOutputPath:
    def setup_method(self) -> None:
        self.fm = FileManager()

    def test_builds_correct_path(self, tmp_path: Path) -> None:
        result = self.fm.build_output_path("My Song", "abc123", "mp3", tmp_path)
        assert result.name == "My Song_[abc123].mp3"
        assert result.parent == tmp_path.resolve()

    def test_path_traversal_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Path traversal"):
            self.fm._validate_path_safety(
                tmp_path / ".." / ".." / "etc" / "passwd",
                tmp_path,
            )


class TestEnsureDirectory:
    def setup_method(self) -> None:
        self.fm = FileManager()

    def test_creates_directory(self, tmp_path: Path) -> None:
        new_dir = tmp_path / "new" / "nested"
        result = self.fm.ensure_directory(new_dir)
        assert result.exists()
        assert result.is_dir()
