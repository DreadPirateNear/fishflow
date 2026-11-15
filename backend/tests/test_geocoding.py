import pytest
import asyncio
import time
from app.services.geocoding import BoundedLRUCache, _get_nominatim_semaphore


@pytest.mark.asyncio
async def test_bounded_lru_cache_basic_and_eviction():
    cache = BoundedLRUCache(max_size=3, ttl_seconds=60.0)
    await cache.set("a", 1)
    await cache.set("b", 2)
    await cache.set("c", 3)

    assert await cache.get("a") == 1
    assert await cache.get("b") == 2
    assert await cache.get("c") == 3

    # Add 4th item; 'a' was accessed most recently before 'b' and 'c'
    # Wait, access order: set a, set b, set c.
    # get a -> order: b, c, a
    # get b -> order: c, a, b
    # get c -> order: a, b, c
    # Now set d: oldest is 'a', so 'a' should be evicted
    await cache.set("d", 4)

    assert await cache.get("a") is None
    assert await cache.get("b") == 2
    assert await cache.get("c") == 3
    assert await cache.get("d") == 4


@pytest.mark.asyncio
async def test_bounded_lru_cache_ttl_expiration():
    cache = BoundedLRUCache(max_size=5, ttl_seconds=0.05)
    await cache.set("key", "val")
    assert await cache.get("key") == "val"

    await asyncio.sleep(0.06)
    assert await cache.get("key") is None


@pytest.mark.asyncio
async def test_nominatim_semaphore_concurrency():
    sem = _get_nominatim_semaphore()
    assert isinstance(sem, asyncio.Semaphore)
    async with sem:
        # Verify semaphore can be acquired without blocking
        assert sem.locked()
