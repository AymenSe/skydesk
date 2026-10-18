from uuid import UUID

import redis

QUEUE_KEY = "skydesk:jobs"
HEARTBEAT_KEY = "skydesk:worker:heartbeat"


def enqueue(r: redis.Redis, ticket_id: UUID | str) -> None:
    # TODO(Lab 5): push the id onto the LEFT end; the worker pops from the right (FIFO)
    r.lpush(QUEUE_KEY, str(ticket_id))


def dequeue(r: redis.Redis, timeout: int = 5) -> str | None:
    """Block up to `timeout` seconds for a job; return a ticket id or None."""
    item = r.brpop(QUEUE_KEY, timeout=timeout)
    return item[1] if item else None


def depth(r: redis.Redis) -> int:
    return r.llen(QUEUE_KEY)