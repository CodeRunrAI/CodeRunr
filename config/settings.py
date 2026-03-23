import os
from pathlib import Path
from typing import Literal, TypeAlias

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from config.sandbox import SandboxConfig


LOG_LEVEL_TYPES: TypeAlias = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_FORMAT_STR = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"


class Settings(BaseSettings):
    """All application level settings can be defined here"""

    PROJECT_NAME: str = "CodeRunr"
    BASE_DIR: Path = Path(__file__).parent.parent
    API_V1_STR: str = "/api/v1"

    # Logging and monitoring
    LOG_LEVEL: LOG_LEVEL_TYPES = (
        "DEBUG" if os.getenv("ENVIRONMENT", "?") == "development" else "INFO"
    )
    LOG_DIR: Path = BASE_DIR / "logs"
    LOG_FILE_NAME: str = "file.log"
    LOG_TO_FILE: bool = True
    LOG_ROTATION: str = "1 MB"
    LOG_RETENTION: str = "10 days"
    LOG_FORMAT: str = LOG_FORMAT_STR

    # This auth token will be used to authenticate every client request
    AUTH_TOKEN: SecretStr = SecretStr("change-me")

    # DATABASE
    POSTGRES_HOST: SecretStr
    POSTGRES_PORT: int
    POSTGRES_USER: SecretStr
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: SecretStr

    # QUEUE/Cache (Redis)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Outbound HTTP
    HTTP_TIMEOUT: float = 10.0
    HTTP_CONNECT_TIMEOUT: float = 5.0
    HTTP_MAX_CONNECTIONS: int = 100
    HTTP_MAX_KEEPALIVE_CONNECTIONS: int = 20
    HTTP_FOLLOW_REDIRECTS: bool = True
    HTTP_USER_AGENT: str = "CodeRunr/0.1.0"

    # Sandbox settings
    SANDBOX: SandboxConfig = SandboxConfig()
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
