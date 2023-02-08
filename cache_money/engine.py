import logging
from typing import Optional

import redis.asyncio

redis_conn: Optional[redis.asyncio.Redis] = None

log = logging.getLogger(__name__)


def init_connection(host: str, port: int = 6379, db: int = 0) -> redis.asyncio.Redis:
    global redis_conn

    url = f"redis://{host}:{port}"

    log.info(f"Connecting to redis {url}")
    redis_conn = redis.asyncio.from_url(
        url=url,
        encoding="utf-8",
        db=db,
    )

    return redis_conn


def get_connection() -> redis.asyncio.Redis:
    global redis_conn
    return redis_conn


async def close_connection():
    global redis_conn
    if redis_conn:
        await redis_conn.close()
