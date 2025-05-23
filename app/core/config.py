from typing import List, Union, Optional, Dict, Any
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"  # We'll use this internally
    API_V1_PREFIX: str = "/api/v1"  # Always starts with '/'; can be overridden by .env
    PROJECT_NAME: str = "AI Customer Assistant"
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DEBUG: bool = True

    # OpenAI
    OPENAI_API_KEY: str

    # Database
    DATABASE_URL: str
    SQLITE_URL: str = "sqlite:///kgen_gaming_support_advanced.db"
    USE_SQLITE: Optional[str] = None

    # Vector Store
    VECTOR_STORE_PATH: str = "/tmp/vector_store"
    KNOWLEDGE_BASE_PATH: str = "advanced_knowledge_base.txt"

    # Environment
    ENVIRONMENT: str = "development"

    @property
    def use_sqlite_db(self) -> bool:
        """Determine if we should use SQLite instead of the configured DATABASE_URL"""
        return self.ENVIRONMENT.lower() == "development" and (self.USE_SQLITE or "false").lower() == "true"

    @property
    def active_db_url(self) -> str:
        """Get the active database URL based on environment"""
        if self.use_sqlite_db:
            return self.SQLITE_URL
        return self.DATABASE_URL

    # Feedback storage
    FEEDBACK_DIR: str = os.environ.get("FEEDBACK_DIR", "/tmp/feedback")

    # Production URLs
    PRODUCTION_API_URL: str = "https://your-production-api.render.com"
    PRODUCTION_FRONTEND_URL: str = "https://your-production-frontend.streamlit.app"

    # JIRA
    JIRA_SERVER: str
    JIRA_EMAIL: str
    JIRA_API_TOKEN: str
    JIRA_PROJECT_KEY: str
    JIRA_URL: Optional[str] = None
    JIRA_USER_EMAIL: Optional[str] = None
    DB_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "game_data.db")

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra fields in .env file


settings = Settings()

# Create feedback directory
os.makedirs(settings.FEEDBACK_DIR, exist_ok=True) 