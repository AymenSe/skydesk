from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from skydesk.api.classifier import Classifier
from skydesk.api.deps import get_classifier, get_session
from skydesk.api.schemas import TicketCreate, TicketCreated, TicketOut
from skydesk.core.models import ESCALATE_INTENTS, Status, Ticket

router = APIRouter(prefix="/tickets", tags=["tickets"])

SessionDep = Annotated[Session, Depends(get_session)]
ClassifierDep = Annotated[Classifier, Depends(get_classifier)]


@router.post("", status_code=202, response_model=TicketCreated)
def create_ticket(
    body: TicketCreate, session: SessionDep, classifier: ClassifierDep
) -> TicketCreated:
    intent, confidence = classifier.predict(body.message)
    # TODO(Lab 3): complaints and "other" are escalated; everything else is queued
    status = Status.ESCALATED if intent in ESCALATE_INTENTS else Status.QUEUED
    ticket = Ticket(
        customer_email=body.customer_email,
        message=body.message,
        intent=intent,
        confidence=confidence,
        status=status,
    )
    session.add(ticket)
    # TODO(Lab 3): save the ticket, then reload it so the database defaults are filled in
    session.commit()
    session.refresh(ticket)
    return TicketCreated(
        id=ticket.id, intent=intent, confidence=round(confidence, 3), status=status
    )


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: UUID, session: SessionDep) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        # TODO(Lab 3): unknown id → 404 with a helpful message
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