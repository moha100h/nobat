from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    SECRET_KEY: str = "change_me"
    ENCRYPTION_KEY: str = "change_me_32_chars_fernet_key_her"
    DATABASE_URL: str = ""
    REDIS_URL: str = ""
    REDIS_PASSWORD: str = ""
    BACKEND_URL: str = "http://backend:8000"
    INTERNAL_API_KEY: str = "change_me"
    MASTER_BOT_TOKEN: str = ""
    MASTER_ADMIN_ID: int = 0
    UPLOAD_DIR: str = "/app/uploads"
    BACKUP_DIR: str = "/app/backups"
    BACKUP_CRON: str = "0 3 * * *"
    REMINDER_INTERVAL: int = 300

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache
def get_settings() -> Settings:
    return Settings()
