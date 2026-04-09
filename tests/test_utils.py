import pytest

from fastapi import HTTPException
from utils.security import require_api_key
from config import settings


class TestSecurityUtil:
    """Test the security utils"""

    @pytest.mark.asyncio
    async def test_require_api_key(self):
        key = await require_api_key(settings.AUTH_TOKEN.get_secret_value())
        assert key == settings.AUTH_TOKEN.get_secret_value()

    @pytest.mark.asyncio
    async def test_require_api_key_with_wrong_key(self):
        # This should raise HttpException
        with pytest.raises(HTTPException):
            await require_api_key("this is wrong key")

    @pytest.mark.asyncio
    async def test_require_api_key_with_none_key(self):
        # This should raise HttpException
        with pytest.raises(HTTPException):
            await require_api_key(None)
