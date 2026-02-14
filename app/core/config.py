from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    log_level: str = "INFO"
    output_dir: Path = Path("downloads")
    max_retries: int = 3
    download_timeout: int = 300
    audio_bitrate: str = "320k"
    preferred_codec_video: str = "h264"
    preferred_codec_audio: str = "aac"


def get_settings() -> Settings:
    """Factory function to create a Settings instance.

    Returns:
        A Settings instance populated from environment variables.
    """
    return Settings()
