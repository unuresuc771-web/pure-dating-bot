from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    BOT_TOKEN: str = Field(default="", description="Telegram Bot API Token")
    DATABASE_URL: str = Field(default=f"sqlite+aiosqlite:///{BASE_DIR}/bot_dating.db", description="Database connection URL")
    ADMIN_IDS: str = Field(default="", description="Comma-separated admin Telegram IDs")
    THROTTLE_RATE_LIMIT: float = Field(default=0.6, description="Minimum seconds between user actions")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def admin_list(self) -> List[int]:
        if not self.ADMIN_IDS:
            return []
        try:
            return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]
        except ValueError:
            return []

settings = Settings()
