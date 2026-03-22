import os
import tomllib
from pathlib import Path
from typing import Literal, TypeAlias

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


LogLevel: TypeAlias = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class SandboxConfig(BaseModel):
    MAX_STACK_LIMIT: int
    MAX_MEMORY_LIMIT: int
    MAX_CPU_TIME_LIMIT: float
    MAX_WALL_TIME_LIMIT: float
    MAX_MAX_FILE_SIZE: int
    MAX_MAX_PROCESSES_AND_OR_THREADS: int


def _load_sandbox_config() -> SandboxConfig:
    config_path = Path(__file__).with_name("coderunr.toml")
    with config_path.open("rb") as config_file:
        return SandboxConfig(**tomllib.load(config_file))


class Settings(BaseSettings):
    PROJECT_NAME: str = "CodeRunr"
    BASE_DIR: Path = Path(__file__).parent.parent
    API_V1_STR: str = "/api/v1"

    # Logging and monitoring
    LOG_LEVEL: LogLevel = (
        "DEBUG" if os.getenv("ENVIRONMENT", "?") == "development" else "INFO"
    )
    LOG_DIR: Path = BASE_DIR / "logs"
    LOG_FILE_NAME: str = "file.log"
    LOG_TO_FILE: bool = True
    LOG_ROTATION: str = "1 MB"
    LOG_RETENTION: str = "10 days"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    # This auth token will be used to authenticate every client request
    AUTH_TOKEN: SecretStr = SecretStr("change-me")
    # DATABASE
    POSTGRES_HOST: SecretStr
    POSTGRES_PORT: int
    POSTGRES_USER: SecretStr
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: SecretStr

    # QUEUE (Redis)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Outbound HTTP
    HTTP_TIMEOUT: float = 10.0
    HTTP_CONNECT_TIMEOUT: float = 5.0
    HTTP_MAX_CONNECTIONS: int = 100
    HTTP_MAX_KEEPALIVE_CONNECTIONS: int = 20
    HTTP_FOLLOW_REDIRECTS: bool = True
    HTTP_USER_AGENT: str = "CodeRunr/0.1.0"

    # Sandbox settings
    sandbox: SandboxConfig = Field(default_factory=_load_sandbox_config)
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
