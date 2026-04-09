"""
Code Execution Sandbox — FastAPI application.
"""

from contextlib import asynccontextmanager
from typing import Any

from loguru import logger
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from schema import APIResponse
from routes import api_router
from config import settings, configure_logger
from utils.http_util import close_http_clients, init_http_clients


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configure the logger before the FastAPI application starts"""
    configure_logger()
    """Initialize the http client"""
    init_http_clients()
    yield
    """Close http client and active http connections"""
    await close_http_clients()


app = FastAPI(
    debug=True if settings.LOG_LEVEL == "DEBUG" else False,
    version="0.1.0",
    title=settings.PROJECT_NAME,
    description="CodeRunr: Sandbox code execution",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)


def get_cors_middleware_options() -> dict[str, Any]:
    allow_origins = settings.CORS_CONFIG.ALLOW_ORIGINS
    allow_credentials = settings.CORS_CONFIG.ALLOW_CREDENTIALS

    if "*" in allow_origins and allow_credentials:
        raise ValueError(
            "CORS misconfiguration: wildcard origins cannot be used with credentials enabled."
        )

    return {
        "allow_origins": allow_origins,
        "allow_credentials": allow_credentials,
        "allow_methods": settings.CORS_CONFIG.ALLOWED_METHODS,
        "allow_headers": settings.CORS_CONFIG.ALLOWED_HEADERS,
        "max_age": settings.CORS_CONFIG.MAX_AGE,
    }


@app.exception_handler(IntegrityError)
async def database_integrity_error_handler(request: Request, exc: IntegrityError):
    logger.error(exc)
    api_response = APIResponse[None](status="Error", message="Database integrity error")
    return JSONResponse(status_code=409, content=api_response.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [{"field": err["loc"][-1], "message": err["msg"]} for err in exc.errors()]
    api_response = APIResponse[Any](
        status="Error", message="Validation Error", data=errors
    )
    return JSONResponse(status_code=422, content=api_response.model_dump())


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    errors = [{"field": err["loc"][-1], "message": err["msg"]} for err in exc.errors()]
    api_response = APIResponse[Any](
        status="Error", message="Validation Error", data=errors
    )
    return JSONResponse(status_code=422, content=api_response.model_dump())


@app.exception_handler(HTTPException)
def handle_http_exception(request: Request, exc: HTTPException):
    """When HTTPException occur, catch it here and send the APIResponse"""
    api_response = APIResponse[None](status="Error", message=exc.detail)
    return JSONResponse(status_code=exc.status_code, content=api_response.model_dump())


@app.exception_handler(Exception)
def handle_exception(request: Request, exc: Exception):
    """When Exception occur, catch it here, log this exception and send the APIResponse"""
    logger.exception(exc)
    api_response = APIResponse[None](status="Error", message="Internal server error")
    return JSONResponse(status_code=500, content=api_response.model_dump())


"""CORS middleware"""
app.add_middleware(
    CORSMiddleware,
    **get_cors_middleware_options(),
)

"""Include the main api_router, this router will expose all the API endpoints"""
app.include_router(api_router)
