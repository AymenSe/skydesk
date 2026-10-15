from fastapi import FastAPI

from skydesk.api.routes import health

app = FastAPI(title="SkyDesk", version="0.1.0")
# TODO(Lab 2): register the health router on the app
app.include_router(health.router)

