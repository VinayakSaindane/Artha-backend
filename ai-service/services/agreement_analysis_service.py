from __future__ import annotations

import json
import re
from datetime import datetime
from difflib import SequenceMatcher
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

        self.document_keywords = [
            "loan agreement",
            "terms and conditions",
            "interest rate",
            "borrower",
            "lender",
            "emi",
            "repayment",
        ]
        self.risk_weights = {
            "High Interest Rate": 25,
            "Penalty Clause": 20,
            "Variable Interest Clause": 20,
            "Hidden Fees": 10,
            "Foreclosure Charges": 10,
        }
        self.protection_checks = [
            (r"\b(grievance|complaint)\s+(redressal|resolution|officer)\b", "Grievance redressal clause missing"),
            (r"\b(cooling[-\s]?off|cancellation\s+period|free\s+look\s+period)\b", "Cooling-off period missing"),
            (r"\b(foreclosure|prepayment|pre-payment)\s+(charges?|fee|penalty)\b", "Foreclosure charge disclosure missing"),
        ]
        self.heading_pattern = re.compile(
            r"^(Clause\s+[\w.-]+.*|Section\s+[\w.-]+.*|\d+[.)]\s+.*|[•\-*]\s+.*)$",
            re.IGNORECASE,
        )
        self.percentage_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*%")
        self.variable_interest_pattern = re.compile(
            r"\b(variable|floating)\s+interest\b|\binterest\s+rate\b.{0,80}\b(may|can|shall)\s+(change|revise|modify|reset)\b|\b(lender|bank)\b.{0,60}\b(sole\s+discretion|without\s+prior\s+notice)\b",
            re.IGNORECASE,
        )
        self.penalty_pattern = re.compile(
            r"\b(penalty|late\s+fee|default\s+charge|overdue\s+interest|bounce\s+charge|penal\s+interest|compound\s+interest)\b",
            re.IGNORECASE,
        )
        self.hidden_fees_pattern = re.compile(
            r"\b(processing|administrative|documentation|service|convenience|other)\s+fees?\b|\bcharges?\s+as\s+applicable\b|\bany\s+other\s+charges\b",
            re.IGNORECASE,
        )
        self.foreclosure_pattern = re.compile(
            r"\b(foreclosure|prepayment|pre-payment|early\s+closure)\b",
            re.IGNORECASE,
        )
        self.ambiguity_pattern = re.compile(
            r"\b(sole\s+discretion|as\s+deemed\s+fit|from\s+time\s+to\s+time|without\s+prior\s+notice|at\s+any\s+time|as\s+applicable)\b",
            re.IGNORECASE,
        )

    def _cache_key(self, text: str, user_context: dict[str, Any] | None) -> str:
        safe_context = json.dumps(user_context or {}, sort_keys=True, default=str)
        return str(hash(f"{text.lower().strip()}::{safe_context}"))

    def _normalize_text(self, text: str) -> str:
        lowered = text.lower()
        lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
        return re.sub(r"\s+", " ", lowered).strip()

    def _is_financial_agreement(self, text: str) -> tuple[bool, list[str]]:
        text_lower = text.lower()
        matches = [keyword for keyword in self.document_keywords if keyword in text_lower]
        is_agreement = len(matches) >= 2 and any(keyword in matches for keyword in ["loan agreement", "borrower", "lender", "repayment", "interest rate"])
        return is_agreement, matches

    def _extract_clauses(self, text: str) -> list[dict[str, str]]:
        clauses: list[dict[str, str]] = []
        current_title = "Document Overview"
        current_lines: list[str] = []

        def flush_clause() -> None:
            nonlocal current_lines, current_title
            clause_text = " ".join(current_lines).strip()
            if clause_text:
                clauses.append({
                    "clause_title": current_title[:160],
                    "clause_text": clause_text[:1800],
                })
            current_lines = []

        for raw_line in text.splitlines():
            line = re.sub(r"\s+", " ", raw_line).strip()
            if not line:
                continue
            if self.heading_pattern.match(line):
                flush_clause()
                current_title = line.rstrip(":")
                bullet_text = re.sub(r"^[•\-*]\s+", "", line).strip()
                if re.match(r"^[•\-*]\s+", line):
                    current_lines = [bullet_text]
                    current_title = bullet_text[:160]
                continue
            current_lines.append(line)

        flush_clause()

        if clauses:
            return clauses

        paragraphs = [segment.strip() for segment in re.split(r"\n\s*\n", text) if segment.strip()]
        return [
            {
                "clause_title": f"Clause {index + 1}",
                "clause_text": paragraph[:1800],
            }
            for index, paragraph in enumerate(paragraphs[:20])
        ]

    def _deduplicate_clauses(self, clauses: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
        unique_clauses: list[dict[str, str]] = []
        normalized_texts: list[str] = []
        removed_count = 0

        for clause in clauses:
            normalized = self._normalize_text(clause["clause_text"])
            if len(normalized) < 20:
                removed_count += 1
                continue
            if normalized in normalized_texts:
                removed_count += 1
                continue
            if any(SequenceMatcher(None, normalized, existing).ratio() > 0.85 for existing in normalized_texts):
                removed_count += 1
                continue
            unique_clauses.append(clause)
            normalized_texts.append(normalized)

        return unique_clauses, removed_count

    def _severity_rank(self, severity: str) -> int:
        return {"LOW": 1, "MEDIUM": 2, "HIGH": 3}.get(severity, 1)

    def _percentage_contexts(self, text: str) -> list[tuple[float, str, bool]]:
        contexts: list[tuple[float, str, bool]] = []
        for match in self.percentage_pattern.finditer(text):
            percentage = float(match.group(1))
            context = text[max(0, match.start() - 45): min(len(text), match.end() + 45)]
            monthly = bool(re.search(r"per\s+month|monthly|p\.m\b", context, re.IGNORECASE))
            contexts.append((percentage, context.strip(), monthly))
        return contexts

    def _build_user_profile_context(self, user_context: dict[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
        user_context = user_context or {}
        monthly_income = float(user_context.get("monthly_income") or 0)
        existing_emis = float(user_context.get("existing_emis") or 0)
        cibil_score = int(user_context.get("cibil_score") or 0)
        emi_ratio = round((existing_emis / monthly_income) * 100, 1) if monthly_income > 0 else 0.0

        profile = {
            "monthly_income": int(monthly_income) if monthly_income else 0,
            "existing_emis": int(existing_emis) if existing_emis else 0,
            "emi_to_income_ratio": emi_ratio,
            "cibil_score": cibil_score,
            "occupation": str(user_context.get("occupation") or ""),
            "state": str(user_context.get("state") or ""),
            "age": int(user_context.get("age") or 0),
        }

        profile_notes: list[str] = []
        if emi_ratio >= 35:
            profile_notes.append(
                f"Your stored EMI load is already {emi_ratio}% of monthly income, so any additional costly borrowing materially increases repayment stress."
            )
        elif emi_ratio > 0:
            profile_notes.append(
                f"Your current EMI load is {emi_ratio}% of monthly income; keep total obligations close to or below 35% where possible."
            )

        if 0 < cibil_score < 700:
            profile_notes.append(
                "Your stored credit score suggests reduced pricing power, so fixed-rate and fee transparency should be negotiated before acceptance."
            )

        return profile, profile_notes

    def _build_detection(
        self,
        category: str,
        clause_title: str,
        clause_text: str,
        severity: str,
        risk_reason: str,
        suggested_fix: str,
    ) -> dict[str, str]:
        return {
            "category": category,
            "clause_title": clause_title,
            "clause": clause_text[:240],
            "severity": severity,
            "risk_reason": risk_reason,
            "suggested_fix": suggested_fix,
        }

    def _add_detection(self, detections: list[dict[str, str]], detection: dict[str, str]) -> None:
        candidate_text = self._normalize_text(f"{detection['category']} {detection['clause']}")
        for existing in detections:
            existing_text = self._normalize_text(f"{existing['category']} {existing['clause']}")
            if existing["category"] == detection["category"] and SequenceMatcher(None, candidate_text, existing_text).ratio() > 0.85:
                if self._severity_rank(detection["severity"]) > self._severity_rank(existing["severity"]):
                    existing.update(detection)
                return
        detections.append(detection)

    def _extract_relevant_clause_excerpt(self, text: str, keyword_pattern: str) -> str:
        match = re.search(keyword_pattern, text, re.IGNORECASE)
        if not match:
            return text[:240]
        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 140)
        return text[start:end].strip()

    def _detect_clause_risks(
        self,
        clause_title: str,
        clause_text: str,
        user_profile: dict[str, Any],
    ) -> list[dict[str, str]]:
        detections: list[dict[str, str]] = []
        clause_lower = clause_text.lower()
        safe_emi_limit = int((user_profile.get("monthly_income") or 0) * 0.35)
        emi_fix_suffix = (
            f" Keep total EMIs near or below Rs. {safe_emi_limit:,} based on your saved monthly income."
            if safe_emi_limit > 0
            else ""
        )

        if "interest" in clause_lower:
            for percentage, context, monthly in self._percentage_contexts(clause_text):
                annualized_rate = percentage * 12 if monthly else percentage
                if annualized_rate > 24:
                    rate_label = f"{percentage}% monthly" if monthly else f"{percentage}% annual"
                    risk_reason = (
                        f"{rate_label} is above common retail borrowing ranges and may indicate predatory pricing."
                    )
                    if monthly:
                        risk_reason += f" This is roughly {annualized_rate:.1f}% annualized before compounding."
                    self._add_detection(
                        detections,
                        self._build_detection(
                            "High Interest Rate",
                            clause_title,
                            context,
                            "HIGH",
                            risk_reason,
                            f"Negotiate a lower fixed interest rate with a clearly stated annual cap.{emi_fix_suffix}",
                        ),
                    )

        if self.penalty_pattern.search(clause_text):
            severe_penalty = False
            penalty_context = self._extract_relevant_clause_excerpt(
                clause_text,
                r"penalty|late\s+fee|default\s+charge|overdue\s+interest|bounce\s+charge|penal\s+interest|compound\s+interest",
            )
            penalty_reason = "Penalty wording can sharply increase the effective repayment burden after a missed due date."
            for percentage, _, monthly in self._percentage_contexts(clause_text):
                if monthly and percentage > 2:
                    severe_penalty = True
                    penalty_reason = f"Penalty of {percentage}% per month exceeds the 2% monthly threshold and can escalate quickly."
                    break
            if "compound interest" in clause_lower:
                severe_penalty = True
                penalty_reason = "Compound penal interest can rapidly magnify dues after even short delays."

            self._add_detection(
                detections,
                self._build_detection(
                    "Penalty Clause",
                    clause_title,
                    penalty_context,
                    "HIGH" if severe_penalty else "MEDIUM",
                    penalty_reason,
                    "Ask for a capped one-time late fee or a lower penal interest formula with no compounding.",
                ),
            )

        if self.variable_interest_pattern.search(clause_text):
            variable_context = self._extract_relevant_clause_excerpt(
                clause_text,
                r"variable|floating|interest\s+rate|sole\s+discretion|without\s+prior\s+notice",
            )
            self._add_detection(
                detections,
                self._build_detection(
                    "Variable Interest Clause",
                    clause_title,
                    variable_context,
                    "HIGH",
                    "The lender appears able to revise pricing unilaterally, making future instalments unpredictable.",
                    "Ask for a fixed rate or a transparent benchmark-linked reset formula with advance notice and a rate cap.",
                ),
            )

        if self.hidden_fees_pattern.search(clause_text):
            fee_context = self._extract_relevant_clause_excerpt(
                clause_text,
                r"processing|administrative|documentation|service|convenience|other\s+charges|charges\s+as\s+applicable",
            )
            fee_reason = "Fee wording is broad and may allow charges that are hard to verify before signing."
            severity = "MEDIUM"
            for percentage, _, _ in self._percentage_contexts(clause_text):
                if percentage > 3 and re.search(r"processing|administrative|documentation|service", clause_text, re.IGNORECASE):
                    severity = "HIGH"
                    fee_reason = f"Processing or service fees above 3% are expensive relative to standard retail lending practice."
                    break

            self._add_detection(
                detections,
                self._build_detection(
                    "Hidden Fees",
                    clause_title,
                    fee_context,
                    severity,
                    fee_reason,
                    "Request a full fee schedule with each charge quantified in rupees or capped as a percentage before disbursal.",
                ),
            )

        if self.foreclosure_pattern.search(clause_text):
            foreclosure_context = self._extract_relevant_clause_excerpt(
                clause_text,
                r"foreclosure|prepayment|pre-payment|early\s+closure",
            )
            foreclosure_reason = "Charges on early closure can trap the borrower in an expensive loan even when funds become available."
            severity = "MEDIUM"
            for percentage, _, _ in self._percentage_contexts(clause_text):
                if percentage > 3:
                    severity = "HIGH"
                    foreclosure_reason = f"Foreclosure or prepayment charges above 3% materially reduce the value of repaying early."
                    break
            if re.search(r"not\s+permitted|only\s+with\s+lender\s+consent", clause_text, re.IGNORECASE):
                severity = "HIGH"
                foreclosure_reason = "The clause restricts or conditions early closure, which can function as a foreclosure trap."

            self._add_detection(
                detections,
                self._build_detection(
                    "Foreclosure Charges",
                    clause_title,
                    foreclosure_context,
                    severity,
                    foreclosure_reason,
                    "Negotiate zero or low prepayment charges and require the right to part-prepay without lender discretion.",
                ),
            )

        if self.ambiguity_pattern.search(clause_text):
            ambiguity_context = self._extract_relevant_clause_excerpt(
                clause_text,
                r"sole\s+discretion|as\s+deemed\s+fit|from\s+time\s+to\s+time|without\s+prior\s+notice|at\s+any\s+time|as\s+applicable",
            )
            self._add_detection(
                detections,
                self._build_detection(
                    "Legal Ambiguity",
                    clause_title,
                    ambiguity_context,
                    "MEDIUM",
                    "Open-ended language makes borrower obligations harder to predict and dispute later.",
                    "Ask for precise triggers, notice periods, and numerical caps instead of discretionary wording.",
                ),
            )

        return detections

    def analyze(self, text: str, user_context: dict[str, Any] | None = None) -> dict[str, Any]:
        key = self._cache_key(text, user_context)
        if key in self.cache:
            return self.cache[key]

        text_lower = text.lower()
        is_agreement, matched_keywords = self._is_financial_agreement(text)
        if not is_agreement:
            result = {
                "document_type": "Not a financial agreement",
                "message": "Uploaded file does not appear to be a financial contract.",
            }
            self.cache[key] = result
            return result

        clauses = self._extract_clauses(text)
        deduplicated_clauses, duplicate_clauses_removed = self._deduplicate_clauses(clauses)
        user_profile, profile_notes = self._build_user_profile_context(user_context)
        detections: list[dict[str, str]] = []

        for clause in deduplicated_clauses:
            clause_detections = self._detect_clause_risks(
                clause_title=clause["clause_title"],
                clause_text=clause["clause_text"],
                user_profile=user_profile,
            )
            for detection in clause_detections:
                self._add_detection(detections, detection)

        ml_probability = self.model.predict_risk_probability(text_lower)
        score = 0.0
        for category in {detection["category"] for detection in detections}:
            score += self.risk_weights.get(category, 0)
        score += ml_probability * 15

        words = max(1, len(text.lower().split()))
        long_words = len([word for word in text.split() if len(word) >= 10])
        complexity_ratio = long_words / words
        score += min(5.0, complexity_ratio * 40)

        risk_score = int(min(100, round(score)))
        if risk_score >= 61:
            risk_level = "High Risk"
            risk_level_code = "HIGH"
        elif risk_score >= 31:
            risk_level = "Medium Risk"
            risk_level_code = "MEDIUM"
        else:
            risk_level = "Low Risk"
            risk_level_code = "LOW"

        missing_protections = [
            label for pattern, label in self.protection_checks if not re.search(pattern, text, re.IGNORECASE)
        ]

        recommended_actions = []
        for detection in detections[:6]:
            if detection["suggested_fix"] not in recommended_actions:
                recommended_actions.append(detection["suggested_fix"])
        for note in profile_notes:
            if note not in recommended_actions:
                recommended_actions.append(note)
        if not recommended_actions:
            recommended_actions = [
                "Request a plain-language summary of all repayment, penalty, and closure terms before signing.",
                "Verify that the annual interest rate and every fee are disclosed in writing.",
            ]

        danger_clauses = [detection["clause"] for detection in detections[:8]]
        flags = [
            {
                "issue": detection["category"],
                "clause_text": detection["clause"],
                "severity": detection["severity"],
                "regulation_violated": detection["risk_reason"],
                "suggested_fix": detection["suggested_fix"],
            }
            for detection in detections
        ]

        reviewed_clause_count = len(deduplicated_clauses)
        executive_summary = (
            f"Automated agreement scan completed on {datetime.utcnow().date().isoformat()}. "
            f"Reviewed {reviewed_clause_count} unique clauses after removing {duplicate_clauses_removed} duplicates. "
            f"Detected {len(detections)} material risk indicators."
        )
        if matched_keywords:
            executive_summary += f" Financial agreement markers found: {', '.join(matched_keywords[:5])}."
        if profile_notes:
            executive_summary += f" Borrower context: {profile_notes[0]}"

        result = {
            "document_type": "Financial agreement",
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_level_code": risk_level_code,
            "ai_verified": True,
            "executive_summary": executive_summary,
            "summary": executive_summary,
            "borrower_profile_context": user_profile,
            "keyword_matches": matched_keywords,
            "clause_count": reviewed_clause_count,
            "duplicate_clauses_removed": duplicate_clauses_removed,
            "detected_risks": detections,
            "missing_protections": missing_protections[:5],
            "danger_clauses": danger_clauses[:8],
            "recommended_actions": recommended_actions[:8],
            "flags": flags[:12],
            "missing_clauses": missing_protections[:5],
        }

        self.cache[key] = result
        return result


agreement_analysis_service = AgreementAnalysisService()