from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression


@dataclass
class LoanApprovalModel:
    classifier: LogisticRegression

    @classmethod
    def build(cls) -> "LoanApprovalModel":
        # [salary, existing_loan_ratio, credit_score, employment_code]
        x = np.array([
            [30000, 0.45, 620, 1],
            [45000, 0.30, 690, 1],
            [65000, 0.25, 730, 1],
            [90000, 0.20, 780, 1],
            [40000, 0.55, 640, 0],
            [75000, 0.35, 710, 0],
            [120000, 0.15, 810, 1],
            [28000, 0.60, 580, 0],
        ])
        y = np.array([0, 1, 1, 1, 0, 1, 1, 0])
        clf = LogisticRegression(max_iter=300)
        clf.fit(x, y)
        return cls(classifier=clf)

    def predict_approval_probability(self, salary: float, loan_ratio: float, credit_score: int, employment_code: int) -> float:
        prob = self.classifier.predict_proba([[salary, loan_ratio, credit_score, employment_code]])[0, 1]
        return float(np.clip(prob, 0.0, 1.0))