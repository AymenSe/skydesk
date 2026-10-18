from collections.abc import Iterator
from functools import lru_cache

from fastapi import Request
from sqlalchemy.orm import Session

from skydesk.api.classifier import Classifier
from skydesk.core.db import get_sessionmaker

import redis
from skydesk.core.config import get_settings



def get_session() -> Iterator[Session]:
    factory = get_sessionmaker()
    with factory() as session:
        yield session

@lru_cache
def _redis_client() -> redis.Redis:
    return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)

def get_redis() -> redis.Redis:
    return _redis_client()

def get_classifier(request: Request) -> Classifier:
    return request.app.state.classifier
