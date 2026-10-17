import numpy as np
import yaml

from src.data import ROOT
from src.metrics_d import compute, ece, fold_weights, oracle_recall

CFG = yaml.safe_load(open(ROOT / "configs" / "stage_d.yaml"))["metrics"]


def run(n=400, seed=0):
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < 0.3).astype(int); s = np.clip(0.3 * y + rng.normal(.35, .15, n), 0, 1)
    fold = np.repeat([0, 1], n // 2); reg = np.where(y == 1, "att", np.where(rng.random(n) < .1, "U0", "U"))
    thr = {k: np.full(n, v) for k, v in {"main": .5, "fpr": .7, "fpr01": .9, "rec": .3}.items()}
    return {"y": y, "s": s, "fold": fold, "reg": reg, "thr": thr, "prob": True}


def test_prevalence_weights_per_fold():
    r = run(); w = fold_weights(r["y"], r["fold"], 0.0835)
    for f in (0, 1):
        m = r["fold"] == f
        assert np.isclose(w[m & (r["y"] == 1)].sum() / w[m].sum(), 0.0835)


def test_oracle_recall_matches_definition_and_monotone():
    r = run()
    o1, o01 = oracle_recall(r["y"], r["s"], r["fold"], .01), oracle_recall(r["y"], r["s"], r["fold"], .001)
    assert 0 <= o01 <= o1 <= 1
    perfect = np.r_[np.zeros(100), np.ones(100)]
    assert oracle_recall(perfect.astype(int), perfect, np.zeros(200, int), .01) == 1.0


def test_ece_zero_when_calibrated_and_large_when_not():
    rng = np.random.default_rng(0); p = rng.random(20000); y = (rng.random(20000) < p).astype(int)
    assert ece(y, p, np.ones(len(y))) < 0.02
    assert ece(y, np.clip(p * 0.2, 0, 1), np.ones(len(y))) > 0.2


def test_compute_regime_split_and_threshold_transfer():
    r = run(); m = compute(r, 0.0835, CFG)
    assert 0 <= m["tr_fpr_val1"] <= 1 and 0 <= m["cnt_fpr_val1"] <= 1 and m["roc_auc"] > .6
    assert m["tr_fpr_val1"] <= m["tr_fpr_his"]            # thr .7 is stricter than .5
