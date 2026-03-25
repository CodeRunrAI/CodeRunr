from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException


class TestMainApp:
    """Test the main fastapi app"""

    def test_has_title(self, client: TestClient):
        """Title is required"""
        assert hasattr(client.app, "title")

    def test_has_version(self, client: TestClient):
        """Version is required"""
        assert hasattr(client.app, "version")

    def test_has_description(self, client: TestClient):
        """Description is required"""
        assert hasattr(client.app, "description")

    def test_has_openapi_url(self, client: TestClient):
        """Openapi url is required"""
        assert hasattr(client.app, "openapi_url")

    def test_has_docs_url(self, client: TestClient):
        """Docs url is required"""
        assert hasattr(client.app, "docs_url")

    def test_has_lifespan(self, client: TestClient):
        """Lifespan is required"""
        assert hasattr(client, "lifespan")

    def test_has_global_exception_handler(self, client: TestClient):
        """Check exception handlers"""
        assert hasattr(client.app, "exception_handlers")

        exception_handlers = getattr(client.app, "exception_handlers")
        # Check both exception
        assert HTTPException in exception_handlers
        assert Exception in exception_handlers

    def test_has_cors_middleware(self, client: TestClient):
        """Check CORS middleware"""
        assert hasattr(client.app, "user_middleware")

        user_middlewares = getattr(client.app, "user_middleware")
        cors_middleware = None

        for user_middleware in user_middlewares:
            if user_middleware.cls == CORSMiddleware:
                cors_middleware = user_middleware

        assert cors_middleware is not None

    def test_has_api_routes(self, client: TestClient):
        """App should has api endpoints"""
        routes = getattr(client.app, "routes")
        assert len(routes) > 0
