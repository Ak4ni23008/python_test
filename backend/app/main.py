"""
CloudTrade API — runs on Railway cloud, not user devices.

Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Worker: python -m app.workers.live_worker
"""

from __future__ import annotations

import socket

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.database import init_db
from app.rate_limit import rate_limit_middleware

settings = get_settings()
HOST = socket.gethostname()

app = FastAPI(
    title="CloudTrade API",
    description="Cloud-hosted algorithmic trading MVP — execution on Railway workers",
    version="1.0.0",
)

origins = settings.cors_origin_list
if settings.environment == "development":
    origins = list(set(origins + ["http://localhost:3000", "http://127.0.0.1:3000"]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(rate_limit_middleware)
app.include_router(router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "host": HOST,
        "cloud": settings.is_railway,
        "service": "api",
    }


@app.get("/")
def root():
    return {
        "app": "CloudTrade",
        "docs": "/docs",
        "cloud_status": "/api/cloud/status",
        "frontend": "Deploy Next.js frontend separately or set NEXT_PUBLIC_API_URL",
    }
