import pytest
import asyncio
from meridian.core.types import CompletionResponse, FinishReason, Message, Role, TokenUsage
from meridian.providers.mock import MockProvider

@pytest.mark.asyncio
async def test_mock_provider_latency() -> None:
    provider = MockProvider(latency_ms=50)
    start = asyncio.get_event_loop().time()
    await provider.complete([Message(Role.USER, "hi")])
    end = asyncio.get_event_loop().time()
    assert (end - start) >= 0.04

@pytest.mark.asyncio
async def test_mock_provider_rate_limit() -> None:
    provider = MockProvider(rate_limit_error=True)
    with pytest.raises(Exception, match="Rate limit exceeded"):
        await provider.complete([Message(Role.USER, "hi")])

@pytest.mark.asyncio
async def test_mock_provider_scripted() -> None:
    resp = CompletionResponse(
        model="test",
        message=Message(Role.ASSISTANT, "Scripted"),
        finish_reason=FinishReason.STOP
    )
    provider = MockProvider(scripted_responses=[resp])
    result = await provider.complete([Message(Role.USER, "hi")])
    assert result.message.text == "Scripted"
