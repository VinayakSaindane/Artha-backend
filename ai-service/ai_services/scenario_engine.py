from __future__ import annotations

from datetime import datetime
from typing import Any


class ScenarioEngineService:
    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        current_income = max(float(payload.get("income") or payload.get("current_income") or 0.0), 1.0)
        expenses = max(float(payload.get("expenses") or 0.0), 0.0)
        emi = max(float(payload.get("emi") or payload.get("new_emi") or 0.0), 0.0)

        salary_change = float(payload.get("salary_change_percent") or 0.0) / 100.0
        investment_increase = max(float(payload.get("investment_increase") or 0.0), 0.0)
        job_loss_months = max(int(payload.get("job_loss_months") or 0), 0)
        marriage_cost = max(float(payload.get("marriage_cost") or 0.0), 0.0)
        child_education_monthly = max(float(payload.get("child_education_monthly") or 0.0), 0.0)

        projection = []
        net_worth = max(float(payload.get("current_net_worth") or 0.0), 0.0)
        retirement_corpus = max(float(payload.get("current_retirement_corpus") or 0.0), 0.0)

        base_year = datetime.now().year
        for i in range(1, 6):
            year_income = current_income * (12.0 if i > job_loss_months / 12.0 else 8.0)
            year_income *= (1.0 + salary_change) ** i

            year_expenses = expenses * 12.0 * (1.06 ** i)
            year_emi = emi * 12.0
            life_event_drag = marriage_cost if i == 1 else 0.0
            child_edu = child_education_monthly * 12.0 * (1.04 ** i)

            annual_surplus = year_income - year_emi - year_expenses - life_event_drag - child_edu
            net_worth = max(0.0, net_worth + annual_surplus + investment_increase * 12.0)
            retirement_corpus = max(0.0, retirement_corpus * 1.09 + max(0.0, annual_surplus * 0.35))

            foir = round((year_emi / max(year_income, 1.0)) * 100.0, 2)

            projection.append({
                "year": base_year + i,
                "income": round(year_income, 2),
                "emi": round(year_emi, 2),
                "expenses": round(year_expenses + child_edu, 2),
                "surplus": round(annual_surplus, 2),
                "net_worth": round(net_worth, 2),
                "retirement_corpus": round(retirement_corpus, 2),
                "foir": foir,
            })

        return {
            "scenario_name": payload.get("scenario_name") or "Custom What-If",
            "horizon_years": 5,
            "projection": projection,
            "net_worth_growth": round(projection[-1]["net_worth"] - projection[0]["net_worth"], 2),
            "retirement_corpus_projection": round(projection[-1]["retirement_corpus"], 2),
            "foir_trend": [point["foir"] for point in projection],
            "chart_data": projection,
        }


scenario_engine_service = ScenarioEngineService()
