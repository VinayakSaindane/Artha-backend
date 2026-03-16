from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends

from app.config import validate_api_key
from services.debt_pulse_service import debt_pulse_service

router = APIRouter(prefix="/ai", tags=["debt"], dependencies=[Depends(validate_api_key)])


class DebtPulseRequest(BaseModel):
    monthly_income: float | None = None
    income: float | None = None
    total_emi: float | None = None
    total_emis: float | None = None
    credit_used: float | None = None
    credit_limit: float | None = 100000
    outstanding_loans: float | None = None
    monthly_expenses: float | None = None
    trend: str | None = "STABLE"


@router.post("/debt-pulse")
async def debt_pulse(payload: DebtPulseRequest) -> dict:
    return debt_pulse_service.evaluate(payload.model_dump())