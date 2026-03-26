"""Application configuration settings."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "Food Management API"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./food_management.db"
    
    # Security
    AUTH_PROVIDER: str = "local"  # local | cognito
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = False

    # AWS Cognito
    AWS_REGION: str = ""
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_APP_CLIENT_ID: str = ""
    COGNITO_APP_CLIENT_SECRET: str = ""
    COGNITO_AUTH_FLOW: str = "USER_PASSWORD_AUTH"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8501"
    ]
    
    # pick which env file to load; prefer ".env" but fall back to the template
    _env_file = ".env"
    if not os.path.exists(_env_file):
        _env_file = ".env.example"

    model_config = SettingsConfigDict(
        env_file=_env_file,
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins, handling both string and list formats."""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            try:
                return json.loads(self.BACKEND_CORS_ORIGINS)
            except json.JSONDecodeError:
                return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return self.BACKEND_CORS_ORIGINS

    @property
    def cognito_issuer(self) -> str:
        if not self.AWS_REGION or not self.COGNITO_USER_POOL_ID:
            return ""
        return (
            f"https://cognito-idp.{self.AWS_REGION}.amazonaws.com/"
            f"{self.COGNITO_USER_POOL_ID}"
        )

    @property
    def cognito_jwks_url(self) -> str:
        issuer = self.cognito_issuer
        if not issuer:
            return ""
        return f"{issuer}/.well-known/jwks.json"

    @property
    def is_cognito_enabled(self) -> bool:
        return self.AUTH_PROVIDER.strip().lower() == "cognito"


settings = Settings()