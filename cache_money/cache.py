import hashlib
import inspect
import logging
import pickle
from functools import wraps
from typing import Any, Callable, List, Optional, Union

import aioredis

from cache_money import engine
from cache_money.constants import CACHE_HOUR
from cache_money.utils import decode

log = logging.getLogger(__name__)


class CacheMoney(object):
    """
    Walrus-inspired redis cache implementation that supports asyncio. Implement simple GET/SET/DELETE operations,
    and a decorator.
    """

    def __init__(self):
        self.conn: Optional[aioredis.client.Redis] = None
        self.prefix: Optional[str] = None
        self.default_timeout: Optional[int] = None
        self.enabled: bool = False

    def setup_cache(
        self,
        conn: Optional[aioredis.client.Redis] = None,
        prefix: Optional[str] = None,
        default_timeout: Optional[int] = None,
        enabled: bool = False,
    ):
        """
        Setup the caching.

        Args:
            conn: Active aioredis client, optional when in debug.
            prefix: A prefix added in front of the cache key.
            default_timeout: Default timeout for all cache entries that don't specify their own time.
            enabled: Whether the cache is active or not.
        """
        self.conn = conn
        self.prefix = prefix
        self.default_timeout = default_timeout
        self.enabled = enabled

    def make_key(self, keys: Union[str, List[str]]) -> Union[str, List[str]]:
        """
        Apply the prefix in front of the key separated by a colon `:` if the prefix has been set for the class.

        Args:
            keys: Keys to add the prefix to.

        Returns:
            Keys with the prefix added.BBB
        """
        if isinstance(keys, str):
            return ":".join((self.prefix, keys)) if self.prefix else keys
        return [(":".join((self.prefix, k)) if self.prefix else k) for k in keys]

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from the cache. In the event the value does not exist, return the `default`.

        Trying to access a non-existing key in Redis returns None from aioredis. This effectively makes `None` a non
        cacheable value for Cache Money.
        """
        if not self.enabled:
            return default

        key = self.make_key(key)

        try:
            value = await self.conn.get(key)
        except Exception:
            log.exception(f"Exception trying to retrieve key [{key}] from Redis")
            return default

        if value is not None:
            return pickle.loads(value)
        else:
            return value

    async def set(self, key: str, value: Any, timeout: int = None) -> bool:
        """
        Cache the given `value` in the specified `key`. If no timeout is specified, the default timeout will be used.
        """
        if not self.enabled:
            return True

        key = self.make_key(key)
        if timeout is None:
            timeout = self.default_timeout

        try:
            pickled_value = pickle.dumps(value)
        except Exception:
            log.exception(f"Error pickling object for caching: key=[{key}]; value type=[{type(value)}]")
            return False

        try:
            if timeout:
                return await self.conn.setex(key, int(timeout), pickled_value)
            else:
                return await self.conn.set(key, pickled_value)
        except Exception:
            log.exception(f"Exception trying to set key [{key}] in Redis")
            return False

    async def delete(self, keys: Union[str, List[str], bytes, List[bytes]], make_key: bool = True):
        """
        Remove one or more keys from the cache.

        Args:
            keys: One or more keys to delete, can be string or byte string. You cannot mix and match strings and byte
                strings if you send a list.
            make_key: Whether the key construction function is to be ran on the keys received. If byte strings are
                received, the make_key function will not be executed.
        """
        if not self.enabled or not keys:
            return

        if make_key and isinstance(keys[0], str):
            keys = self.make_key(keys)

        keys = [keys] if not isinstance(keys, list) else keys

        return await self.conn.delete(*keys)

    async def bust(self, force: bool = False):
        """
        Delete all keys in Redis starting with the value for the prefix. If there are no value defined for the
        prefix, that means that there is no way to know which keys belongs to cache-money and which keys belong to
        something else using the redis DB Cache Money is connected to. If you want to delete keys without a prefix set
        for Cache Money, you need to pass force=True.
        """
        if not self.enabled:
            return

        if not self.prefix and not force:
            log.warning(
                "Cache Money skipped bust on all Cache Money values because no prefix has been set for "
                "Cache Money which will result in all keys on the redis DB being removed. You can pass "
                "force=True to the function `bust` to execute the bust without a prefix."
            )
            return

        keys = await self.keys(decode_to_str=False)
        return await self.delete(keys)

    async def keys(self, function: Callable = None, decode_to_str: bool = True) -> Union[List[bytes], List[str]]:
        """
        Return keys from Redis that were cached by Cache Money. Note that if the parameter function is not provided and
        Cache Money doesn't have a value for its prefix attribute, all keys in the Redis DB will be returned, even if
        the keys were not set up by Cache Money.

        Args:
            function: If provided will only returns keys representing cache entries for the function.
            decode_to_str: Whether the keys should be decoded before being returned to this function. If set to False
                the function will return byte strings instead of strings.

        Returns:
            A list of string or byte strings representing the cache keys in Redis.
        """
        if not self.enabled:
            return []

        function_name = f"{inspect.getmodule(function).__name__}:{function.__name__}" if function else ""

        keys = await self.conn.keys(self.make_key(function_name) + "*")
        if decode_to_str:
            keys = [decode(key) for key in keys]
        return keys

    def _key_fn(a, k) -> str:
        """Generate a hash from args and kwargs."""
        return hashlib.md5(pickle.dumps((a, k))).hexdigest()

    def cached(self, key_fn: Callable = _key_fn, timeout: int = None) -> Any:
        """
        Decorator that will transparently cache calls to the wrapped function. By default, the cache key will be made
        up of the arguments passed in (like memoize), but you can override this by specifying a custom `key_fn`.

        Usage:
            from cache_money import cache_money
            from cache_money.constants import CACHE_MINUTE

            @cache.cached(timeout=CACHE_MINUTE)
            async def addition(x, y):
                return x + y

            await addition(3, 4)  # Function is called.
            await addition(3, 4)  # Not called, value is cached.
            await add_numbers.bust(3, 4)  # Clear cache for (3, 4).
            await add_numbers(3, 4)  # Function is called.

        The decorated function also gains a new attribute named `bust` which will clear the cache for the given args.

        Args:
            key_fn: Function used to generate a key from the given args and kwargs.
            timeout: Time to cache return values in seconds.

        Returns:
            Return the result of the decorated function call with the given args and kwargs.
        """

        def decorator(fn):
            def make_key(args, kwargs):
                """Apply the module and name of the function in front of the key, separated by a colon `:`."""
                return f"{inspect.getmodule(fn).__name__}:{fn.__name__}:{key_fn(args, kwargs)}"

            async def bust(*args, **kwargs):
                """Bust a specific cache entry for the decorated function that match the provided args and kwargs."""
                return await self.delete(make_key(args, kwargs))

            async def bust_all():
                """Bust all cache entries for the decorated function."""
                keys = await self.keys(fn, decode_to_str=False)
                return await self.delete(keys)

            @wraps(fn)
            async def inner(*args, **kwargs):
                if not self.enabled:
                    return await fn(*args, **kwargs)

                key = make_key(args, kwargs)
                res = await self.get(key)
                if res is None:
                    res = await fn(*args, **kwargs)

                    if res is not None:  # None is not cacheable in Cache Money
                        await self.set(key, res, timeout)

                return res

            inner.bust = bust
            inner.bust_all = bust_all
            inner.make_key = make_key
            return inner

        return decorator


cache_money: CacheMoney = CacheMoney()


def init_cache_money(
    host: str,
    port: int = 6379,
    prefix: str = None,
    db: int = 0,
    default_timeout: Optional[int] = CACHE_HOUR,
    enabled: bool = True,
):
    """
    Create the connection to Redis and setup Cache Money to use it.

    Args:
        host: redis host
        port: redis port
        prefix: An optional prefix to add in front of all cache keys generated.
        db: The database number in redis.
        default_timeout: A default timeout in seconds to set on function cache if no timeout is provided when
            decorating the function.
        enabled: If the cache is enabled or not. Set it to False when you don't want to enable cache for local
            development or for debugging. When set to False no connection to Redis will be established and all call to
            Cache Money will be ignored.
    """
    if not enabled:
        log.info("Initialization of Cache Money skipped because enabled=False")
        return

    global cache_money

    log.info("Initializing Cache Money..")

    conn = engine.get_connection()
    if not conn:
        conn = engine.init_connection(
            host=host,
            port=port,
            db=db,
        )

    cache_money.setup_cache(conn=conn, prefix=prefix, default_timeout=default_timeout, enabled=enabled)


async def close_cache_money():
    await engine.close_connection()
