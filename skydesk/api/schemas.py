from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TicketCreate(BaseModel):
    customer_email: EmailStr
    message: str = Field(min_length=5, max_length=2000)

class TicketCreated(BaseModel):
    id: UUID
    intent: str
    confidence: float
    status: str


class TicketOut(BaseModel):
    # TODO(Lab 3): let this model be built directly from a SQLAlchemy object's attributes
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_email: str
    message: str
    intent: str
    confidence: float
    status: str
    draft_reply: str | None
    model: str | None
    latency_ms: int | None
    attempts: int
    created_at: datetime
    updated_at: datetime