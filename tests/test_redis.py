import fakeredis
import pytest

from skydesk.api.main import app
from skydesk.core import cache, queue, ratelimit
from skydesk.core.config import Settings, get_settings

VALID = {"customer_email": "ana@example.com", "message": "My bag did not arrive in Lisbon"}


@pytest.fixture
def r():
    return fakeredis.FakeRedis(decode_responses=True)


def test_rate_limit_allows_up_to_the_limit(r):
    results = [ratelimit.allow(r, "customer:a", limit=3, window_seconds=3600) for _ in range(4)]
    assert results == [True, True, True, False]


def test_rate_limit_buckets_expire(r):
    ratelimit.allow(r, "customer:a", limit=3, window_seconds=60)
    [key] = r.keys("ratelimit:*")
    assert 0 < r.ttl(key) <= 60


def test_cache_ignores_case_and_spacing_but_not_model(r):
    cache.set_reply(r, "m1", "baggage", "Where is  my BAG?", "reply", ttl=60)
    assert cache.get_reply(r, "m1", "baggage", "where is my bag?") == "reply"
    assert cache.get_reply(r, "m2", "baggage", "where is my bag?") is None


def test_queue_is_first_in_first_out(r):
    queue.enqueue(r, "first")
    queue.enqueue(r, "second")
    assert queue.dequeue(r, timeout=1) == "first"
    assert queue.depth(r) == 1


def test_queued_ticket_is_enqueued(client, fake_redis):
    ticket_id = client.post("/tickets", json=VALID).json()["id"]
    assert fake_redis.lrange(queue.QUEUE_KEY, 0, -1) == [ticket_id]


def test_escalated_ticket_is_not_enqueued(client, classifier, fake_redis):
    classifier.intent = "complaint"
    client.post("/tickets", json=VALID)
    assert fake_redis.llen(queue.QUEUE_KEY) == 0


def test_flood_gets_429(client):
    app.dependency_overrides[get_settings] = lambda: Settings(rate_limit_per_minute=2)
    codes = [client.post("/tickets", json=VALID).status_code for _ in range(3)]
    assert codes == [202, 202, 429]


def test_stats_counts_tickets(client, classifier):
    client.post("/tickets", json=VALID)
    classifier.intent = "complaint"
    client.post("/tickets", json=VALID)
    body = client.get("/stats").json()
    assert body["tickets_by_status"] == {"queued": 1, "escalated": 1}
    assert body["queue_depth"] == 1
    assert body["worker_alive"] is False
