from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from app.config import validate_api_key
from services.festival_spending_service import festival_spending_service

router = APIRouter(prefix="/ai", tags=["spending"], dependencies=[Depends(validate_api_key)])


class FestivalSpendingRequest(BaseModel):
    user_id: str | None = None
    festival_name: str | None = None
    name: str | None = None
    festival_date: str | None = None
    date: str | None = None
    income: float | None = Field(default=50000)


@router.post("/festival-spending")
async def festival_spending(payload: FestivalSpendingRequest) -> dict:
    event_name = payload.festival_name or payload.name or "Festival"
    event_date = payload.festival_date or payload.date
    if not event_date:
        raise HTTPException(status_code=400, detail="festival_date or date is required")

    return await festival_spending_service.predict(
        user_id=payload.user_id,
        festival_name=event_name,
        festival_date=event_date,
        income=payload.income,
    )