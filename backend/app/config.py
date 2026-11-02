from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    database_url: str = "sqlite:///./cinevibe.db"
    jwt_secret: str = "replace-this-secret-before-use"
    jwt_expire_minutes: int = 1440
    admin_email: str = "admin@cinevibe.local"
    admin_password: str = "ChangeMe@123"
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    max_upload_size: int = 2_147_483_648
    media_root: str = "./data/media"
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    @property
    def cors_list(self):
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

settings = Settings()
