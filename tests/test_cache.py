import os

import pytest

from cache_money import cache_money, close_cache_money, init_cache_money
from cache_money.constants import CACHE_MINUTE

executions: int = 0


init_cache_money(host="localhost", prefix="cache_money_test", port=os.getenv("REDIS_6379_TCP_PORT", 63798))


@cache_money.cached(timeout=CACHE_MINUTE)
async def addition(x: int, y: int) -> int:
    global executions

    executions += 1
    return x + y


@cache_money.cached(timeout=CACHE_MINUTE)
async def multiplication(x: int, y: int) -> int:
    global executions

    executions += 1
    return x * y


@pytest.mark.asyncio
async def test_cache():
    global executions

    # Wipe out all keys
    if keys := await cache_money.conn.keys("*"):
        await cache_money.conn.delete(*keys)

    # Normal test, execute function without cache, then re-execute the function but this time it should be cached
    await addition(3, 4)
    assert executions == 1

    await addition(3, 4)
    assert executions == 1

    await addition(3, 7)
    assert executions == 2

    # Bust cache for one entry, then execute twice, shows that the function will have been executed only once
    # Shows that busting the cache for a specific entry won't bust the cache of other entries
    await addition.bust(3, 4)
    executions = 0

    await addition(3, 4)
    assert executions == 1

    await addition(3, 4)
    assert executions == 1

    await addition(3, 7)
    assert executions == 1

    # Bust cache for all cache entries of the function addition, shows that busting the cache for all entries
    # related to a function don't bust the cache of other functions (multiplication)
    executions = 0

    await multiplication(2, 4)
    assert executions == 1

    await addition.bust_all()

    await addition(3, 4)
    assert executions == 2

    await addition(3, 7)
    assert executions == 3

    await multiplication(2, 4)
    assert executions == 3

    # Bust all cache entries, shows that it removes cache for all entries of both addition and multiplications
    executions = 0

    await addition(3, 4)
    assert executions == 0

    await addition(3, 7)
    assert executions == 0

    await multiplication(2, 4)
    assert executions == 0

    await cache_money.bust()

    await addition(3, 4)
    assert executions == 1

    await addition(3, 7)
    assert executions == 2

    await multiplication(2, 4)
    assert executions == 3

    # Shows that trying to bust all cache entries when there is no prefix is not working
    await cache_money.bust()
    executions = 0
    cache_money.prefix = None

    await addition(3, 4)
    assert executions == 1

    await addition(3, 7)
    assert executions == 2

    await multiplication(2, 4)
    assert executions == 3

    await cache_money.bust()

    await addition(3, 4)
    assert executions == 3

    await cache_money.bust(force=True)  # We do allow deletion with no prefix if force is set to True

    await addition(3, 4)
    assert executions == 4

    # Test when the cache is disabled
    await cache_money.bust()
    executions = 0
    cache_money.enabled = False

    await addition(3, 4)
    assert executions == 1

    await addition(3, 4)
    assert executions == 2

    assert await cache_money.get(addition.make_key(3, 4)) is None  # Show that get is disconnected
    assert await cache_money.set(addition.make_key(3, 4), 7) is True  # Show that the set is disconnected
    assert await cache_money.delete(addition.make_key(3, 4), make_key=False) is None  # Show that delete is disconnected
    assert await cache_money.bust() is None  # Show that bust is disconnected
    assert await cache_money.keys() == []  # Show that keys is disconnected

    # Check that we can set cache without a timeout
    cache_money.enabled = True
    cache_money.default_timeout = None
    cache_money.prefix = None
    await cache_money.bust()
    executions = 0

    await cache_money.set("pompatus", "puppetutes")
    assert await cache_money.get("pompatus") == "puppetutes"

    # Test that make_key can work a list
    cache_money.prefix = "cache-money-test"
    assert cache_money.make_key(["pompatus"]) == ["cache-money-test:pompatus"]

    await close_cache_money()
