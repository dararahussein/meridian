import pytest
from meridian.core.router import Router, CircuitState
from meridian.providers.mock import MockProvider
from meridian.core.types import Message, Role

@pytest.mark.asyncio
async def test_router_fallback() -> None:
    p1 = MockProvider(rate_limit_error=True)
    p2 = MockProvider()
    router = Router([p1, p2])
    resp = await router.complete([Message(Role.USER, "hi")])
    assert resp.message.text == "Mock response"

@pytest.mark.asyncio
async def test_circuit_breaker_opens() -> None:
    p1 = MockProvider(rate_limit_error=True)
    router = Router([p1])
    for _ in range(3):
        try: await router.complete([Message(Role.USER, "hi")])
        except: pass
    assert router.breakers[0].state == CircuitState.OPEN
