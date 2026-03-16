from __future__ import annotations

from typing import Any

from cachetools import TTLCache

from app.config import get_settings
from models.debt_risk_model import DebtRiskModel
from utils.financial_features import compute_debt_metrics


class DebtPulseService:
    def __init__(self) -> None:
        settings = get_settings()
        self.cache = TTLCache(maxsize=2048, ttl=settings.cache_ttl_seconds)
        self.model = DebtRiskModel.build()

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        cache_key = str(hash(str(sorted(payload.items()))))
        if cache_key in self.cache:
            return self.cache[cache_key]

        metrics = compute_debt_metrics(
            monthly_income=payload.get("monthly_income") or payload.get("income") or 50000,
            total_emi=payload.get("total_emi") or payload.get("total_emis") or 0,
            credit_used=payload.get("credit_used") or payload.get("credit_card_spend") or 0,
            credit_limit=payload.get("credit_limit") or 100000,
            outstanding_loans=payload.get("outstanding_loans") or payload.get("loan_outstanding") or 0,
        )

        emi_ratio = round(metrics.emi_to_income_ratio, 2)
        cc_utilization = round(metrics.cc_utilization, 2)
        loan_burden = round(metrics.loan_burden_ratio, 2)

        score = 100 - (emi_ratio * 0.9 + cc_utilization * 0.35 + loan_burden * 0.2)
        debt_health_score = int(max(0, min(100, round(score))))

        if emi_ratio >= 50:
            risk_level = "DANGER"
        elif emi_ratio >= 30:
            risk_level = "WARNING"
        else:
            risk_level = "SAFE"

        days_until_danger = self.model.predict_days_until_danger(emi_ratio, cc_utilization, loan_burden)
        if risk_level == "SAFE":
            days_until_danger = None

        monthly_income = max(float(payload.get("monthly_income") or payload.get("income") or 50000), 1.0)
        monthly_expenses = max(float(payload.get("monthly_expenses") or 0), 0.0)
        savings_rate = round(max(0.0, ((monthly_income - monthly_expenses) / monthly_income) * 100.0), 2)

        recommended_actions = [
            "Cap EMI obligations below 30% of monthly income.",
            "Pay down high-interest revolving credit before new borrowing.",
            "Move variable-rate debt to fixed-rate instruments when feasible.",
        ]

        result = {
            "debt_health_score": debt_health_score,
            "days_until_danger": days_until_danger,
            "risk_level": risk_level,
            "recommended_actions": recommended_actions,
            # Compatibility fields for existing frontend.
            "health_score": debt_health_score,
            "status": risk_level,
            "debt_trap_days": days_until_danger,
            "emi_to_income_ratio": emi_ratio,
            "savings_rate": savings_rate,
            "trend": payload.get("trend") or "STABLE",
            "scenario_if_no_action": "Debt servicing pressure can increase sharply if utilization continues to rise.",
            "prescription": [
                {"action": "Reduce non-essential monthly spend by 10%", "priority": "HIGH", "monthly_saving": 3000},
                {"action": "Prepay highest-interest loan tranche", "priority": "HIGH", "monthly_saving": 2500},
                {"action": "Set auto-debit for credit card full payment", "priority": "MED", "monthly_saving": 1500},
            ],
        }

        self.cache[cache_key] = result
        return result


debt_pulse_service = DebtPulseService()