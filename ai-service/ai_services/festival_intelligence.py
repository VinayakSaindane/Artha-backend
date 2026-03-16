from __future__ import annotations

from datetime import datetime
from typing import Any

from app.database import get_db


SEASONAL_MULTIPLIERS = {
    "diwali": 1.35,
    "wedding season": 1.5,
    "holi": 1.2,
    "eid": 1.22,
    "school admissions": 1.4,
}


class FestivalIntelligenceService:
    async def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        user_id = payload.get("user_id")
        festival_name = str(payload.get("festival_name") or payload.get("season") or "Diwali")
        key = festival_name.lower().strip()

        income = max(float(payload.get("income") or 0.0), 1.0)
        monthly_expenses = max(float(payload.get("monthly_expenses") or payload.get("expenses") or 0.0), 1.0)

        db = get_db()
        historical_spend = 0.0
        sample_size = 0

        if user_id:
            now = datetime.utcnow()
            month_window = [max(1, now.month - 1), now.month, min(12, now.month + 1)]
            cursor = db["expenses"].find({"user_id": user_id})
            async for expense in cursor:
                expense_date = expense.get("date")
                if expense_date and getattr(expense_date, "month", None) in month_window:
                    historical_spend += float(expense.get("amount") or 0.0)
                    sample_size += 1

        average_event_spend = (historical_spend / sample_size) if sample_size else monthly_expenses * 0.28
        multiplier = SEASONAL_MULTIPLIERS.get(key, 1.18)

        projected_spike = average_event_spend * multiplier
        festival_spike_probability = int(min(95, max(10, round((projected_spike / monthly_expenses) * 100.0))))
        recommended_savings_target = round(projected_spike * 0.75, 2)

        return {
            "festival_name": festival_name,
            "festival_spike_probability": festival_spike_probability,
            "recommended_savings_target": recommended_savings_target,
            "risk_level": "High" if festival_spike_probability >= 70 else "Moderate" if festival_spike_probability >= 40 else "Low",
            "projected_spike_amount": round(projected_spike, 2),
            "advice": [
                "Start a festival sinking fund 90 days in advance",
                "Cap celebratory spend to 30% of monthly surplus",
                "Use UPI reminders for category-level controls",
            ],
        }


festival_intelligence_service = FestivalIntelligenceService()
