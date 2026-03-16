from __future__ import annotations

from datetime import date, datetime
from math import exp
from typing import Any

from cachetools import TTLCache

from app.config import get_settings
from app.database import get_db
from models.festival_spike_model import FestivalSpikeModel


FESTIVAL_WEIGHTS = {
    "diwali": 0.98,
    "wedding": 1.0,
    "holi": 0.72,
    "eid": 0.68,
    "school": 0.83,
    "admission": 0.83,
}


class FestivalSpendingService:
    def __init__(self) -> None:
        settings = get_settings()
        self.cache = TTLCache(maxsize=1024, ttl=settings.cache_ttl_seconds)
        self.model = FestivalSpikeModel.build()

    def _weight(self, festival_name: str) -> float:
        name = festival_name.lower()
        for key, value in FESTIVAL_WEIGHTS.items():
            if key in name:
                return value
        return 0.58

    async def _average_monthly_spend(self, user_id: str | None) -> float:
        if not user_id:
            return 25000.0
        db = get_db()
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": {"$month": "$date"}, "total": {"$sum": "$amount"}}},
        ]
        docs = await db["expenses"].aggregate(pipeline).to_list(length=24)
        if not docs:
            return 25000.0
        return float(sum(doc.get("total", 0.0) for doc in docs) / max(len(docs), 1))

    async def predict(self, user_id: str | None, festival_name: str, festival_date: str, income: float | None) -> dict[str, Any]:
        cache_key = f"{user_id}:{festival_name}:{festival_date}:{income}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        base_spend = await self._average_monthly_spend(user_id)
        event_date = datetime.fromisoformat(festival_date).date()
        days_to_event = max((event_date - date.today()).days, 1)
        weight = self._weight(festival_name)

        expected_total_expense = self.model.predict_expected_spike(base_spend, weight, days_to_event)
        expected_total_expense = round(expected_total_expense, 2)

        effective_income = max(float(income or 50000), 1.0)
        ratio = expected_total_expense / effective_income
        festival_spike_probability = round(1.0 / (1.0 + exp(-3.0 * (ratio - 0.6))), 4)
        recommended_daily_savings = round(expected_total_expense / days_to_event, 2)

        if festival_spike_probability > 0.8:
            pattern = "High Cultural Spike"
        elif festival_spike_probability > 0.5:
            pattern = "Moderate Cultural Spike"
        else:
            pattern = "Controlled Spike"

        result = {
            "festival_spike_probability": festival_spike_probability,
            "recommended_daily_savings": recommended_daily_savings,
            "expected_total_expense": expected_total_expense,
            # Compatibility fields for existing frontend.
            "detected_spike_pattern": pattern,
            "estimated_extra_spending": expected_total_expense,
            "savings_plan": {
                "daily_target": int(round(recommended_daily_savings)),
                "days_remaining": days_to_event,
                "total_target": int(round(expected_total_expense)),
            },
            "actionable_tips": [
                "Create a festive envelope budget and freeze discretionary app spends.",
                "Book big-ticket purchases at least 3 weeks early to avoid premium pricing.",
                "Use UPI cashback windows for planned essentials only.",
            ],
            "debt_warning": "Early savings reduce the probability of revolving card debt after festivals.",
        }

        self.cache[cache_key] = result
        return result


festival_spending_service = FestivalSpendingService()