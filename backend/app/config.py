import json
import os
from typing import List, Union
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    APP_NAME: str = "Invoice Processing System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

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
    MYSQL_SSL_MODE: str = ""
    MYSQL_SKIP_DB_CREATE: bool = False
    MYSQL_MIN_POOL_SIZE: int = 1
    MYSQL_MAX_POOL_SIZE: int = 10

    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AUTH_DISABLED: bool = True  # Demo mode supported

    # CORS & Formatting
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8501", "http://localhost:8503"]
    ALLOWED_HOSTS: Union[List[str], str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    ALLOWED_FORMATS: Union[List[str], str] = ["png", "jpg", "jpeg", "pdf", "tiff", "zip"]

    # File Upload
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "data/uploads"

    # Processing
    PROCESSING_TIMEOUT: int = 300
    BATCH_SIZE: int = 50

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # TrOCR / Handwriting
    ENABLE_TROCR_HANDWRITING: bool = False
    TROCR_MODEL_NAME: str = "microsoft/trocr-small-handwritten"
    TROCR_DEVICE: str = "cpu"
    TROCR_TRIGGER_CONFIDENCE: float = 0.55

    def get_cors_origins(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            try:
                parsed = json.loads(self.CORS_ORIGINS)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]
        return ["*"]

    def get_allowed_formats(self) -> List[str]:
        if isinstance(self.ALLOWED_FORMATS, list):
            return [f.lower().strip() for f in self.ALLOWED_FORMATS]
        if isinstance(self.ALLOWED_FORMATS, str):
            try:
                parsed = json.loads(self.ALLOWED_FORMATS)
                if isinstance(parsed, list):
                    return [f.lower().strip() for f in parsed]
            except Exception:
                pass
            return [x.lower().strip() for x in self.ALLOWED_FORMATS.split(",") if x.strip()]
        return ["png", "jpg", "jpeg", "pdf", "tiff", "zip"]


settings = Settings()
