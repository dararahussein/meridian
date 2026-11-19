import asyncio
import random
import time
from enum import StrEnum, auto
from typing import Sequence
from meridian.core.types import CompletionResponse, Message
from meridian.providers.base import ModelProvider
from meridian.providers.http import RateLimitError, TransientProviderError

class CircuitState(StrEnum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time = 0.0

    def record_failure(self) -> None:
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def record_success(self) -> None:
        self.failures = 0
        self.state = CircuitState.CLOSED

    def can_attempt(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
        return self.state == CircuitState.HALF_OPEN

class Router:
    def __init__(self, providers: Sequence[ModelProvider], max_retries: int = 3) -> None:
        self.providers = list(providers)
        self.breakers = [CircuitBreaker() for _ in providers]
        self.max_retries = max_retries

    async def complete(self, messages: Sequence[Message]) -> CompletionResponse:
        for attempt in range(self.max_retries + 1):
            for i, provider in enumerate(self.providers):
                if not self.breakers[i].can_attempt():
                    continue
                try:
                    resp = await provider.complete(messages)
                    self.breakers[i].record_success()
                    return resp
                except (RateLimitError, TransientProviderError) as e:
                    self.breakers[i].record_failure()
                    if isinstance(e, RateLimitError):
                        await asyncio.sleep(min(2 ** attempt + random.uniform(0, 1), 30))
                    continue
                except Exception:
                    self.breakers[i].record_failure()
                    continue
        raise RuntimeError("All providers exhausted or failing")
