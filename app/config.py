from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Trail Service API"
    DEBUG: bool = False

    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-fallback-secret-key-never-use-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DB_DRIVER: str = os.getenv("DB_DRIVER", "SQL Server")
    DB_SERVER: str = os.getenv("DB_SERVER", "localhost")
    DB_NAME: str = os.getenv("DB_NAME", "COMP2001")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_TRUSTED_CONNECTION: bool = os.getenv("DB_TRUSTED_CONNECTION", "true").lower() == "true"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "https://web.socem.plymouth.ac.uk"
    ]

    # Plymouth Auth Service
    PLYMOUTH_AUTH_URL: str = "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users"

    @property
    def DATABASE_URL(self) -> str:
        """Generate database connection string based on configuration"""
        if self.DB_TRUSTED_CONNECTION:
            return (
                f"Driver={{{self.DB_DRIVER}}};"
                f"Server={self.DB_SERVER};"
                f"Database={self.DB_NAME};"
                "Trusted_Connection=yes;"
            )
        else:
            return (
                f"Driver={{{self.DB_DRIVER}}};"
                f"Server={self.DB_SERVER};"
                f"Database={self.DB_NAME};"
                f"UID={self.DB_USER};"
                f"PWD={self.DB_PASSWORD};"
            )

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
