from app.cli.main import _with_default_command, build_parser


class TestBuildParserDownload:
    def test_parses_required_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["download", "https://youtu.be/abc12345678", "mp3"])
        assert args.command == "download"
        assert args.url == "https://youtu.be/abc12345678"
        assert args.format == "mp3"

    def test_default_quality(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["download", "https://youtu.be/abc12345678", "mp4"])
        assert args.quality == "best"

    def test_verbose_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["download", "-v", "https://youtu.be/abc12345678", "mp3"]
        )
        assert args.verbose is True

    def test_playlist_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["download", "--playlist", "https://youtu.be/abc12345678", "mp3"]
        )
        assert args.playlist is True

    def test_custom_options(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "download",
            "https://youtu.be/abc12345678",
            "mp4",
            "--quality", "720p",
            "--max-retries", "5",
            "--timeout", "600",
        ])
        assert args.quality == "720p"
        assert args.max_retries == 5
        assert args.timeout == 600


class TestBuildParserPitch:
    def test_parses_required_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["pitch", "downloads/song.mp3"])
        assert args.command == "pitch"
        assert args.file == "downloads/song.mp3"

    def test_default_semitones_is_minus_one(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["pitch", "downloads/song.mp3"])
        assert args.semitones == -1.0

    def test_custom_semitones(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["pitch", "downloads/song.mp3", "--semitones", "2"]
        )
        assert args.semitones == 2.0

    def test_custom_output(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["pitch", "downloads/song.mp3", "--output", "downloads/out.mp3"]
        )
        assert str(args.output) == "downloads/out.mp3"


class TestWithDefaultCommand:
    def test_prepends_download_when_no_subcommand_given(self) -> None:
        result = _with_default_command(["https://youtu.be/abc12345678", "mp3"])
        assert result == ["download", "https://youtu.be/abc12345678", "mp3"]

    def test_leaves_explicit_download_subcommand(self) -> None:
        raw = ["download", "https://youtu.be/abc12345678", "mp3"]
        assert _with_default_command(raw) == raw

    def test_leaves_explicit_pitch_subcommand(self) -> None:
        raw = ["pitch", "downloads/song.mp3"]
        assert _with_default_command(raw) == raw

    def test_leaves_help_flag_untouched(self) -> None:
        assert _with_default_command(["--help"]) == ["--help"]
