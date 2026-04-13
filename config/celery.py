from typing import Any, Dict

from kombu import Queue
from kombu.utils.url import safequote
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.aws import aws_config
from db.session import _build_url


def _build_predefined_queues() -> Dict[str, str]:
    data = {aws_config.SQS_QUEUE_NAME: {"url": aws_config.SQS_QUEUE_URL}}

    if hasattr(aws_config, "access_key_id") and hasattr(
        aws_config, "secret_access_key"
    ):
        data[aws_config.SQS_QUEUE_NAME]["access_key_id"] = (
            aws_config.ACCESS_KEY_ID.get_secret_value()
        )
        data[aws_config.SQS_QUEUE_NAME]["secret_access_key"] = (
            aws_config.SECRET_ACCESS_KEY.get_secret_value()
        )

    return data


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
    AWS_REGION: str = aws_config.REGION
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
    def celery_kwargs(self) -> dict[str, Any]:
        return {
            "backend": self.BACKEND_URL,
            "broker": self.BROKER_URL,
            "broker_connection_retry_on_startup": self.BROKER_CONNECTION_RETRY_ON_STARTUP,
            "broker_connection_max_retries": self.BROKER_CONNECTION_MAX_RETRIES,
            "broker_transport_options": self.broker_transport_options,
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
    AWS_ACCESS_KEY_ID = aws_config.ACCESS_KEY_ID.get_secret_value()
    AWS_SECRET_ACCESS_KEY = aws_config.SECRET_ACCESS_KEY.get_secret_value()

    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        # URL-encode ONLY for broker URL
        aws_access_key_encoded = safequote(AWS_ACCESS_KEY_ID)
        aws_secret_key_encoded = safequote(AWS_SECRET_ACCESS_KEY)

        # Use encoded credentials in broker URL
        return f"sqs://{aws_access_key_encoded}:{aws_secret_key_encoded}@"

    return "sqs://"


def _create_backend_url() -> str:
    return _build_url("db+postgresql")


celery_config = CeleryConfig(
    BROKER_URL=_create_broker_url(), BACKEND_URL=_create_backend_url()
)
