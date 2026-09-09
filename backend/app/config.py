"""
Oasis — Smart Desert Orchard Management Platform.

Configuration settings loaded from environment / .env.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Oasis API"
    api_prefix: str = "/api/v1"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    database_url: str = "sqlite:///./oasis.db"
    upload_dir: str = "./uploads"
    storage_backend: str = "local"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
