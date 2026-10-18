import time

import redis


def allow(r: redis.Redis, key: str, limit: int, window_seconds: int = 60) -> bool:
    """Fixed-window limiter: at most `limit` calls per key in each window."""
    window = int(time.time() // window_seconds)
    bucket = f"ratelimit:{key}:{window}"
    count = r.incr(bucket)
    if count == 1:
        r.expire(bucket, window_seconds)
    return count <= limit