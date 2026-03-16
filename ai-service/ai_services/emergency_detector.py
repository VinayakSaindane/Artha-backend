from __future__ import annotations

from typing import Any


class EmergencyDetectorService:
    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        savings = max(float(payload.get("savings") or payload.get("liquid_savings") or 0.0), 0.0)
        monthly_expenses = max(float(payload.get("monthly_expenses") or payload.get("expenses") or 0.0), 1.0)
        income = max(float(payload.get("income") or 0.0), 0.0)

        trigger_weights = {
            "job_loss": 1.0,
            "medical_emergency": 0.8,
            "family_crisis": 0.65,
            "salary_delay": 0.45,
        }

        trigger = str(payload.get("trigger") or "salary_delay")
        trigger_weight = trigger_weights.get(trigger, 0.5)

        burn_rate = monthly_expenses * (1.0 + trigger_weight * 0.25)
        survival_months = round(savings / max(burn_rate, 1.0), 2)

        if survival_months < 2:
            status = "Warning"
        elif survival_months < 4:
            status = "Caution"
        else:
            status = "Stable"

        recommended_fund = monthly_expenses * 6.0
        action_plan = [
            "Pause discretionary spending",
            "Cancel low-value subscriptions",
            "Create emergency buffer auto-transfer",
        ]
        if income <= 0:
            action_plan.append("Prioritize short-term liquidity and essential obligations")

        return {
            "emergency_status": status,
            "survival_months": survival_months,
            "recommended_emergency_fund": f"₹{recommended_fund / 100000:.1f}L",
            "action_plan": action_plan,
            "trigger": trigger,
        }


emergency_detector_service = EmergencyDetectorService()
