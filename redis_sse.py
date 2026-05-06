import os
import json
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

_redis = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    return _redis


async def publish_sse(channel: str, data: dict) -> None:
    try:
        r = await get_redis()
        await r.publish(channel, json.dumps(data, ensure_ascii=False, default=str))
    except Exception as e:
        print(f"[Redis SSE] publish 실패 (channel={channel}): {e}")
