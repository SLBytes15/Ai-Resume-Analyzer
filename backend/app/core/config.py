import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "TalentLens"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = "talentlens-mvp-super-secret-key-at-least-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database URLs
    DATABASE_URL: str = "postgresql+asyncpg://saranshop@/talentlens_mvp?host=/tmp"
    TEST_DATABASE_URL: str = "postgresql+asyncpg://saranshop@/talentlens_test?host=/tmp"

    # CORS origins
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                return [v]
        return v


settings = Settings()
