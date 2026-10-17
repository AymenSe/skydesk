from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres (Lab 3)
    database_url: str | None = None
    db_host: str = "localhost"
    db_user: str = "skydesk"
    db_name: str = "skydesk"
    db_password_file: Path | None = None

    # Classifier (Lab 4)
    artifacts_dir: Path = Path("artifacts")
    intent_threshold: float = 0.45

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.db_password_file:
            password = self.db_password_file.read_text().strip()
        else:
            password = "skydesk"
        return f"postgresql+psycopg://{self.db_user}:{password}@{self.db_host}:5432/{self.db_name}"


@lru_cache
def get_settings() -> Settings:
    return Settings()