from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LinearRegression


@dataclass
class DebtRiskModel:
    day_model: LinearRegression

    @classmethod
    def build(cls) -> "DebtRiskModel":
        # [emi_ratio, cc_utilization, loan_burden] -> days to danger
        x = np.array([
            [20, 25, 15],
            [30, 40, 25],
            [40, 60, 35],
            [55, 85, 65],
            [65, 90, 80],
            [75, 95, 90],
        ])
        y = np.array([999, 180, 75, 25, 12, 5])
        model = LinearRegression()
        model.fit(x, y)
        return cls(day_model=model)

    def predict_days_until_danger(self, emi_ratio: float, cc_utilization: float, loan_burden: float) -> int:
        days = self.day_model.predict([[emi_ratio, cc_utilization, loan_burden]])[0]
        return int(max(0, min(999, round(days))))