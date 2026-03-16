from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.database import get_db


class HabitScoreService:
    async def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        user_id = payload.get("user_id")
        if not user_id:
            return {
                "score": 0,
                "range": "0-850",
                "streak_days": 0,
                "badges": [],
                "milestones": ["Add a user_id to compute personalized habit score"],
            }

        db = get_db()
        now = datetime.utcnow()
        since = now - timedelta(days=90)

        income_total = 0.0
        expense_total = 0.0
        emi_total = 0.0
        overspend_days = 0

        income_cursor = db["incomes"].find({"user_id": user_id, "date": {"$gte": since}})
        async for item in income_cursor:
            income_total += float(item.get("amount") or 0.0)

        expense_cursor = db["expenses"].find({"user_id": user_id, "date": {"$gte": since}})
        daily_buckets: dict[str, float] = {}
        async for item in expense_cursor:
            amount = float(item.get("amount") or 0.0)
            expense_total += amount
            if str(item.get("category") or "") == "EMI":
                emi_total += amount
            day_key = (item.get("date") or now).strftime("%Y-%m-%d")
            daily_buckets[day_key] = daily_buckets.get(day_key, 0.0) + amount

        daily_budget = max((income_total / 90.0) * 0.65, 1.0)
        for day_spend in daily_buckets.values():
            if day_spend > daily_budget:
                overspend_days += 1

        savings_rate = max(0.0, (income_total - expense_total) / max(income_total, 1.0))
        budget_compliance = max(0.0, 1.0 - (overspend_days / 90.0))
        debt_reduction = max(0.0, 1.0 - (emi_total / max(income_total, 1.0)))
        no_overspend_streak = max(0, 14 - overspend_days)

        raw = (
            0.35 * savings_rate
            + 0.25 * budget_compliance
            + 0.20 * min(1.0, no_overspend_streak / 14.0)
            + 0.20 * debt_reduction
        )
        score = int(min(850, max(0, round(raw * 850.0))))

        badges = []
        if debt_reduction > 0.75:
            badges.append("EMI Slayer")
        if budget_compliance > 0.8:
            badges.append("Shield User")
        if savings_rate > 0.2:
            badges.append("Bharat Saver")

        milestones = []
        if score >= 700:
            milestones.append("Financial discipline elite zone")
        if no_overspend_streak >= 10:
            milestones.append("10+ day no-overspend streak")
        if savings_rate >= 0.25:
            milestones.append("Savings champion: 25%+ allocation")

        return {
            "score": score,
            "range": "0-850",
            "streak_days": no_overspend_streak,
            "badges": badges,
            "milestones": milestones,
            "components": {
                "savings_rate": round(savings_rate, 3),
                "budget_compliance": round(budget_compliance, 3),
                "debt_reduction": round(debt_reduction, 3),
                "overspend_days": overspend_days,
            },
        }


habit_score_service = HabitScoreService()
