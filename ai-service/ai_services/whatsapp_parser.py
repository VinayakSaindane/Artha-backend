from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from app.database import get_db

CATEGORY_KEYWORDS = {
    "food": "Food",
    "groceries": "Essentials",
    "uber": "Transport",
    "ola": "Transport",
    "fuel": "Transport",
    "rent": "Housing",
    "emi": "EMI",
    "medicine": "Health",
    "hospital": "Health",
}


class WhatsappParserService:
    amount_pattern = re.compile(r"(?:spent|paid|rs|inr|₹)?\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)

    def _extract_category(self, message: str) -> str:
        lower = message.lower()
        for keyword, category in CATEGORY_KEYWORDS.items():
            if keyword in lower:
                return category
        return "Other"

    def _extract_merchant(self, message: str) -> str | None:
        merchant_match = re.search(r"(?:at|to)\s+([a-zA-Z][\w\s&.-]{1,40})", message, re.IGNORECASE)
        return merchant_match.group(1).strip() if merchant_match else None

    async def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        message = str(payload.get("message") or "").strip()
        user_id = payload.get("user_id")

        amount_match = self.amount_pattern.search(message)
        amount = float(amount_match.group(1)) if amount_match else 0.0
        category = self._extract_category(message)
        merchant = self._extract_merchant(message)

        if amount <= 0:
            return {
                "status": "failed",
                "message": "Could not parse amount from message",
                "parsed": {"amount": None, "category": category, "merchant": merchant},
            }

        month_total = amount
        if user_id:
            db = get_db()
            expense_doc = {
                "user_id": user_id,
                "amount": amount,
                "category": category,
                "description": f"WhatsApp log: {merchant or 'manual entry'}",
                "date": datetime.utcnow(),
            }
            await db["expenses"].insert_one(expense_doc)

            start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            cursor = db["expenses"].find({"user_id": user_id, "date": {"$gte": start_of_month}, "category": category})
            month_total = 0.0
            async for row in cursor:
                month_total += float(row.get("amount") or 0.0)

        budget_cap = max(float(payload.get("category_budget") or 2500.0), 1.0)
        budget_used_pct = int(min(100, round((month_total / budget_cap) * 100.0)))

        return {
            "status": "logged",
            "amount": amount,
            "category": category,
            "merchant": merchant,
            "budget_used_percent": budget_used_pct,
            "reply": f"Logged ₹{int(amount)} under {category}. Your {category} budget is now {budget_used_pct}% used.",
        }


whatsapp_parser_service = WhatsappParserService()
