from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session

from skydesk.api.classifier import Classifier
from skydesk.core.db import get_sessionmaker


def get_session() -> Iterator[Session]:
    # TODO(Lab 3): open a session from the sessionmaker; the `with` block closes it
    # after the request finishes
    factory = get_sessionmaker()
    with factory() as session:
        yield session


def get_classifier(request: Request) -> Classifier:
    return request.app.state.classifier