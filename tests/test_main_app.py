import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

import main as main_module
from config import settings
from config.settings import CORSConfig
from utils import http_util
from main import (
    database_integrity_error_handler,
    get_cors_middleware_options,
    handle_exception,
    handle_http_exception,
    validation_exception_handler,
    pydantic_validation_handler,
)


class TestMainApp:
    """Test the main fastapi app"""

    @staticmethod
    def _expected_allow_origin(origin: str) -> str:
        if "*" in settings.CORS_CONFIG.ALLOW_ORIGINS:
            return "*"

        return origin

    @staticmethod
    def _cors_test_origin() -> str:
        if "*" in settings.CORS_CONFIG.ALLOW_ORIGINS:
            return "https://frontend.example.test"

        return settings.CORS_CONFIG.ALLOW_ORIGINS[0]

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

        with TestClient(main_module.app):
            assert http_util._async_http_client is not None
            assert http_util._sync_http_client is not None

        assert http_util._async_http_client is None
        assert http_util._sync_http_client is None

    def test_has_global_exception_handler(self, client: TestClient):
        """Check exception handlers"""
        exception_handlers = client.app.exception_handlers

        assert exception_handlers[IntegrityError] is database_integrity_error_handler
        assert (
            exception_handlers[RequestValidationError] is validation_exception_handler
        )
        assert exception_handlers[ValidationError] is pydantic_validation_handler
        assert exception_handlers[HTTPException] is handle_http_exception
        assert exception_handlers[Exception] is handle_exception

    def test_database_integrity_error_handler_returns_sanitized_conflict(self):
        """Integrity errors should return a sanitized conflict response."""
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/",
                "headers": [],
            }
        )
        exc = IntegrityError(
            statement="INSERT INTO languages ...",
            params={"name": "python"},
            orig=Exception("duplicate key value violates unique constraint"),
        )

        response = asyncio.run(database_integrity_error_handler(request, exc))

        assert response.status_code == 409
        assert json.loads(response.body) == {
            "status": "Error",
            "message": "Database integrity error",
            "data": None,
        }

    def test_has_cors_middleware(self, client: TestClient):
        """Check CORS middleware"""
        cors_middleware = None

        for user_middleware in client.app.user_middleware:
            if user_middleware.cls == CORSMiddleware:
                cors_middleware = user_middleware

        assert cors_middleware is not None
        assert cors_middleware.kwargs == {
            "allow_origins": settings.CORS_CONFIG.ALLOW_ORIGINS,
            "allow_credentials": settings.CORS_CONFIG.ALLOW_CREDENTIALS,
            "allow_methods": settings.CORS_CONFIG.ALLOWED_METHODS,
            "allow_headers": settings.CORS_CONFIG.ALLOWED_HEADERS,
            "max_age": settings.CORS_CONFIG.MAX_AGE,
        }

    def test_get_cors_middleware_options_rejects_wildcard_credentials(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """Wildcard origins cannot be combined with credentials."""
        monkeypatch.setattr(
            main_module.settings,
            "CORS_CONFIG",
            CORSConfig(ALLOW_ORIGINS=["*"], ALLOW_CREDENTIALS=True),
        )

        with pytest.raises(ValueError, match="wildcard origins"):
            get_cors_middleware_options()

    def test_cors_simple_request_returns_expected_origin_header(
        self, client: TestClient
    ):
        """Simple CORS requests should expose the configured origin policy."""
        origin = self._cors_test_origin()
        response = client.get("/api/v1/health", headers={"Origin": origin})

        assert response.status_code == 200
        assert response.headers[
            "access-control-allow-origin"
        ] == self._expected_allow_origin(origin)

        if "*" not in settings.CORS_CONFIG.ALLOW_ORIGINS:
            assert response.headers["vary"] == "Origin"

    def test_cors_preflight_request_returns_configured_headers(
        self, client: TestClient
    ):
        """Preflight requests should return the configured CORS metadata."""
        origin = self._cors_test_origin()
        requested_method = (
            "GET"
            if "*" in settings.CORS_CONFIG.ALLOWED_METHODS
            else settings.CORS_CONFIG.ALLOWED_METHODS[0]
        )
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": requested_method,
            },
        )

        assert response.status_code == 200
        assert response.headers[
            "access-control-allow-origin"
        ] == self._expected_allow_origin(origin)
        assert response.headers["access-control-max-age"] == str(
            settings.CORS_CONFIG.MAX_AGE
        )

        allowed_methods = response.headers["access-control-allow-methods"]
        assert requested_method in allowed_methods

    def test_cors_preflight_request_allows_configured_headers(self, client: TestClient):
        """Preflight requests should allow the configured request headers."""
        origin = self._cors_test_origin()
        requested_method = (
            "GET"
            if "*" in settings.CORS_CONFIG.ALLOWED_METHODS
            else settings.CORS_CONFIG.ALLOWED_METHODS[0]
        )
        requested_header = (
            "X-Test-Header"
            if "*" in settings.CORS_CONFIG.ALLOWED_HEADERS
            else settings.CORS_CONFIG.ALLOWED_HEADERS[0]
        )
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": requested_method,
                "Access-Control-Request-Headers": requested_header,
            },
        )

        assert response.status_code == 200

        allowed_headers = response.headers["access-control-allow-headers"].lower()
        assert requested_header.lower() in allowed_headers

    def test_cors_preflight_rejects_unconfigured_headers(self, client: TestClient):
        """Preflight should reject request headers that are not configured."""
        if "*" in settings.CORS_CONFIG.ALLOWED_HEADERS:
            pytest.skip("Wildcard header policy allows arbitrary preflight headers.")

        origin = self._cors_test_origin()
        requested_method = (
            "GET"
            if "*" in settings.CORS_CONFIG.ALLOWED_METHODS
            else settings.CORS_CONFIG.ALLOWED_METHODS[0]
        )
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": requested_method,
                "Access-Control-Request-Headers": "BEARER-TOKEN",
            },
        )

        assert response.status_code == 400
        assert response.text == "Disallowed CORS headers"
