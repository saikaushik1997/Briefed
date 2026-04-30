import redis.asyncio as aioredis
import hashlib
from ..config import settings

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def hash_file(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def hash_page(page_content: str, prompt_version: str) -> str:
    return hashlib.sha256(f"{page_content}:{prompt_version}".encode()).hexdigest()


async def get_document_cache(file_hash: str) -> str | None:
    """Returns cached document_id if this exact PDF was processed before."""
    return await get_redis().get(f"doc:{file_hash}")


async def set_document_cache(file_hash: str, document_id: str, ttl_days: int = 30):
    await get_redis().setex(f"doc:{file_hash}", ttl_days * 86400, document_id)


async def get_page_cache(page_hash: str) -> dict | None:
    """Returns cached agent output for a page+prompt combination."""
    import json
    value = await get_redis().get(f"page:{page_hash}")
    return json.loads(value) if value else None


async def set_page_cache(page_hash: str, result: dict, ttl_days: int = 7):
    import json
    await get_redis().setex(f"page:{page_hash}", ttl_days * 86400, json.dumps(result))
