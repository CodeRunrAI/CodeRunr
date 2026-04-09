import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from config import settings


x_api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ApiKeyAuth",
    description="Send the API token in the X-API-Key header.",
    auto_error=False,
)


async def require_api_key(x_api_key: str | None = Security(x_api_key_header)) -> str:
    """Validate the shared API token sent by the client."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: No API key provided",
        )

    expected_token = settings.AUTH_TOKEN.get_secret_value()
    if secrets.compare_digest(x_api_key, expected_token):
        return x_api_key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: invalid API key",
    )
