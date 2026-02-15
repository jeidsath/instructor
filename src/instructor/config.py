from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/instructor"
    )

    # Anthropic
    anthropic_api_key: str = ""

    # Application
    app_env: str = "development"
    log_level: str = "info"

    # Curriculum
    curriculum_path: Path = Path("curriculum")

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


settings = Settings()
