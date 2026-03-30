from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings from .env file"""

    # Application
    APP_NAME: str = "invoiceflow"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development" # development, staging, production

    # Server
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    # Database (MySQL)
    MYSQL_URL: str = ""
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "invoices"
    MYSQL_MIN_POOL_SIZE: int = 1
    MYSQL_MAX_POOL_SIZE: int = 10

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AUTH_DISABLED: bool = False

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000"
    ]

    # Allowed hosts for security
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    # File upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024 # 10MB
    ALLOWED_FORMATS: List[str] = ["png", "jpg", "jpeg", "pdf"]
    UPLOAD_DIR: str = "data/uploads"

    # Processing
    PROCESSING_TIMEOUT: int = 300 # 5 minutes
    BATCH_SIZE: int = 50

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # OCR
    TESSERACT_CMD: str = ""
    TESSDATA_PREFIX: str = ""
    ENABLE_TROCR_HANDWRITING: bool = False
    TROCR_MODEL_NAME: str = "microsoft/trocr-small-handwritten"
    TROCR_DEVICE: str = "cpu"
    TROCR_TRIGGER_CONFIDENCE: float = 0.55
    TROCR_TRIGGER_SIGNAL: float = 8.0
    TROCR_MIN_TEXT_LENGTH: int = 350
    TROCR_SELECTION_MARGIN: float = 5.0
    TROCR_MAX_REGIONS: int = 24
    TROCR_MIN_LINE_HEIGHT: int = 18

    @field_validator("CORS_ORIGINS", "ALLOWED_HOSTS", "ALLOWED_FORMATS", mode="before")
    @classmethod
    def _split_csv(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("DEBUG", mode="before")
    @classmethod
    def _coerce_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"debug", "dev", "development"}:
                return True
        return value

    model_config = {
        "env_file": str(Path(__file__).resolve().parents[2] / ".env"),
        "case_sensitive": False
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() # type: ignore


settings = get_settings()
