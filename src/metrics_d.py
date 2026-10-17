"""Stage D metrics. Ranking quality (oracle thresholds on the held-out group) is kept
separate from threshold transfer (thresholds fixed on validation of the training side)."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

NAMES = ["roc_auc", "pr_auc", "orec_fpr1", "orec_fpr01", "tr_fpr_val1", "tr_rec_val1",
         "tr_fpr_his", "tr_rec_his", "tr_prec_his", "tr_f1_his", "cnt_fpr_val1", "cnt_fpr_his",
         "oth_fpr_val1", "ece"]


def fold_weights(y, fold, prevalence):
    w = np.ones(len(y))
    for f in np.unique(fold):
        m = fold == f
        n1, n0 = max((y[m] == 1).sum(), 1), max((y[m] == 0).sum(), 1)
        w[m & (y == 1)] = prevalence / (1 - prevalence) * n0 / n1
    return w


def oracle_recall(y, s, fold, fpr):
    """Per fold: threshold = the fold's own normal-score quantile; recall pooled over folds."""
    tp = n = 0
    for f in np.unique(fold):
        m = fold == f
        sn, sa = s[m & (y == 0)], s[m & (y == 1)]
        if len(sn) == 0 or len(sa) == 0:
            continue
        thr = np.quantile(sn, 1 - fpr)
        tp += (sa > thr).sum(); n += len(sa)
    return tp / n if n else np.nan


def ece(y, p, w, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    b = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    tot, e = w.sum(), 0.0
    for k in range(bins):
        m = b == k
        if m.any():
            e += w[m].sum() / tot * abs(np.average(y[m], weights=w[m]) - np.average(p[m], weights=w[m]))
    return e


def compute(run: dict, prevalence: float, cfg: dict, idx=None) -> dict:
    g = (lambda a: a) if idx is None else (lambda a: a[idx])
    y, s, fold, reg = g(run["y"]), g(run["s"]), g(run["fold"]), g(run["reg"])
    thr = {k: g(v) for k, v in run["thr"].items()}
    w = fold_weights(y, fold, prevalence)
    two = len(np.unique(y)) == 2
    p_fpr = s > thr["fpr"]
    p_his = s >= thr["main"]
    n0, n1 = (y == 0), (y == 1)
    tp_w = w[n1 & p_his].sum(); fp_w = w[n0 & p_his].sum()
    prec = tp_w / (tp_w + fp_w) if tp_w + fp_w > 0 else 0.0
    rec = p_his[n1].mean() if n1.any() else np.nan
    f1 = 2 * prec * rec / (prec + rec) if prec + rec > 0 else 0.0
    cnt = n0 & (reg == "U0"); oth = n0 & (reg == "U")
    return {
        "roc_auc": roc_auc_score(y, s) if two else np.nan,
        "pr_auc": average_precision_score(y, s, sample_weight=w) if two else np.nan,
        "orec_fpr1": oracle_recall(y, s, fold, cfg["fpr_targets"][0]),
        "orec_fpr01": oracle_recall(y, s, fold, cfg["fpr_targets"][1]),
        "tr_fpr_val1": p_fpr[n0].mean(), "tr_rec_val1": p_fpr[n1].mean() if n1.any() else np.nan,
        "tr_fpr_his": p_his[n0].mean(), "tr_rec_his": rec, "tr_prec_his": prec, "tr_f1_his": f1,
        "cnt_fpr_val1": p_fpr[cnt].mean() if cnt.any() else np.nan,
        "cnt_fpr_his": p_his[cnt].mean() if cnt.any() else np.nan,
        "oth_fpr_val1": p_fpr[oth].mean() if oth.any() else np.nan,
        "ece": ece(y, s, w, cfg["ece_bins"]) if run.get("prob") else np.nan,
    }


def bootstrap(runs: list[dict], prevalence, cfg, reps, seed, ci=0.95) -> dict:
    """Rows resampled within (fold, class); metric averaged over seeds in each replicate.
    Captures within-set sampling and seed noise only, NOT between-group variation."""
    rng = np.random.default_rng(seed)
    cells = [[np.where((r["fold"] == f) & (r["y"] == c))[0] for f in np.unique(r["fold"]) for c in (0, 1)] for r in runs]
    pt = {k: float(np.nanmean([compute(r, prevalence, cfg)[k] for r in runs])) for k in NAMES}
    boots = {k: [] for k in NAMES}
    for _ in range(reps):
        vals = []
        for r, cl in zip(runs, cells):
            idx = np.concatenate([rng.choice(c, len(c)) for c in cl if len(c)])
            vals.append(compute(r, prevalence, cfg, idx))
        for k in NAMES:
            boots[k].append(np.nanmean([v[k] for v in vals]) if not all(np.isnan(v[k]) for v in vals) else np.nan)
    a = (1 - ci) / 2
    return {k: (pt[k], float(np.nanquantile(boots[k], a)) if not np.all(np.isnan(boots[k])) else np.nan,
                float(np.nanquantile(boots[k], 1 - a)) if not np.all(np.isnan(boots[k])) else np.nan) for k in NAMES}
