from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .routers import (
    analytics,
    auth_router,
    dashboard,
    reprice,
    settings_router,
    sold_not_updated,
    status_options,
    stores,
    vehicles,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dealership Inventory Snapshot API")

app.add_middleware(
    CORSMiddleware,
    # Auth is a Bearer token in the Authorization header, not a cookie, so no
    # credentials mode is needed — origins can be a real allow-list instead of "*".
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(stores.router)
app.include_router(vehicles.router)
app.include_router(status_options.router)
app.include_router(settings_router.router)
app.include_router(reprice.router)
app.include_router(analytics.router)
app.include_router(sold_not_updated.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"ok": True}
