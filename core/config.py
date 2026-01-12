import os
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings:
    # معلومات النظام
    PROJECT_NAME = "Abu Jamal CyberShield"
    VERSION = "1.0.0"
    API_V1_STR = "/api/v1"
    
    # Replit Settings - SQLite محلي
    SQLALCHEMY_DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR}/storage/databases/cyber_shield.db"
    )
    
    # JWT Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Evidence Storage
    EVIDENCE_STORAGE_PATH = BASE_DIR / "storage" / "evidence"
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Replit Compatibility
    IS_REPLIT = os.getenv("REPL_ID") is not None
    PORT = int(os.getenv("PORT", 3000))

settings = Settings()
