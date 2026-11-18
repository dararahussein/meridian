import asyncio
from typing import AsyncIterator, Sequence
from meridian.core.types import CompletionResponse, FinishReason, Message, Role, TextBlock, TokenUsage
from meridian.providers.base import ModelProvider

class MockProvider(ModelProvider):
    def __init__(self, latency_ms: float = 0.0, rate_limit_error: bool = False, scripted_responses: Sequence[CompletionResponse] | None = None) -> None:
        self.latency_ms = latency_ms
        self.rate_limit_error = rate_limit_error
        self.scripted_responses = list(scripted_responses or [])
        self._call_count = 0

    async def complete(self, messages: Sequence[Message]) -> CompletionResponse:
        if self.latency_ms > 0:
            await asyncio.sleep(self.latency_ms / 1000.0)
        if self.rate_limit_error:
            raise Exception("Rate limit exceeded")
        
        if self.scripted_responses:
            response = self.scripted_responses[min(self._call_count, len(self.scripted_responses) - 1)]
            self._call_count += 1
            return response

        return CompletionResponse(
            model="mock-model",
            message=Message(Role.ASSISTANT, "Mock response"),
            finish_reason=FinishReason.STOP,
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5)
        )
