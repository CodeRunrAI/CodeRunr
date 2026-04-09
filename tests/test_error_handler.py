import pytest
from exceptions.error_handler import sync_error_handler, async_error_handler


class TestErrorHandler:
    def test_sync_error_handler_success(self):
        @sync_error_handler(name="test_sync_error_handler", max_retries=2)
        def mock_func():
            return "Success"

        assert mock_func() == "Success"

    def test_sync_error_handler_fail(self):
        @sync_error_handler(name="test_sync_error_handler", max_retries=2)
        def mock_func():
            raise Exception()

        with pytest.raises(Exception):
            mock_func()

    @pytest.mark.asyncio
    async def test_async_error_handler_success(self):
        @async_error_handler(name="test_async_error_handler", max_retries=2)
        async def mock_func():
            return "Success"

        await mock_func() == "Success"

    @pytest.mark.asyncio
    async def test_async_error_handler_fail(self):
        @async_error_handler(name="test_async_error_handler", max_retries=2)
        async def mock_func():
            raise Exception()

        with pytest.raises(Exception):
            await mock_func()
