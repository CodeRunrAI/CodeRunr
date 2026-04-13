from pathlib import Path
from typing import TYPE_CHECKING, List, Literal, TypeAlias

from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from config.aws import AWSConfig
    from config.celery import CeleryConfig
    from config.sandbox import SandboxConfig


LOG_LEVEL_TYPES: TypeAlias = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_FORMAT_STR = "{level} | {name}:{function}:{line} - {message}"


class CORSConfig(BaseSettings):
    """Cors config"""

    ALLOW_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])
    ALLOW_CREDENTIALS: bool = False
    ALLOWED_METHODS: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    )
    ALLOWED_HEADERS: List[str] = Field(default_factory=lambda: ["*"])
    MAX_AGE: int = 600

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore", env_prefix="CORS_"
    )


class Settings(BaseSettings):
    """All application level settings can be defined here"""

    PROJECT_NAME: str = "CodeRunr"
    BASE_DIR: Path = Path(__file__).parent.parent
    API_V1_STR: str = "/api/v1"

    # CORS
    CORS_CONFIG: CORSConfig = CORSConfig()

    # Logging and monitoring
    LOG_LEVEL: LOG_LEVEL_TYPES = "INFO"
    LOG_DIR: Path = BASE_DIR / "logs"
    LOG_FILE_NAME: str = "file.log"
    LOG_TO_FILE: bool = False
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

    # Outbound HTTP
    HTTP_TIMEOUT: float = 10.0
    HTTP_CONNECT_TIMEOUT: float = 5.0
    HTTP_MAX_CONNECTIONS: int = 100
    HTTP_MAX_KEEPALIVE_CONNECTIONS: int = 20
    HTTP_FOLLOW_REDIRECTS: bool = True
    HTTP_USER_AGENT: str = "CodeRunr/0.1.0"

    @property
    def SANDBOX_CONFIG(self) -> "SandboxConfig":
        from config.sandbox import sandbox_config

        return sandbox_config

    @property
    def AWS_CONFIG(self) -> "AWSConfig":
        from config.aws import aws_config

        return aws_config

    @property
    def CELERY_CONFIG(self) -> "CeleryConfig":
        from config.celery import celery_config

        return celery_config

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


settings = Settings()
