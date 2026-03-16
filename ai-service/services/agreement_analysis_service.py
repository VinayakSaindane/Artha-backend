from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from cachetools import TTLCache

from app.config import get_settings
from models.agreement_risk_model import AgreementRiskModel

try:
    import spacy
except Exception:  # pragma: no cover
    spacy = None


class AgreementAnalysisService:
    def __init__(self) -> None:
        settings = get_settings()
        self.cache = TTLCache(maxsize=2048, ttl=settings.cache_ttl_seconds)
        self.model = AgreementRiskModel.build()
        self.nlp = None
        if spacy is not None:
            try:
                self.nlp = spacy.blank("en")
            except Exception:
                self.nlp = None

        self.rule_patterns = [
            (r"\b(interest\s+rate\s+\d{2,}|\d{2,}\s*%\s*(per\s*annum|p\.a\.|monthly))\b", "Predatory interest rate", "HIGH"),
            (r"\b(penalty|late\s+fee|default\s+charge|compound\s+interest)\b", "Hidden penalty clause", "MEDIUM"),
            (r"\b(variable\s+rate|floating\s+rate|bank\s+discretion|without\s+notice)\b", "Variable interest trap", "HIGH"),
            (r"\b(arbitration|waive\s+rights|indemnify|non-refundable|irrevocable)\b", "Legal risk phrase", "MEDIUM"),
        ]

    def _cache_key(self, text: str) -> str:
        return str(hash(text.lower().strip()))

    def analyze(self, text: str) -> dict[str, Any]:
        key = self._cache_key(text)
        if key in self.cache:
            return self.cache[key]

        text_lower = text.lower()
        flags: list[dict[str, str]] = []
        danger_clauses: list[str] = []
        score = 0.0

        for pattern, issue, severity in self.rule_patterns:
            for match in re.finditer(pattern, text_lower):
                clause = text[max(0, match.start() - 50): min(len(text), match.end() + 120)].strip()
                flags.append(
                    {
                        "issue": issue,
                        "clause_text": clause[:220],
                        "severity": severity,
                        "regulation_violated": "Potential consumer protection concern",
                        "suggested_fix": "Ask lender for rewritten clause with fixed limits and transparent penalties.",
                    }
                )
                danger_clauses.append(clause[:220])
                score += 22 if severity == "HIGH" else 12

        ml_probability = self.model.predict_risk_probability(text_lower)
        score += ml_probability * 45

        # Basic linguistic complexity bump for dense legal text.
        words = max(1, len(text_lower.split()))
        long_words = len([w for w in text_lower.split() if len(w) >= 10])
        complexity_ratio = long_words / words
        score += min(10.0, complexity_ratio * 100)

        risk_score = int(min(100, round(score)))
        if risk_score >= 67:
            risk_level = "HIGH"
        elif risk_score >= 34:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        recommended_actions = [
            "Request a plain-language schedule of all fees and penalties.",
            "Negotiate fixed-rate or capped-rate terms before signing.",
            "Seek review by a legal advisor if arbitration/waiver clauses are present.",
        ]

        missing_clauses = []
        for clause in ["grievance redressal", "cooling-off", "foreclosure charges"]:
            if clause not in text_lower:
                missing_clauses.append(f"Missing clarity on {clause}")

        result = {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "summary": f"Automated scan completed on {datetime.utcnow().date().isoformat()}. {len(flags)} risk indicators found.",
            "danger_clauses": danger_clauses[:8],
            "recommended_actions": recommended_actions,
            "flags": flags[:12],
            "missing_clauses": missing_clauses[:5],
        }

        self.cache[key] = result
        return result


agreement_analysis_service = AgreementAnalysisService()