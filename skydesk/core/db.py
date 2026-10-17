from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from skydesk.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    # pool_pre_ping tests each pooled connection before use, so a Postgres restart
    # doesn't break the next request
    return create_engine(get_settings().sqlalchemy_url, pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)