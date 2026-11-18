from typing import AsyncIterator, Protocol, Sequence
from meridian.core.types import CompletionResponse, Message

class ModelProvider(Protocol):
    async def complete(self, messages: Sequence[Message]) -> CompletionResponse:
        ...
    async def stream(self, messages: Sequence[Message]) -> AsyncIterator[CompletionResponse]:
        yield await self.complete(messages)
