import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None
        self._available: bool = False

    async def connect(self) -> None:
        settings = get_settings()
        try:
            self._client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await self._client.ping()
            self._available = True
            logger.info("redis_connected", url=settings.REDIS_URL)
        except Exception as e:
            self._available = False
            logger.warning("redis_unavailable", error=str(e))

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    async def get(self, key: str) -> Any | None:
        if not self._available or not self._client:
            return None
        try:
            value = await self._client.get(key)
            if value is not None:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning("redis_get_error", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        if not self._available or not self._client:
            return False
        try:
            await self._client.set(key, json.dumps(value, default=str), ex=ttl)
            return True
        except Exception as e:
            logger.warning("redis_set_error", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        if not self._available or not self._client:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.warning("redis_delete_error", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        if not self._available or not self._client:
            return False
        try:
            return bool(await self._client.exists(key))
        except Exception:
            return False


redis_cache = RedisCache()


async def get_redis_cache() -> RedisCache:
    return redis_cache
