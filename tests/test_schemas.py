import pytest
from pydantic import ValidationError

from skydesk.api.schemas import TicketCreate


def test_valid_ticket():
    ticket = TicketCreate(customer_email="ana@example.com", message="Where is my bag?")
    assert ticket.message == "Where is my bag?"


@pytest.mark.parametrize(
    "email,message",
    [
        ("not-an-email", "Where is my bag?"),
        ("ana@example.com", "hi"),
        ("ana@example.com", "x" * 2001),
    ],
)
def test_invalid_tickets(email, message):
    with pytest.raises(ValidationError):
        TicketCreate(customer_email=email, message=message)