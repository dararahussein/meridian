from __future__ import annotations
import httpx
import json
from typing import AsyncIterator, Sequence, Any
from meridian.core.types import CompletionResponse, Message, FinishReason, Role, TextBlock, TokenUsage
from meridian.providers.base import ModelProvider

class ProviderError(Exception): pass
class RateLimitError(ProviderError): pass
class ContextOverflowError(ProviderError): pass
class TransientProviderError(ProviderError): pass

class HTTPProvider(ModelProvider):
    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 30.0) -> None:
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=timeout,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )

    def _handle_error(self, response: httpx.Response) -> None:
        if response.status_code == 429: raise RateLimitError("Rate limit exceeded")
        if response.status_code == 413: raise ContextOverflowError("Context window exceeded")
        if response.status_code >= 500: raise TransientProviderError(f"Provider error: {response.status_code}")
        response.raise_for_status()

    async def complete(self, messages: Sequence[Message]) -> CompletionResponse:
        payload = {"model": self.model, "messages": [m.to_dict() for m in messages]}
        resp = await self.client.post("/chat/completions", json=payload)
        self._handle_error(resp)
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return CompletionResponse(
            model=self.model,
            message=Message(Role.ASSISTANT, content),
            finish_reason=FinishReason.STOP,
            usage=TokenUsage(prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0), completion_tokens=data.get("usage", {}).get("completion_tokens", 0))
        )

    async def stream(self, messages: Sequence[Message]) -> AsyncIterator[CompletionResponse]:
        payload = {"model": self.model, "messages": [m.to_dict() for m in messages], "stream": True}
        async with self.client.stream("POST", "/chat/completions", json=payload) as resp:
            self._handle_error(resp)
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    data = json.loads(line[6:])
                    delta = data["choices"][0].get("delta", {}).get("content", "")
                    if delta:
                        yield CompletionResponse(model=self.model, message=Message(Role.ASSISTANT, delta), finish_reason=FinishReason.STOP)
