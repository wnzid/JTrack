"""Environment-backed application configuration."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    ENVIRONMENT = os.getenv("JTRACK_ENV", "development").strip().lower()
    DEBUG = env_bool("FLASK_DEBUG", ENVIRONMENT == "development")
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5001"))

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", ENVIRONMENT == "production")
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(2 * 1024 * 1024)))

    USERS_DATABASE = os.getenv(
        "USERS_DATABASE", str(BASE_DIR / "instance" / "users.db")
    )
    ANALYTICS_DATABASE = os.getenv(
        "ANALYTICS_DATABASE", str(BASE_DIR / "dummy_data.db")
    )
    EXCEL_DATA_PATH = os.getenv("EXCEL_DATA_PATH", str(BASE_DIR / "dummy_data.xlsx"))
    DEFAULT_SQLITE_TABLE = os.getenv("DEFAULT_SQLITE_TABLE")

    USE_SHAREPOINT = env_bool("USE_SHAREPOINT")
    SP_CLIENT_ID = os.getenv("SP_CLIENT_ID")
    SP_CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
    SP_SITE_URL = os.getenv("SP_SITE_URL")
    SP_FILE_PATH = os.getenv("SP_FILE_PATH")

    ALLOW_REGISTRATION = env_bool("ALLOW_REGISTRATION", ENVIRONMENT != "production")
    ALLOW_ROLE_SELECTION = env_bool("ALLOW_ROLE_SELECTION", ENVIRONMENT != "production")
    DEFAULT_REGISTRATION_ROLE = os.getenv("DEFAULT_REGISTRATION_ROLE", "Leader")
    API_MAX_PAGE_SIZE = int(os.getenv("API_MAX_PAGE_SIZE", "500"))
