from typing import Any, Dict

from kombu import Queue
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.aws import aws_config
from db.session import _build_url


def _build_predefined_queues():
    queues: Dict = {aws_config.SQS_QUEUE_NAME: {"url": aws_config.SQS_QUEUE_URL}}
    return queues


class TransportOptions(BaseModel):
    MAX_RETRIES: int = 10
    """Maximum broker transport retry attempts for transient connection errors."""
    RETRY_TIMEOUT_SECONDS: float = 5.0
    """Socket timeout, in seconds, used by the broker client's retry policy."""
    VISIBILITY_TIMEOUT_SECONDS: int = 30
    """Seconds a fetched message stays hidden before another worker can receive it."""
    POLLING_INTERVAL_SECONDS: float = 0.5
    """Delay, in seconds, between queue polling attempts when no messages are available."""
    WALL_TIME_SECONDS: float = 15.0
    """SQS long polling wait time, in seconds, used to reduce empty and false-empty ReceiveMessage responses."""
    PREDEFINED_QUEUES: Dict = _build_predefined_queues()
    """Predefined queues"""
    AWS_REGION: str = aws_config.REGION or ""
    """AWS Region"""


class CeleryConfig(BaseSettings):
    BROKER_URL: str
    """Broker connection URL used by Celery workers."""
    BACKEND_URL: str
    """Result backend connection URL used to store task states and results."""
    BROKER_CONNECTION_RETRY_ON_STARTUP: bool = True
    """Retry broker connection during worker startup until the broker becomes available."""
    BROKER_CONNECTION_MAX_RETRIES: int = 50
    """Maximum number of initial broker connection retries before startup fails."""
    BROKER_TRANSPORT_OPTIONS: TransportOptions = TransportOptions()
    """Broker transport options"""
    TASK_DEFAULT_QUEUE: str = aws_config.SQS_QUEUE_NAME
    """Default Celery queue name, must be present in SQS predefined_queues."""
    TASK_PUBLISH_RETRY: bool = True
    """Retry task publishing when transient broker errors occur."""
    TASK_PUBLISH_RETRY_MAX_RETRIES: int = 3
    """Maximum retries attempted while publishing a task."""
    TASK_PUBLISH_RETRY_INTERVAL_START_SECONDS: float = 0.0
    """Initial delay between task publish retries."""
    TASK_PUBLISH_RETRY_INTERVAL_STEP_SECONDS: float = 0.5
    """Increment added between task publish retries."""
    TASK_PUBLISH_RETRY_INTERVAL_MAX_SECONDS: float = 2.0
    """Maximum delay between task publish retries."""
    TASK_SERIALIZER: str = "json"
    """Serializer used for outbound task payloads."""
    ACCEPT_CONTENT: list[str] = ["json"]
    """Content types accepted for inbound task payloads."""
    RESULT_SERIALIZER: str = "json"
    """Serializer used for task results stored in the backend."""
    RESULT_EXPIRES: int = 60 * 60 * 24
    """Seconds task results remain in the backend before Celery expires them."""
    TIMEZONE: str = "Asia/Kolkata"
    """Application timezone used by Celery for schedules and timestamps."""
    ENABLE_UTC: bool = True
    """Whether Celery stores and processes timestamps in UTC internally."""

    @property
    def broker_transport_options(self) -> dict[str, Any]:
        return {
            "visibility_timeout": self.BROKER_TRANSPORT_OPTIONS.VISIBILITY_TIMEOUT_SECONDS,
            "max_retries": self.BROKER_TRANSPORT_OPTIONS.MAX_RETRIES,
            "retry_policy": {
                "timeout": self.BROKER_TRANSPORT_OPTIONS.RETRY_TIMEOUT_SECONDS,
            },
            "polling_interval": self.BROKER_TRANSPORT_OPTIONS.POLLING_INTERVAL_SECONDS,
            "wait_time_seconds": self.BROKER_TRANSPORT_OPTIONS.WALL_TIME_SECONDS,
            "region": self.BROKER_TRANSPORT_OPTIONS.AWS_REGION,
            "predefined_queues": self.BROKER_TRANSPORT_OPTIONS.PREDEFINED_QUEUES,
        }

    @property
    def task_publish_retry_policy(self) -> dict[str, Any]:
        return {
            "max_retries": self.TASK_PUBLISH_RETRY_MAX_RETRIES,
            "interval_start": self.TASK_PUBLISH_RETRY_INTERVAL_START_SECONDS,
            "interval_step": self.TASK_PUBLISH_RETRY_INTERVAL_STEP_SECONDS,
            "interval_max": self.TASK_PUBLISH_RETRY_INTERVAL_MAX_SECONDS,
        }

    @property
    def celery_kwargs(self) -> dict[str, Any]:
        return {
            "backend": self.BACKEND_URL,
            "broker": self.BROKER_URL,
            "broker_connection_retry_on_startup": self.BROKER_CONNECTION_RETRY_ON_STARTUP,
            "broker_connection_max_retries": self.BROKER_CONNECTION_MAX_RETRIES,
            "broker_transport_options": self.broker_transport_options,
            "task_publish_retry": self.TASK_PUBLISH_RETRY,
            "task_publish_retry_policy": self.task_publish_retry_policy,
            "task_default_queue": self.TASK_DEFAULT_QUEUE,
            "task_queues": (Queue(self.TASK_DEFAULT_QUEUE),),
            "task_serializer": self.TASK_SERIALIZER,
            "accept_content": self.ACCEPT_CONTENT,
            "result_serializer": self.RESULT_SERIALIZER,
            "result_expires": self.RESULT_EXPIRES,
            "timezone": self.TIMEZONE,
            "enable_utc": self.ENABLE_UTC,
        }

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore", env_prefix="CELERY_"
    )


def _create_broker_url() -> str:
    return "sqs://"


def _create_backend_url() -> str:
    return _build_url("db+postgresql")


celery_config = CeleryConfig(
    BROKER_URL=_create_broker_url(), BACKEND_URL=_create_backend_url()
)
