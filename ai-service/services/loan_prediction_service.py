from __future__ import annotations

from typing import Any

from cachetools import TTLCache

from app.config import get_settings
from models.loan_approval_model import LoanApprovalModel


EMPLOYMENT_CODE = {
    "salaried": 1,
    "self-employed": 0,
    "business": 0,
}


class LoanPredictionService:
    def __init__(self) -> None:
        settings = get_settings()
        self.cache = TTLCache(maxsize=2048, ttl=settings.cache_ttl_seconds)
        self.model = LoanApprovalModel.build()

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        cache_key = str(hash(str(sorted(payload.items()))))
        if cache_key in self.cache:
            return self.cache[cache_key]

        salary = float(payload.get("salary") or payload.get("income") or 50000)
        existing_loans = float(payload.get("existing_loans") or payload.get("existing_emis") or 0)
        credit_score = int(payload.get("credit_score") or 700)
        employment_type = str(payload.get("employment_type") or "salaried").lower()
        loan_amount = float(payload.get("loan_amount") or salary * 10)

        loan_ratio = existing_loans / max(salary, 1.0)
        employment_code = EMPLOYMENT_CODE.get(employment_type, 0)
        probability = self.model.predict_approval_probability(salary, loan_ratio, credit_score, employment_code)
        approval_probability = int(round(probability * 100))

        risk_factors = []
        if credit_score < 700:
            risk_factors.append("Credit score below preferred lender threshold")
        if loan_ratio > 0.4:
            risk_factors.append("Existing debt burden is high")
        if employment_code == 0:
            risk_factors.append("Income volatility considered for non-salaried profile")

        improvement_tips = [
            {"action": "Reduce active EMI obligations by 10-15%", "impact": "High"},
            {"action": "Maintain credit utilization below 30% for 3 billing cycles", "impact": "High"},
            {"action": "Avoid new hard inquiries before application", "impact": "Med"},
        ]

        if approval_probability >= 75:
            verdict = "Likely Approved"
        elif approval_probability >= 45:
            verdict = "Marginal"
        else:
            verdict = "High Risk"

        result = {
            "approval_probability": approval_probability,
            "risk_factors": risk_factors,
            "improvement_tips": improvement_tips,
            # Compatibility fields for existing frontend.
            "verdict": verdict,
            "recommended_loan_amount": int(round(min(loan_amount, salary * 18))),
            "suggested_banks": ["HDFC Bank", "ICICI Bank", "SBI"],
        }

        self.cache[cache_key] = result
        return result


loan_prediction_service = LoanPredictionService()