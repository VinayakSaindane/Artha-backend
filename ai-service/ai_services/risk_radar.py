from __future__ import annotations

from typing import Any


class RiskRadarService:
    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        income = max(float(payload.get("income") or 0.0), 1.0)
        expenses = max(float(payload.get("expenses") or 0.0), 0.0)
        savings = max(float(payload.get("savings") or max(income - expenses, 0.0)), 0.0)
        existing_loans = max(float(payload.get("existing_loans") or payload.get("loan_outstanding") or 0.0), 0.0)
        expense_trend = payload.get("monthly_expense_trend") or payload.get("expense_trend") or []

        debt_ratio = min(100.0, (existing_loans / (income * 12.0)) * 100.0)

        if isinstance(expense_trend, list) and len(expense_trend) >= 2:
            start = max(float(expense_trend[0]), 1.0)
            end = max(float(expense_trend[-1]), 0.0)
            expense_growth_rate = max(0.0, ((end - start) / start) * 100.0)
        else:
            expense_growth_rate = max(0.0, ((expenses - (savings + 1.0)) / max(savings + 1.0, 1.0)) * 8.0)

        savings_rate = (savings / income) * 100.0
        low_savings_rate = max(0.0, 30.0 - savings_rate) * (100.0 / 30.0)

        if isinstance(expense_trend, list) and len(expense_trend) >= 3:
            mean = sum(float(x) for x in expense_trend) / len(expense_trend)
            variance = sum((float(x) - mean) ** 2 for x in expense_trend) / len(expense_trend)
            income_volatility = min(100.0, (variance ** 0.5 / max(mean, 1.0)) * 100.0)
        else:
            income_volatility = min(100.0, abs(expenses - income * 0.65) / max(income, 1.0) * 100.0)

        weighted_risk = (
            0.4 * min(100.0, debt_ratio)
            + 0.3 * min(100.0, expense_growth_rate)
            + 0.2 * min(100.0, low_savings_rate)
            + 0.1 * min(100.0, income_volatility)
        )

        risk_score = int(max(0, min(100, round(weighted_risk))))
        risk_level = "Low" if risk_score < 40 else "Moderate" if risk_score < 70 else "High"

        emergency_fund_coverage = round(savings / max(expenses, 1.0), 1)
        retirement_gap_value = max(0.0, (income * 12.0 * 20.0) - (savings * 10.0))

        recommendations = []
        if emergency_fund_coverage < 3:
            recommendations.append("Increase emergency savings to 6 months of expenses")
        if debt_ratio > 35:
            recommendations.append("Reduce EMI burden below 35% of annual income")
        if savings_rate < 20:
            recommendations.append("Increase retirement investments and SIP allocation")
        if not recommendations:
            recommendations.append("Maintain current discipline and rebalance quarterly")

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "debt_trap_risk": "High" if debt_ratio > 45 else "Medium" if debt_ratio > 30 else "Low",
            "emergency_fund_coverage_months": emergency_fund_coverage,
            "retirement_gap": f"₹{retirement_gap_value / 100000:.1f}L",
            "credit_dependence": "High" if expenses > income * 0.9 else "Medium" if expenses > income * 0.75 else "Low",
            "drivers": {
                "debt_ratio": round(debt_ratio, 2),
                "expense_growth_rate": round(expense_growth_rate, 2),
                "low_savings_rate": round(low_savings_rate, 2),
                "income_volatility": round(income_volatility, 2),
            },
            "recommendations": recommendations,
        }


risk_radar_service = RiskRadarService()
