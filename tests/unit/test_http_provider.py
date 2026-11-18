import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from meridian.providers.http import HTTPProvider, RateLimitError
from meridian.core.types import Message, Role

@pytest.mark.asyncio
async def test_http_provider_error_handling() -> None:
    provider = HTTPProvider("http://test", "key", "model")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 429
    provider.client.post = AsyncMock(return_value=mock_resp)
    with pytest.raises(RateLimitError):
        await provider.complete([Message(Role.USER, "hi")])
