from app.cli.main import build_parser


class TestBuildParser:
    def test_parses_required_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["https://youtu.be/abc12345678", "mp3"])
        assert args.url == "https://youtu.be/abc12345678"
        assert args.format == "mp3"

    def test_default_quality(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["https://youtu.be/abc12345678", "mp4"])
        assert args.quality == "best"

    def test_verbose_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["-v", "https://youtu.be/abc12345678", "mp3"])
        assert args.verbose is True

    def test_playlist_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["--playlist", "https://youtu.be/abc12345678", "mp3"]
        )
        assert args.playlist is True

    def test_custom_options(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "https://youtu.be/abc12345678",
            "mp4",
            "--quality", "720p",
            "--max-retries", "5",
            "--timeout", "600",
        ])
        assert args.quality == "720p"
        assert args.max_retries == 5
        assert args.timeout == 600
