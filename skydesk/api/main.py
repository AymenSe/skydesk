from contextlib import asynccontextmanager

from fastapi import FastAPI

from skydesk.api.classifier import KeywordClassifier
from skydesk.api.routes import health, tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Heavy objects load once here at startup
    app.state.classifier = KeywordClassifier()
    yield


app = FastAPI(title="SkyDesk", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(tickets.router)