from typing import Annotated

import redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from skydesk.api.deps import get_redis, get_session
from skydesk.core import cache, queue
from skydesk.core.models import Ticket

router = APIRouter(tags=["health"])
SessionDep = Annotated[Session, Depends(get_session)]
RedisDep = Annotated[redis.Redis, Depends(get_redis)]


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
def ready(session: SessionDep, r: RedisDep) -> dict:
    try:
        session.execute(text("SELECT 1"))
        r.ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"not ready: {exc}") from exc
    return {"status": "ready"}


@router.get("/stats")
def stats(session: SessionDep, r: RedisDep) -> dict:
    rows = session.execute(select(Ticket.status, func.count()).group_by(Ticket.status)).all()
    return {
        "tickets_by_status": {status: count for status, count in rows},
        "queue_depth": queue.depth(r),
        "worker_alive": bool(r.exists(queue.HEARTBEAT_KEY)),
        "cache": cache.stats(r),
    }