from typing import List, Union, Optional, Dict, Any
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "KGen AI Support"
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

    # Vector Store
    VECTOR_STORE_PATH: str = "vector_store"
    KNOWLEDGE_BASE_PATH: str = "knowledge_base.txt"

    # Environment
    ENVIRONMENT: str = "development"

    # Feedback storage
    FEEDBACK_DIR: str = "feedback"

    # Production URLs
    PRODUCTION_API_URL: str = "https://your-production-api.render.com"
    PRODUCTION_FRONTEND_URL: str = "https://your-production-frontend.streamlit.app"

    # JIRA
    JIRA_SERVER: str
    JIRA_EMAIL: str
    JIRA_API_TOKEN: Optional[str] = os.getenv("JIRA_API_TOKEN", None)
    JIRA_PROJECT_KEY: str
    JIRA_URL: Optional[str] = os.getenv("JIRA_URL", None)
    JIRA_USER_EMAIL: Optional[str] = os.getenv("JIRA_USER_EMAIL", None)
    DB_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "game_data.db")

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Create feedback directory
os.makedirs(settings.FEEDBACK_DIR, exist_ok=True) 