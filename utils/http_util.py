"""
HTTP utility based on Httpx for making Http request on other services.
"""

from httpx import AsyncClient, Client, Limits, Timeout
from config import settings

_async_http_client: AsyncClient | None = None
_sync_http_client: Client | None = None


def _build_timeout() -> Timeout:
    return Timeout(
        timeout=settings.HTTP_TIMEOUT,
        connect=settings.HTTP_CONNECT_TIMEOUT,
    )


def _build_limits() -> Limits:
    return Limits(
        max_connections=settings.HTTP_MAX_CONNECTIONS,
        max_keepalive_connections=settings.HTTP_MAX_KEEPALIVE_CONNECTIONS,
    )


def _build_headers() -> dict[str, str]:
    return {"User-Agent": settings.HTTP_USER_AGENT}


def init_http_clients() -> None:
    global _async_http_client, _sync_http_client

    if _async_http_client is not None and _sync_http_client is not None:
        return

    timeout = _build_timeout()
    limits = _build_limits()
    headers = _build_headers()

    _async_http_client = AsyncClient(
        timeout=timeout,
        limits=limits,
        follow_redirects=settings.HTTP_FOLLOW_REDIRECTS,
        headers=headers,
    )
    _sync_http_client = Client(
        timeout=timeout,
        limits=limits,
        follow_redirects=settings.HTTP_FOLLOW_REDIRECTS,
        headers=headers,
    )


async def close_http_clients() -> None:
    global _async_http_client, _sync_http_client

    if _async_http_client is not None:
        await _async_http_client.aclose()
        _async_http_client = None

    if _sync_http_client is not None:
        _sync_http_client.close()
        _sync_http_client = None


async def get_async_http() -> AsyncClient:
    if _async_http_client is None:
        raise RuntimeError("Async HTTP client has not been initialized")
    return _async_http_client


def get_sync_http() -> Client:
    if _sync_http_client is None:
        init_http_clients()
    if _sync_http_client is None:
        raise RuntimeError("Sync HTTP client has not been initialized")
    return _sync_http_client
