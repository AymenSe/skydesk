from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
import redis


from skydesk.api.classifier import Classifier
from skydesk.api.deps import get_classifier, get_session, get_redis
from skydesk.api.schemas import TicketCreate, TicketCreated, TicketOut
from skydesk.core.models import ESCALATE_INTENTS, Status, Ticket
from skydesk.core import queue, ratelimit
from skydesk.core.config import Settings, get_settings



router = APIRouter(prefix="/tickets", tags=["tickets"])

SessionDep = Annotated[Session, Depends(get_session)]
ClassifierDep = Annotated[Classifier, Depends(get_classifier)]
RedisDep = Annotated[redis.Redis, Depends(get_redis)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.post("", status_code=202, response_model=TicketCreated)
def create_ticket(
    body: TicketCreate,
    session: SessionDep,
    classifier: ClassifierDep,
    r: RedisDep,
    settings: SettingsDep,
) -> TicketCreated:
    if not ratelimit.allow(r, f"customer:{body.customer_email}", settings.rate_limit_per_minute):
        raise HTTPException(status_code=429, detail="Too many requests; try again in a minute")

    intent, confidence = classifier.predict(body.message)
    status = Status.ESCALATED if intent in ESCALATE_INTENTS else Status.QUEUED
    ticket = Ticket(
        customer_email=body.customer_email,
        message=body.message,
        intent=intent,
        confidence=confidence,
        status=status,
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    if ticket.status == Status.QUEUED:
        queue.enqueue(r, ticket.id)
    return TicketCreated(
        id=ticket.id, intent=intent, confidence=round(confidence, 3), status=status
    )



@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: UUID, session: SessionDep) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@router.get("", response_model=list[TicketOut])
def list_tickets(
    session: SessionDep,
    status: str | None = None,
    intent: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Ticket]:
    query = select(Ticket).order_by(Ticket.created_at.desc()).limit(limit)
    if status:
        query = query.where(Ticket.status == status)
    if intent:
        query = query.where(Ticket.intent == intent)
    return list(session.scalars(query))