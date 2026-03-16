from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DebtMetrics:
    emi_to_income_ratio: float
    cc_utilization: float
    loan_burden_ratio: float


def safe_num(value: float | int | str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return default


def compute_debt_metrics(
    monthly_income: float | int | str,
    total_emi: float | int | str,
    credit_used: float | int | str,
    credit_limit: float | int | str,
    outstanding_loans: float | int | str,
) -> DebtMetrics:
    income = max(safe_num(monthly_income, 1.0), 1.0)
    emi = max(safe_num(total_emi), 0.0)
    used = max(safe_num(credit_used), 0.0)
    limit = max(safe_num(credit_limit, 1.0), 1.0)
    outstanding = max(safe_num(outstanding_loans), 0.0)

    return DebtMetrics(
        emi_to_income_ratio=(emi / income) * 100.0,
        cc_utilization=(used / limit) * 100.0,
        loan_burden_ratio=(outstanding / (income * 12.0)) * 100.0,
    )