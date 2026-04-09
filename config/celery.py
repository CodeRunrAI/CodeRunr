from typing import Any
from pydantic import BaseModel, Field


class CeleryConfig(BaseModel):
    BROKER_URL: str = Field(description="Broker connection URL used by Celery workers.")
    BACKEND_URL: str = Field(
        description="Result backend connection URL used to store task states and results."
    )
    BROKER_CONNECTION_RETRY_ON_STARTUP: bool = Field(
        default=True,
        description="Retry broker connection during worker startup until the broker becomes available.",
    )
    BROKER_CONNECTION_MAX_RETRIES: int = Field(
        default=50,
        description="Maximum number of times Celery retries the initial broker connection before failing startup.",
    )
    BROKER_TRANSPORT_VISIBILITY_TIMEOUT_SECONDS: int = Field(
        default=30,
        description="How long a fetched message stays invisible to other workers before it can be redelivered.",
    )
    BROKER_TRANSPORT_MAX_RETRIES: int = Field(
        default=10,
        description="Maximum number of retry attempts performed by the broker transport for transient connection errors.",
    )
    BROKER_TRANSPORT_RETRY_TIMEOUT_SECONDS: float = Field(
        default=5.0,
        description="Socket timeout used by the broker client's retry policy.",
    )
    BROKER_TRANSPORT_POLLING_INTERVAL_SECONDS: float = Field(
        default=0.5,
        description="Delay between queue polling attempts when no messages are available.",
    )
    BROKER_TRANSPORT_CONFIRM_PUBLISH: bool = Field(
        default=True,
        description="Request broker-side publish confirmation when the selected transport supports it.",
    )
    TASK_SERIALIZER: str = Field(
        default="json",
        description="Serializer used for outbound task payloads.",
    )
    ACCEPT_CONTENT: list[str] = Field(
        default_factory=lambda: ["json"],
        description="List of accepted content types for inbound task payloads.",
    )
    RESULT_SERIALIZER: str = Field(
        default="json",
        description="Serializer used for task results stored in the backend.",
    )
    RESULT_EXPIRES: int = Field(
        default=60 * 60 * 24,
        description="How long task results remain in the backend before Celery considers them expired.",
    )
    TIMEZONE: str = Field(
        default="Asia/Kolkata",
        description="Application timezone used by Celery for scheduling and timestamps.",
    )
    ENABLE_UTC: bool = Field(
        default=True,
        description="Store and process Celery timestamps in UTC internally.",
    )

    @property
    def broker_transport_options(self) -> dict[str, Any]:
        return {
            "visibility_timeout": self.BROKER_TRANSPORT_VISIBILITY_TIMEOUT_SECONDS,
            "max_retries": self.BROKER_TRANSPORT_MAX_RETRIES,
            "retry_policy": {
                "timeout": self.BROKER_TRANSPORT_RETRY_TIMEOUT_SECONDS,
            },
            "polling_interval": self.BROKER_TRANSPORT_POLLING_INTERVAL_SECONDS,
            "confirm_publish": self.BROKER_TRANSPORT_CONFIRM_PUBLISH,
        }

    @property
    def celery_kwargs(self) -> dict[str, Any]:
        return {
            "backend": self.BACKEND_URL,
            "broker": self.BROKER_URL,
            "broker_connection_retry_on_startup": self.BROKER_CONNECTION_RETRY_ON_STARTUP,
            "broker_connection_max_retries": self.BROKER_CONNECTION_MAX_RETRIES,
            "broker_transport_options": self.broker_transport_options,
            "task_serializer": self.TASK_SERIALIZER,
            "accept_content": self.ACCEPT_CONTENT,
            "result_serializer": self.RESULT_SERIALIZER,
            "result_expires": self.RESULT_EXPIRES,
            "timezone": self.TIMEZONE,
            "enable_utc": self.ENABLE_UTC,
        }
