# ─── Feature 8: In-Memory Cache ───────────────────────────────────────────────
import time
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    def __init__(self):
        self._store: dict = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            value, expiry = self._store[key]
            if time.time() < expiry:
                logger.info(f"Cache HIT: {key}")
                return value
            else:
                del self._store[key]
                logger.info(f"Cache EXPIRED: {key}")
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 60):
        self._store[key] = (value, time.time() + ttl_seconds)
        logger.info(f"Cache SET: {key} (TTL: {ttl_seconds}s)")

    def delete(self, key: str):
        if key in self._store:
            del self._store[key]
            logger.info(f"Cache DELETE: {key}")

    def clear(self):
        self._store.clear()
        logger.info("Cache CLEARED")


# Global cache instance
cache = SimpleCache()
