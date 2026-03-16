from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor


@dataclass
class FestivalSpikeModel:
    regressor: GradientBoostingRegressor

    @classmethod
    def build(cls) -> "FestivalSpikeModel":
        # [base_monthly_spend, festival_weight, days_to_event]
        x = np.array([
            [20000, 0.9, 30],
            [35000, 0.95, 45],
            [15000, 0.5, 20],
            [28000, 0.8, 25],
            [50000, 1.0, 60],
            [22000, 0.7, 15],
        ])
        y = np.array([18000, 36000, 7000, 19000, 60000, 9000])
        model = GradientBoostingRegressor(random_state=42)
        model.fit(x, y)
        return cls(regressor=model)

    def predict_expected_spike(self, base_monthly_spend: float, festival_weight: float, days_to_event: int) -> float:
        pred = self.regressor.predict([[base_monthly_spend, festival_weight, max(days_to_event, 1)]])[0]
        return float(max(pred, 0.0))