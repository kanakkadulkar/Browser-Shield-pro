"""Trivial baselines for context: logistic regression and the best single-feature threshold."""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score


class LogReg:
    def fit(self, X, y, *_):
        self.m = LogisticRegression(max_iter=2000, class_weight="balanced").fit(X, y)
        return self

    def predict_proba(self, X):
        return self.m.predict_proba(X)[:, 1]


class BestSingleFeature:
    """Pick the feature with the highest training ROC-AUC (sign-adjusted); score = +/- value."""

    def fit(self, X, y, *_):
        aucs = [roc_auc_score(y, X[:, j]) for j in range(X.shape[1])]
        self.j = int(np.argmax(np.maximum(aucs, 1 - np.array(aucs))))
        self.sign = 1.0 if aucs[self.j] >= 0.5 else -1.0
        self.auc = float(max(aucs[self.j], 1 - aucs[self.j]))
        return self

    def predict_proba(self, X):  # a monotone score, not a probability
        return self.sign * X[:, self.j]
