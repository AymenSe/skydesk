from contextlib import asynccontextmanager

from fastapi import FastAPI

from skydesk.api.classifier import IntentClassifier
from skydesk.api.routes import health, tickets
from skydesk.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Heavy objects load once here at startup
    settings = get_settings()
    app.state.classifier = IntentClassifier(settings.artifacts_dir, settings.intent_threshold)
    yield


app = FastAPI(title="SkyDesk", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(tickets.router)