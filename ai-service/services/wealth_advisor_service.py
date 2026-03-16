from __future__ import annotations

from typing import Any

from cachetools import TTLCache

from app.config import get_settings


RISK_TO_RETURN = {
    "conservative": 0.08,
    "moderate": 0.11,
    "aggressive": 0.14,
}

RISK_TO_ALLOCATION = {
    "conservative": {"equity": 25, "debt": 55, "gold": 10, "emergency_fund": 10},
    "moderate": {"equity": 55, "debt": 30, "gold": 10, "emergency_fund": 5},
    "aggressive": {"equity": 80, "debt": 10, "gold": 5, "emergency_fund": 5},
}


class WealthAdvisorService:
    def __init__(self) -> None:
        settings = get_settings()
        self.cache = TTLCache(maxsize=1024, ttl=settings.cache_ttl_seconds)

    def recommend(self, payload: dict[str, Any]) -> dict[str, Any]:
        cache_key = str(hash(str(sorted(payload.items()))))
        if cache_key in self.cache:
            return self.cache[cache_key]

        age = int(payload.get("age", 30))
        income = float(payload.get("income", 60000))
        expenses = float(payload.get("expenses", 35000))
        savings = float(payload.get("savings", 0))
        risk = str(payload.get("risk_appetite", "moderate")).lower()
        retirement_age = int(payload.get("retirement_age", 55))

        annual_return = RISK_TO_RETURN.get(risk, 0.11)
        allocation = RISK_TO_ALLOCATION.get(risk, RISK_TO_ALLOCATION["moderate"])

        investable_monthly = max(income - expenses, income * 0.2)
        years_left = max(retirement_age - age, 1)

        corpus = savings
        projections = []
        for i in range(1, years_left + 1):
            corpus = corpus * (1 + annual_return) + investable_monthly * 12
            if i == 1 or i == years_left or i % 5 == 0:
                projections.append(
                    {
                        "age": age + i,
                        "corpus": int(round(corpus)),
                        "inflation_adjusted_value": int(round(corpus / ((1.06) ** i))),
                    }
                )

        target_corpus = int(round(income * 12 * 25 * ((1.06) ** years_left)))
        monthly_sip_required = int(round(max(0.0, (target_corpus - corpus) / max(years_left * 12, 1))))

        five_year_roadmap = []
        roadmap_corpus = savings
        for y in range(1, 6):
            roadmap_corpus = roadmap_corpus * (1 + annual_return) + investable_monthly * 12
            five_year_roadmap.append(
                {
                    "year": y,
                    "goal": [
                        "Build emergency buffer",
                        "Boost SIP by inflation",
                        "Rebalance equity-debt split",
                        "Review insurance cover",
                        "Consolidate high-interest debt",
                    ][y - 1],
                    "projected_corpus": int(round(roadmap_corpus)),
                }
            )

        result = {
            "recommended_asset_allocation": allocation,
            "five_year_roadmap": five_year_roadmap,
            # Compatibility fields for existing frontend.
            "health_score": max(45, min(95, int(round((investable_monthly / max(income, 1)) * 100 + 50)))),
            "summary": {
                "savings_rate": round(max(0.0, (income - expenses) / max(income, 1.0)), 2),
                "emergency_fund_status": "Adequate" if savings >= expenses * 6 else "Needs Improvement",
                "emergency_fund_months": int(round(savings / max(expenses, 1))),
                "debt_to_income": round(float(payload.get("debt_to_income", 0.15)), 2),
            },
            "retirement": {
                "projected_corpus": int(round(corpus)),
                "needed_corpus": target_corpus,
                "shortfall": max(0, target_corpus - int(round(corpus))),
                "monthly_sip_required": monthly_sip_required,
            },
            "asset_allocation": {
                "equity": allocation["equity"],
                "debt": allocation["debt"],
                "gold": allocation["gold"],
            },
            "projections": projections,
            "action_steps": [
                {"title": "Automate monthly investing", "impact": "HIGH", "description": "Set SIP auto-debit to lock in discipline and rupee-cost averaging."},
                {"title": "Rebalance every 6 months", "impact": "MED", "description": "Keep portfolio aligned with target allocation and risk profile."},
            ],
            "risk_analysis": "Portfolio path balances inflation risk and cash-flow resilience under Indian middle-class income volatility.",
        }

        self.cache[cache_key] = result
        return result


wealth_advisor_service = WealthAdvisorService()