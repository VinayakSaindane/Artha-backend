from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


@dataclass
class AgreementRiskModel:
    vectorizer: TfidfVectorizer
    classifier: LogisticRegression

    @classmethod
    def build(cls) -> "AgreementRiskModel":
        samples = [
            "fixed interest rate no prepayment penalty transparent terms",
            "late fee and compounding penalty with unilateral arbitration",
            "floating rate at lender discretion hidden processing fees",
            "clear repayment schedule and no foreclosure charges",
            "penalty interest and legal recovery without borrower notice",
            "simple agreement with clear dispute resolution",
        ]
        labels = [0, 1, 1, 0, 1, 0]

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        x = vectorizer.fit_transform(samples)
        clf = LogisticRegression(max_iter=200)
        clf.fit(x, labels)
        return cls(vectorizer=vectorizer, classifier=clf)

    def predict_risk_probability(self, text: str) -> float:
        x = self.vectorizer.transform([text])
        prob = self.classifier.predict_proba(x)[0, 1]
        return float(np.clip(prob, 0.0, 1.0))