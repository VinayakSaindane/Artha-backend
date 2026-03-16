from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends

from app.config import validate_api_key
from services.wealth_advisor_service import wealth_advisor_service

router = APIRouter(prefix="/ai", tags=["advisor"], dependencies=[Depends(validate_api_key)])


class AdvisorRequest(BaseModel):
    income: float
    expenses: float
    age: int
    risk_appetite: str = "moderate"
    savings: float = 0
    retirement_age: int = 55


@router.post("/wealth-advisor")
async def wealth_advisor(payload: AdvisorRequest) -> dict:
    return wealth_advisor_service.recommend(payload.model_dump())