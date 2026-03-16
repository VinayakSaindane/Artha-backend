from __future__ import annotations

from typing import Any


class FinancialSimulatorService:
    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        decision = str(payload.get("decision") or "Buy Car")
        car_price = max(float(payload.get("car_price") or 0.0), 0.0)
        loan_emi = max(float(payload.get("loan_emi") or 0.0), 0.0)
        current_income = max(float(payload.get("current_income") or payload.get("income") or 0.0), 1.0)
        expenses = max(float(payload.get("expenses") or 0.0), 0.0)
        existing_emi = max(float(payload.get("existing_emi") or 0.0), 0.0)
        savings = max(float(payload.get("savings") or max(current_income - expenses, 0.0)), 0.0)

        total_emi = existing_emi + loan_emi
        debt_ratio_after_purchase = round((total_emi / current_income) * 100.0, 2)

        savings_after = max(0.0, savings - (loan_emi * 3.0) - (car_price * 0.05))
        savings_reduction_pct = round(((savings - savings_after) / max(savings, 1.0)) * 100.0, 2)

        if debt_ratio_after_purchase >= 45:
            risk_level = "High"
        elif debt_ratio_after_purchase >= 30:
            risk_level = "Moderate"
        else:
            risk_level = "Low"

        return {
            "decision": decision,
            "debt_ratio_after_purchase": debt_ratio_after_purchase,
            "savings_reduction_percent": savings_reduction_pct,
            "future_risk_level": risk_level,
            "risk_level": risk_level,
            "impact_summary": "This purchase may push your EMI ratio close to the danger zone." if risk_level != "Low" else "This purchase appears manageable with current cashflow.",
            "advice": [
                "Keep FOIR below 40% before taking new auto loan",
                "Preserve at least 6 months emergency fund after down payment",
                "Prefer shorter tenure only if monthly surplus remains positive",
            ],
        }


financial_simulator_service = FinancialSimulatorService()
