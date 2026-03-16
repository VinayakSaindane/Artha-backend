from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.database import ping_database
from ai_services import macro_risk_engine_service
from routes.advisor_routes import router as advisor_router
from routes.agreement_routes import router as agreement_router
from routes.debt_routes import router as debt_router
from routes.intelligence_routes import router as intelligence_router
from routes.loan_routes import router as loan_router
from routes.spending_routes import router as spending_router

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")
scheduler = AsyncIOScheduler(timezone="UTC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agreement_router)
app.include_router(spending_router)
app.include_router(debt_router)
app.include_router(advisor_router)
app.include_router(loan_router)
app.include_router(intelligence_router)


@app.on_event("startup")
async def startup_event() -> None:
    if not scheduler.running:
        scheduler.add_job(
            macro_risk_engine_service.scheduled_refresh,
            "interval",
            hours=6,
            id="macro-risk-monitor",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()

    # Prime cache immediately so first dashboard hit gets low latency.
    await macro_risk_engine_service.scheduled_refresh()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


@app.get("/")
async def root() -> dict:
    return {"service": settings.app_name, "status": "running"}


@app.get("/health")
async def health() -> dict:
    db_ok = await ping_database()
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}