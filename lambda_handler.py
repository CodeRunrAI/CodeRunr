"""AWS Lambda entry point for the FastAPI server."""

from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from loguru import logger
from mangum import Mangum

from db.seeds.languages import seed_languages_sync
from main import app

_alembic_config_path = Path(__file__).resolve().parent / "alembic.ini"
asgi_handler = Mangum(app)


def run_migrations_once() -> None:
    logger.info("Running database migrations before Lambda request handling")
    alembic_config = Config(str(_alembic_config_path))
    command.upgrade(alembic_config, "head")


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler"""
    event_type = event.get("event_type")

    if event_type == "Migration":
        run_migrations_once()
        return {"statusCode": 200, "body": "Migration run successfully"}

    if event_type == "Seed_Languages":
        seed_languages_sync()
        return {"statusCode": 200, "body": "Languages seed successfully"}

    return asgi_handler(event, context)
