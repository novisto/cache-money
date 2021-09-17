import asyncio

from cache_money import cache_money, init_cache_money
from cache_money.constants import CACHE_MINUTE

init_cache_money(host="localhost", prefix="example")
executions = 0


@cache_money.cached(timeout=CACHE_MINUTE)
async def addition(x: int, y: int) -> int:
    print(f"  ... executing addition({x}, {y})")
    return x + y


async def cached_calls():
    print(f"\nCalling addition(3, 4)")
    print(await addition(3, 4))

    print(f"\nCalling addition(3, 7)")
    print(await addition(3, 7))

    print(f"\nCalling addition(3, 4)")
    print(await addition(3, 4))


async def busting():
    print(f"\nBusting cache for addition(3, 4)")
    await addition.bust(3, 4)

    print(f"\nCalling addition(3, 4)")
    print(await addition(3, 4))

    print(f"\nCalling addition(3, 4)")
    print(await addition(3, 4))

    print(f"\nCalling addition(3, 7)")
    print(await addition(3, 7))

    print(f"\nBusting cache for all cache entries for function addition")
    await addition.bust_all()

    print(f"\nCalling addition(3, 4)")
    print(await addition(3, 4))

    print(f"\nCalling addition(3, 7)")
    print(await addition(3, 7))



loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(cached_calls())
loop.run_until_complete(busting())
