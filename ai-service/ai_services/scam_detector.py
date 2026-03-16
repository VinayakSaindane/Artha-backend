from __future__ import annotations

from typing import Any

from app.database import get_db


KNOWN_RBI_REGISTERED_APPS = {
    "hdfc bank loans",
    "icici personal loan",
    "sbi yono loan",
    "bajaj finserv",
    "tata capital",
}


class ScamDetectorService:
    async def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        app_name = str(payload.get("loan_app_name") or "Unknown App").strip()
        app_name_normalized = app_name.lower()
        interest_rate = float(payload.get("interest_rate") or 0.0)

        db = get_db()
        complaint_count = await db["loan_app_reports"].count_documents({
            "app_name": {"$regex": f"^{app_name}$", "$options": "i"}
        })

        regulatory_risk = 0.0 if app_name_normalized in KNOWN_RBI_REGISTERED_APPS else 100.0
        interest_rate_risk = min(100.0, max(0.0, ((interest_rate - 24.0) / 36.0) * 100.0))
        complaint_rate = min(100.0, complaint_count * 7.5)

        details = str(payload.get("loan_offer_details") or "").lower()
        suspicious_terms = ["contacts permission", "gallery", "instant disbursal fee", "advance processing", "harassment"]
        permission_hits = sum(1 for term in suspicious_terms if term in details)
        permission_risk = min(100.0, permission_hits * 30.0)

        fraud_score = int(round(
            0.35 * regulatory_risk + 0.30 * interest_rate_risk + 0.20 * complaint_rate + 0.15 * permission_risk
        ))
        fraud_score = max(0, min(100, fraud_score))

        reasons = []
        if regulatory_risk >= 80:
            reasons.append("Not found in RBI registered lender list")
        if interest_rate_risk >= 50:
            reasons.append("Interest rate appears above common legality thresholds")
        if complaint_rate >= 40:
            reasons.append("High user complaint volume observed")
        if permission_risk >= 30:
            reasons.append("Offer asks for invasive permissions or suspicious fees")
        if not reasons:
            reasons.append("No major red flags detected in current scan")

        return {
            "app_name": app_name,
            "fraud_score": fraud_score,
            "risk_level": "High" if fraud_score >= 70 else "Moderate" if fraud_score >= 40 else "Low",
            "reasons": reasons,
            "recommendation": "Avoid using this lending application" if fraud_score >= 70 else "Proceed only after verifying RBI registration and terms",
            "signals": {
                "regulatory_risk": round(regulatory_risk, 2),
                "interest_rate_risk": round(interest_rate_risk, 2),
                "complaint_rate": round(complaint_rate, 2),
                "permission_risk": round(permission_risk, 2),
            },
        }


scam_detector_service = ScamDetectorService()
