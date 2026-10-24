import logging
import signal
import time
from uuid import UUID

import redis
from sqlalchemy import update
from sqlalchemy.orm import Session, sessionmaker

from skydesk.core import cache, queue
from skydesk.core.config import Settings, get_settings
from skydesk.core.db import get_sessionmaker
from skydesk.core.models import Policy, Status, Ticket
from skydesk.worker.prompts import build_messages

log = logging.getLogger("skydesk.worker")


def claim(session: Session, ticket_id: UUID) -> bool:
    """Atomically move a ticket from queued to processing; False if it wasn't queued."""
    result = session.execute(
        update(Ticket)
        .where(Ticket.id == ticket_id, Ticket.status == Status.QUEUED)
        .values(status=Status.PROCESSING, attempts=Ticket.attempts + 1)
    )
    session.commit()
    return result.rowcount == 1


def handle_failure(session: Session, ticket_id: UUID, r: redis.Redis, settings: Settings) -> None:
    """Lab 6: give up immediately. Lab 7 replaces this with retries."""
    ticket = session.get(Ticket, ticket_id)
    ticket.status = Status.FAILED
    session.commit()


def process(
    ticket_id: str,
    session_factory: sessionmaker[Session],
    r: redis.Redis,
    llm,
    settings: Settings,
) -> None:
    tid = UUID(ticket_id)
    with session_factory() as session:
        if not claim(session, tid):
            log.info("skip %s: missing or already handled", ticket_id)
            return
        ticket = session.get(Ticket, tid)
        try:
            reply = cache.get_reply(r, llm.model_id, ticket.intent, ticket.message)
            if reply is not None:
                cache.record(r, "hit")
                latency_ms = 0
            else:
                cache.record(r, "miss")
                policy = session.get(Policy, ticket.intent)
                messages = build_messages(ticket.message, policy.title, policy.body)
                start = time.perf_counter()
                reply = llm.generate(messages, settings.llm_max_new_tokens)
                latency_ms = int((time.perf_counter() - start) * 1000)
                cache.set_reply(r, llm.model_id, ticket.intent, ticket.message, reply, settings.cache_ttl_seconds)
            ticket.draft_reply = reply
            ticket.model = llm.model_id
            ticket.latency_ms = latency_ms
            ticket.status = Status.DRAFTED
            session.commit()
            log.info("drafted %s in %d ms", ticket_id, latency_ms)
        except Exception:
            log.exception("failed on %s", ticket_id)
            session.rollback()
            handle_failure(session, tid, r, settings)


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = get_settings()
    r = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=15)
    # r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    session_factory = get_sessionmaker()

    from skydesk.worker.llm import LLM  # heavy import, only in the real worker

    log.info("loading %s on %s (%s)", settings.llm_model_id, settings.llm_device, settings.llm_dtype)
    llm = LLM(settings.llm_model_id, settings.llm_device, settings.llm_dtype)

    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        log.info("signal %s: finishing the current job, then exiting", signum)
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    log.info("worker ready")
    while not stopping:
        r.set(queue.HEARTBEAT_KEY, "1", ex=30)
        ticket_id = queue.dequeue(r, timeout=5)
        if ticket_id:
            process(ticket_id, session_factory, r, llm, settings)
    log.info("worker stopped cleanly")


if __name__ == "__main__":
    run()