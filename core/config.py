from pydantic_settings import (
    BaseSettings, 
    SettingsConfigDict,
)
from core.config_path import BasePath
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f"{BasePath}/.env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # === База данных ===
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    # === JWT ===
    TOKEN_SECRET_KEY: str
    TOKEN_ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_MINUTES: int = 60 * 15  

    # === Форматы ===
    DATETIME_FORMAT: str = "%d-%m-%Y %H:%M:%S"

    # === URL ===
    @property
    def DATABASE_URL_asyncpg(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()