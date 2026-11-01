from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "steam.db"

class Settings(BaseSettings):
    app_name: str = "Steam Game Popularity Predictor API"
    debug: bool = False
    database_url: str = f"sqlite:///{DEFAULT_DB_PATH}"
    cors_origins: str = "*"
    pipeline_api_key: str = "secret-pipeline-key"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
