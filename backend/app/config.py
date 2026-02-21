from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "rag-masterclass"

    # Encryption
    settings_encryption_key: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        protected_namespaces = ("model_",)


@lru_cache
def get_settings() -> Settings:
    return Settings()
