import hashlib
import json
import os
from redis import Redis
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

redis_conn = Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379))
)

def get_cache_key(prefix: str, content: str) -> str:
    """Generate a stable cache key based on content hash."""
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    return f"{prefix}:{content_hash}"

def get_from_cache(key: str) -> Optional[Dict[str, Any]]:
    """Retrieve JSON parsed data from Redis cache."""
    try:
        data = redis_conn.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"Redis cache read error: {e}")
    return None

def set_in_cache(key: str, data: Dict[str, Any], ttl_seconds: int = 3600):
    """Store JSON serializable data in Redis with a TTL."""
    try:
        redis_conn.setex(key, ttl_seconds, json.dumps(data))
    except Exception as e:
        print(f"Redis cache write error: {e}")
