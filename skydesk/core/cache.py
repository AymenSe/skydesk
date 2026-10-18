import hashlib
import json

import redis


def _key(model_id: str, intent: str, message: str) -> str:
    normalized = " ".join(message.lower().split())
    raw = json.dumps([model_id, intent, normalized])
    return "skydesk:reply:" + hashlib.sha256(raw.encode()).hexdigest()


def get_reply(r: redis.Redis, model_id: str, intent: str, message: str) -> str | None:
    return r.get(_key(model_id, intent, message))


def set_reply(
    r: redis.Redis, model_id: str, intent: str, message: str, reply: str, ttl: int
) -> None:
    # TODO(Lab 5): store the reply so it expires after `ttl` seconds
    r.set(_key(model_id, intent, message), reply, ex=ttl)

def record(r: redis.Redis, outcome: str) -> None:
    """Count a cache 'hit' or 'miss'."""
    r.incr(f"skydesk:cache:{outcome}")


def stats(r: redis.Redis) -> dict:
    hits = int(r.get("skydesk:cache:hit") or 0)
    misses = int(r.get("skydesk:cache:miss") or 0)
    total = hits + misses
    return {"hits": hits, "misses": misses, "hit_rate": round(hits / total, 3) if total else 0.0}