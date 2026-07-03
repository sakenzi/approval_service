from pydantic_settings import BaseSettings, SettingsConfigDict

from core.config_path import BasePath


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f"{BasePath}/.env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    LOG_LEVEL: str = "INFO"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_NAME: str = "approval_service"
    DATABASE_URL: str | None = None

    TOKEN_SECRET_KEY: str = "local-secret"
    TOKEN_ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_MINUTES: int = 60 * 15
    DATETIME_FORMAT: str = "%d-%m-%Y %H:%M:%S"

    @property
    def DATABASE_URL_asyncpg(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"sqlite+aiosqlite:///./approval_service.db"


settings = Settings()