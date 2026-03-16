from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query

from app.config import validate_api_key
from ai_services import (
    emergency_detector_service,
    festival_intelligence_service,
    financial_simulator_service,
    habit_score_service,
    risk_radar_service,
    scam_detector_service,
    scenario_engine_service,
    whatsapp_parser_service,
)

router = APIRouter(prefix="/ai", tags=["financial-intelligence"], dependencies=[Depends(validate_api_key)])


class RiskRadarRequest(BaseModel):
    income: float
    expenses: float
    savings: float | None = None
    existing_loans: float | None = 0
    monthly_expense_trend: list[float] | None = None


class ScamLoanRequest(BaseModel):
    loan_app_name: str
    interest_rate: float
    loan_offer_details: str | None = None


class SimulationRequest(BaseModel):
    decision: str | None = "Buy Car"
    car_price: float = 0
    loan_emi: float = 0
    current_income: float
    expenses: float
    existing_emi: float | None = 0
    savings: float | None = None


class WhatIfRequest(BaseModel):
    scenario_name: str | None = "Custom Scenario"
    income: float
    expenses: float
    emi: float
    salary_change_percent: float | None = 0
    job_loss_months: int | None = 0
    new_emi: float | None = 0
    investment_increase: float | None = 0
    marriage_cost: float | None = 0
    child_education_monthly: float | None = 0
    current_net_worth: float | None = 0
    current_retirement_corpus: float | None = 0


class EmergencyRequest(BaseModel):
    income: float | None = 0
    savings: float
    monthly_expenses: float
    trigger: str | None = "salary_delay"


class FestivalIntelligenceRequest(BaseModel):
    user_id: str | None = None
    festival_name: str
    income: float
    monthly_expenses: float


class WhatsappExpenseRequest(BaseModel):
    user_id: str | None = None
    message: str
    category_budget: float | None = 2500


@router.post("/risk-radar")
async def risk_radar(payload: RiskRadarRequest) -> dict:
    return risk_radar_service.evaluate(payload.model_dump())


@router.post("/loan-scam-check")
async def loan_scam_check(payload: ScamLoanRequest) -> dict:
    return await scam_detector_service.evaluate(payload.model_dump())


@router.post("/simulation")
async def simulation(payload: SimulationRequest) -> dict:
    return financial_simulator_service.evaluate(payload.model_dump())


@router.post("/what-if")
async def what_if(payload: WhatIfRequest) -> dict:
    return scenario_engine_service.evaluate(payload.model_dump())


@router.post("/emergency-detector")
async def emergency_detector(payload: EmergencyRequest) -> dict:
    return emergency_detector_service.evaluate(payload.model_dump())


@router.post("/festival-intelligence")
async def festival_intelligence(payload: FestivalIntelligenceRequest) -> dict:
    return await festival_intelligence_service.evaluate(payload.model_dump())


@router.post("/whatsapp-expense")
async def whatsapp_expense(payload: WhatsappExpenseRequest) -> dict:
    return await whatsapp_parser_service.evaluate(payload.model_dump())


@router.get("/habit-score")
async def habit_score(user_id: str = Query(..., min_length=1)) -> dict:
    return await habit_score_service.evaluate({"user_id": user_id})
