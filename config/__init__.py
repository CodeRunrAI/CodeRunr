from config.settings import settings


__all__ = [
    "settings",
    "celery_config",
    "sandbox_config",
    "aws_config",
    "configure_logger",
]


def __getattr__(name: str):
    if name == "aws_config":
        from config.aws import aws_config

        return aws_config

    if name == "celery_config":
        from config.celery import celery_config

        return celery_config

    if name == "configure_logger":
        from config.logging import configure_logger

        return configure_logger

    if name == "sandbox_config":
        from config.sandbox import sandbox_config

        return sandbox_config

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
