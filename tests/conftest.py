import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from skydesk.api import deps
from skydesk.api.main import app
from skydesk.core.models import Base


class FakeClassifier:
    def __init__(self, intent: str = "baggage", confidence: float = 0.9) -> None:
        self.intent = intent
        self.confidence = confidence

    def predict(self, text: str) -> tuple[str, float]:
        return self.intent, self.confidence


@pytest.fixture
def session_factory():
    # A fresh in-memory database per test, shared safely across threads
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def classifier():
    return FakeClassifier()


@pytest.fixture
def client(session_factory, classifier):
    def override_session():
        with session_factory() as session:
            yield session

    app.dependency_overrides[deps.get_session] = override_session
    app.dependency_overrides[deps.get_classifier] = lambda: classifier
    yield TestClient(app)
    app.dependency_overrides.clear()
