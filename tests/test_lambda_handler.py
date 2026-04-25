import pytest
from mangum import Mangum

import lambda_handler
from main import app


def test_lambda_asgi_handler_wraps_server_app():
    assert isinstance(lambda_handler.asgi_handler, Mangum)
    assert lambda_handler.asgi_handler.app is app
    assert lambda_handler.asgi_handler.lifespan == "auto"


def test_lambda_handler(
    monkeypatch: pytest.MonkeyPatch,
):
    calls = []

    def fake_upgrade(config, revision):
        calls.append(("upgrade", config.config_file_name, revision))

    def fake_asgi_handler(event, context):
        calls.append(("asgi", event, context))
        return {"statusCode": 200}

    monkeypatch.setattr(lambda_handler, "seed_languages_sync", lambda: None)
    monkeypatch.setattr(lambda_handler.command, "upgrade", fake_upgrade)
    monkeypatch.setattr(lambda_handler, "asgi_handler", fake_asgi_handler)

    db_migration_event = {"event_type": "Migration"}
    seed_languages_event = {"event_type": "Seed_Languages"}
    first_event = {"request": 1}
    second_event = {"request": 2}
    context = object()

    assert lambda_handler.handler(db_migration_event, context) == {
        "statusCode": 200,
        "body": "Migration run successfully",
    }
    assert lambda_handler.handler(seed_languages_event, context) == {
        "statusCode": 200,
        "body": "Languages seed successfully",
    }
    assert lambda_handler.handler(first_event, context) == {"statusCode": 200}
    assert lambda_handler.handler(second_event, context) == {"statusCode": 200}

    assert calls == [
        ("upgrade", str(lambda_handler._alembic_config_path), "head"),
        ("asgi", first_event, context),
        ("asgi", second_event, context),
    ]
