"""Weighted metrics, validation-derived thresholds, bootstrap CIs.

Evaluation folds contain more attacks than the original prevalence, so attack rows carry a
weight that restores the prevalence (cfg honest.prevalence) in precision, F1, FPR and PR-AUC.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def prevalence_weights(y: np.ndarray, prevalence: float) -> np.ndarray:
    n1, n0 = max((y == 1).sum(), 1), max((y == 0).sum(), 1)
    w = np.ones(len(y))
    w[y == 1] = (prevalence / (1 - prevalence)) * n0 / n1
    return w


def thresholds_from_validation(s_val, y_val, main_thr: float, fpr_target: float, recall_target: float) -> dict:
    """All operating points are fixed on VALIDATION data of the training side."""
    s_n, s_a = s_val[y_val == 0], s_val[y_val == 1]
    return {"main": main_thr,
            "fpr": float(np.quantile(s_n, 1 - fpr_target)),      # predict s >  thr  -> val FPR <= target
            "rec": float(np.quantile(s_a, 1 - recall_target))}   # predict s >= thr  -> val recall ~ target


def predictions(s, thr: dict) -> dict:
    return {"main": (s >= thr["main"]).astype(int), "fpr": (s > thr["fpr"]).astype(int),
            "rec": (s >= thr["rec"]).astype(int)}


def _rates(y, p, w):
    tp = w[(y == 1) & (p == 1)].sum(); fp = w[(y == 0) & (p == 1)].sum()
    fn = w[(y == 1) & (p == 0)].sum(); tn = w[(y == 0) & (p == 0)].sum()
    prec = tp / (tp + fp) if tp + fp > 0 else 0.0
    rec = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec > 0 else 0.0
    fpr = fp / (fp + tn) if fp + tn > 0 else 0.0
    return prec, rec, f1, fpr


METRIC_NAMES = ["precision", "recall", "f1", "fpr", "pr_auc", "roc_auc",
                "recall_at_fpr1", "realised_fpr_at_fpr1", "fpr_at_recall95", "realised_recall_at_rec95"]


def compute(y, s, w, preds: dict) -> dict:
    prec, rec, f1, fpr = _rates(y, preds["main"], w)
    _, rec1, _, fpr1 = _rates(y, preds["fpr"], w)
    _, rec2, _, fpr2 = _rates(y, preds["rec"], w)
    two = len(np.unique(y)) == 2
    return {"precision": prec, "recall": rec, "f1": f1, "fpr": fpr,
            "pr_auc": average_precision_score(y, s, sample_weight=w) if two else np.nan,
            "roc_auc": roc_auc_score(y, s) if two else np.nan,
            "recall_at_fpr1": rec1, "realised_fpr_at_fpr1": fpr1,
            "fpr_at_recall95": fpr2, "realised_recall_at_rec95": rec2}


def bootstrap(runs: list[dict], reps: int, seed: int, ci: float = 0.95) -> dict:
    """runs: one dict per seed with y, s, w, preds. Each run's rows are resampled independently
    (within class); the metric is averaged over seeds in every replicate. Returns
    {metric: (mean, lo, hi)}. Captures evaluation-set sampling noise and seed noise,
    NOT between-group variation (see per-fold results for that)."""
    rng = np.random.default_rng(seed)
    idx0 = [np.where(r["y"] == 0)[0] for r in runs]
    idx1 = [np.where(r["y"] == 1)[0] for r in runs]
    point = {k: float(np.nanmean([compute(r["y"], r["s"], r["w"], r["preds"])[k] for r in runs]))
             for k in METRIC_NAMES}
    boots = {k: [] for k in METRIC_NAMES}
    for _ in range(reps):
        vals = []
        for r, i0, i1 in zip(runs, idx0, idx1):
            idx = np.concatenate([rng.choice(i0, len(i0)), rng.choice(i1, len(i1))])
            vals.append(compute(r["y"][idx], r["s"][idx], r["w"][idx], {k: v[idx] for k, v in r["preds"].items()}))
        for k in METRIC_NAMES:
            boots[k].append(np.nanmean([v[k] for v in vals]))
    a = (1 - ci) / 2
    return {k: (point[k], float(np.nanquantile(boots[k], a)), float(np.nanquantile(boots[k], 1 - a)))
            for k in METRIC_NAMES}
