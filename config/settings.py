import os
from pathlib import Path
from typing import Literal, TypeAlias, Any

from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from config.celery import CeleryConfig
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
    AUTH_TOKEN: SecretStr = Field(..., description="X-API-KEY auth token")

    # Database settings
    POSTGRES_HOST: SecretStr = Field(..., description="Database host")
    POSTGRES_PORT: int = Field(..., description="Database port")
    POSTGRES_USER: SecretStr = Field(..., description="Database user")
    POSTGRES_PASSWORD: SecretStr = Field(..., description="Database password")
    POSTGRES_DB: SecretStr = Field(..., description="Database name")

    # QUEUE/Cache (Redis)
    REDIS_URL: SecretStr = Field(..., description="Redis in-memory db URL")

    # Outbound HTTP
    HTTP_TIMEOUT: float = 10.0
    HTTP_CONNECT_TIMEOUT: float = 5.0
    HTTP_MAX_CONNECTIONS: int = 100
    HTTP_MAX_KEEPALIVE_CONNECTIONS: int = 20
    HTTP_FOLLOW_REDIRECTS: bool = True
    HTTP_USER_AGENT: str = "CodeRunr/0.1.0"

    # Sandbox config
    SANDBOX_CONFIG: SandboxConfig = SandboxConfig()
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )

    # Celery config
    CELERY_CONFIG: CeleryConfig | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.CELERY_CONFIG is None:
            redis_url = self.REDIS_URL.get_secret_value()
            self.CELERY_CONFIG = CeleryConfig(
                BROKER_URL=redis_url,
                BACKEND_URL=redis_url,
            )


settings = Settings()
