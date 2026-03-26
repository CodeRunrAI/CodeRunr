import asyncio

from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException

from config import settings
from utils import http_util
from main import app, handle_exception, handle_http_exception


class TestMainApp:
    """Test the main fastapi app"""

    def test_has_title(self, client: TestClient):
        """Title is required"""
        assert client.app.title == settings.PROJECT_NAME

    def test_has_version(self, client: TestClient):
        """Version is required"""
        assert client.app.version == "0.1.0"

    def test_has_description(self, client: TestClient):
        """Description is required"""
        assert client.app.description == "CodeRunr: Sandbox code execution"

    def test_has_openapi_url(self, client: TestClient):
        """Openapi url is required"""
        assert client.app.openapi_url == f"{settings.API_V1_STR}/openapi.json"

    def test_has_docs_url(self, client: TestClient):
        """Docs url is required"""
        assert client.app.docs_url == "/docs"

    def test_lifespan_initializes_and_closes_http_clients(self):
        """Lifespan should initialize and close shared HTTP clients"""
        asyncio.run(http_util.close_http_clients())

        assert http_util._async_http_client is None
        assert http_util._sync_http_client is None

        with TestClient(app):
            assert http_util._async_http_client is not None
            assert http_util._sync_http_client is not None

        assert http_util._async_http_client is None
        assert http_util._sync_http_client is None

    def test_has_global_exception_handler(self, client: TestClient):
        """Check exception handlers"""
        exception_handlers = client.app.exception_handlers

        assert exception_handlers[HTTPException] is handle_http_exception
        assert exception_handlers[Exception] is handle_exception

    def test_has_cors_middleware(self, client: TestClient):
        """Check CORS middleware"""
        cors_middleware = None

        for user_middleware in client.app.user_middleware:
            if user_middleware.cls == CORSMiddleware:
                cors_middleware = user_middleware

        assert cors_middleware is not None
        assert cors_middleware.kwargs == {
            "allow_origins": ["*"],
            "allow_credentials": False,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }

    def test_has_api_routes(self, client: TestClient):
        """App should have api endpoints"""
        routes = {route.path for route in client.app.routes}

        assert "/api/v1/health" in routes
        assert "/api/v1/languages" in routes
        assert "/api/v1/submissions" in routes
