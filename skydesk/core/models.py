import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Status(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DRAFTED = "drafted"
    ESCALATED = "escalated"
    FAILED = "failed"


# Intents that go straight to a human, with no AI draft
ESCALATE_INTENTS = {"complaint", "other"}


class Base(DeclarativeBase):
    pass


class Policy(Base):
    __tablename__ = "policies"

    intent: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str]
    body: Mapped[str]


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_email: Mapped[str]
    message: Mapped[str]
    intent: Mapped[str]
    confidence: Mapped[float]
    status: Mapped[str] = mapped_column(default=Status.QUEUED)
    draft_reply: Mapped[str | None]
    model: Mapped[str | None]
    latency_ms: Mapped[int | None]
    attempts: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )