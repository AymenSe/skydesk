import fakeredis
import pytest

from skydesk.core import cache
from skydesk.core.config import Settings
from skydesk.core.models import Policy, Status, Ticket
from skydesk.worker.main import process

BAGGAGE = Policy(intent="baggage", title="Baggage", body="Delayed bags are delivered free.")


class FakeLLM:
    model_id = "fake-model"

    def __init__(self, fail=False):
        self.calls = 0
        self.fail = fail

    def generate(self, messages, max_new_tokens):
        self.calls += 1
        if self.fail:
            raise RuntimeError("boom")
        return "Your bag will be delivered free of charge."


@pytest.fixture
def r():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def settings():
    return Settings(database_url="sqlite://", max_attempts=2, llm_max_new_tokens=16)


def add_ticket(session_factory, message="Where is my bag?", status=Status.QUEUED):
    with session_factory() as s:
        s.merge(BAGGAGE)
        t = Ticket(customer_email="a@b.co", message=message, intent="baggage",
                   confidence=0.9, status=status)
        s.add(t)
        s.commit()
        return str(t.id)


def load(session_factory, ticket_id):
    from uuid import UUID

    with session_factory() as s:
        return s.get(Ticket, UUID(ticket_id))


def test_drafts_a_queued_ticket(session_factory, r, settings):
    tid = add_ticket(session_factory)
    process(tid, session_factory, r, FakeLLM(), settings)
    t = load(session_factory, tid)
    assert t.status == Status.DRAFTED
    assert t.draft_reply.startswith("Your bag")
    assert t.model == "fake-model"


def test_identical_question_hits_the_cache(session_factory, r, settings):
    llm = FakeLLM()
    process(add_ticket(session_factory), session_factory, r, llm, settings)
    tid2 = add_ticket(session_factory, message="where is my  BAG?")
    process(tid2, session_factory, r, llm, settings)
    assert llm.calls == 1
    assert load(session_factory, tid2).latency_ms == 0
    assert cache.stats(r)["hits"] == 1


def test_already_drafted_ticket_is_skipped(session_factory, r, settings):
    llm = FakeLLM()
    tid = add_ticket(session_factory, status=Status.DRAFTED)
    process(tid, session_factory, r, llm, settings)
    assert llm.calls == 0


def test_failure_marks_the_ticket_failed(session_factory, r, settings):
    tid = add_ticket(session_factory)
    process(tid, session_factory, r, FakeLLM(fail=True), settings)
    assert load(session_factory, tid).status == Status.FAILED
