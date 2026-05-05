import time
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    def __init__(self):
        self._store = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)

        if not item:
            return None

        value, expiry = item

        if time.time() > expiry:
            self._store.pop(key, None)
            logger.info(f"Cache EXPIRED: {key}")
            return None

        logger.info(f"Cache HIT: {key}")
        return value

    def set(self, key: str, value: Any, ttl_seconds: int = 60):
        expiry = time.time() + ttl_seconds
        self._store[key] = (value, expiry)
        logger.info(f"Cache SET: {key}")

    def delete(self, key: str):
        self._store.pop(key, None)
        logger.info(f"Cache DELETE: {key}")

    def clear(self):
        self._store.clear()
        logger.info("Cache CLEARED")


cache = SimpleCache()