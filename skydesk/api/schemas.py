from pydantic import BaseModel, Field, EmailStr


class TicketCreate(BaseModel):
    customer_email: EmailStr
    message: str = Field(min_length=5, max_length=2000)

