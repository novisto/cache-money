import logging
from typing import Optional

import aioredis

redis_conn: Optional[aioredis.client.Redis] = None

log = logging.getLogger(__name__)


def init_connection(host: str, port: int = 6379, db: int = 0) -> aioredis.client.Redis:
    global redis_conn

    url = f"redis://{host}:{port}"

    log.info(f"Connecting to redis {url}")
    redis_conn = aioredis.from_url(
        url=url,
        encoding="utf-8",
        db=db,
    )

    return redis_conn


def get_connection() -> aioredis.client.Redis:
    global redis_conn
    return redis_conn


async def close_connection():
    global redis_conn
    if redis_conn:
        await redis_conn.close()
