import logging
import sys

from loguru import logger

from .settings import settings


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logger() -> None:
    log_level = settings.LOG_LEVEL
    log_dir = settings.LOG_DIR
    log_file = log_dir / settings.LOG_FILE_NAME

    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(sys.stderr, colorize=True, format=settings.LOG_FORMAT, level=log_level)

    if settings.LOG_TO_FILE:
        logger.add(
            log_file,
            level="ERROR",
            format=settings.LOG_FORMAT,
            rotation=settings.LOG_ROTATION,
            retention=settings.LOG_RETENTION,
            serialize=True,
        )

    intercept_handler = InterceptHandler()
    logging.root.handlers = [intercept_handler]
    logging.root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "celery",
        "httpx",
    ):
        stdlib_logger = logging.getLogger(logger_name)
        stdlib_logger.handlers = [intercept_handler]
        stdlib_logger.propagate = False

    logger.info("Logging setup successfully")
