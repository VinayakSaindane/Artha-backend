from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends

from app.config import validate_api_key
from services.loan_prediction_service import loan_prediction_service

router = APIRouter(prefix="/ai", tags=["loan"], dependencies=[Depends(validate_api_key)])


class LoanPredictorRequest(BaseModel):
    salary: float | None = None
    income: float | None = None
    existing_loans: float | None = None
    existing_emis: float | None = None
    credit_score: int
    employment_type: str
    loan_amount: float | None = None


@router.post("/loan-predictor")
async def loan_predictor(payload: LoanPredictorRequest) -> dict:
    return loan_prediction_service.predict(payload.model_dump())