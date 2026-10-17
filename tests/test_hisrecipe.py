import numpy as np
import pandas as pd
import pytest
import torch
import yaml

from src.baselines import BestSingleFeature, LogReg
from src.data import ROOT
from src.features import FEATURES
from src.hisrecipe import (AttnMLP, HisEnsemble, Prep, engineer_features, focal_loss, his_attacks,
                           his_clip, his_fit, his_normal_noise, his_threshold)
from src.metrics import compute, predictions, prevalence_weights, thresholds_from_validation

CFG = yaml.safe_load(open(ROOT / "configs" / "stage_c.yaml"))


def toy(n=400, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame(rng.gamma(2.0, 1.0, (n, len(FEATURES))), columns=FEATURES)
    df["idle_ratio"] = rng.random(n); df["visibility_hidden"] = rng.integers(0, 2, n)
    return df


def test_focal_loss_matches_numpy_formula():
    y = np.array([1., 0., 1., 0.]); p = np.array([0.9, 0.2, 0.1, 0.8])
    got = focal_loss(torch.tensor(y), torch.tensor(p)).numpy()
    bce = -(y * np.log(p) + (1 - y) * np.log(1 - p)); pt = y * p + (1 - y) * (1 - p)
    foc = (0.85 * y + 0.15 * (1 - y)) * (1 - pt) ** 2 * bce
    want = (1 + 2.0 * (y * (1 - p))) * foc
    assert np.allclose(got, want, rtol=1e-5)
    assert got[2] > got[0]            # a missed attack costs far more than a caught one


def test_threshold_rule_recall_floor_and_fallback():
    y = np.array([1] * 10 + [0] * 90); rng = np.random.default_rng(1)
    s = np.r_[rng.uniform(.5, 1, 10), rng.uniform(0, .6, 90)]
    t = his_threshold(y, s, 0.97)
    assert ((s >= t) & (y == 1)).sum() / 10 >= 0.97
    s2 = np.r_[np.full(10, .5), np.full(90, .5)]                        # nothing separable: still returns a threshold
    assert his_threshold(y, s2, 0.97) == pytest.approx(.5)


def test_his_generator_tiers_and_columns():
    n = toy(2000); fit = his_fit(n)
    a = his_attacks(1000, fit, np.random.default_rng(0))
    assert a.shape == (1000, 11) and (a >= 0).all().all()
    assert np.isclose(a["idle_ratio"].median(), 0.3, atol=0.2)
    clipped = his_clip(n, fit)
    assert (clipped <= fit["cap"] + 1e-12).all().all()
    noisy = his_normal_noise(clipped, fit, np.random.default_rng(1))
    assert (noisy >= 0).all().all() and not noisy.equals(clipped)


def test_engineer_gives_18_and_prep_modes():
    d = toy(50)
    assert engineer_features(d).shape[1] == 18
    p11, p18 = Prep("coded11"), Prep("described18")
    assert p11.fit(d).shape[1] == 11 and p18.fit(d).shape[1] == 18
    assert np.allclose(p11.transform(d).mean(0), 0, atol=1e-8)


def test_network_shapes_and_l2_targets():
    net = AttnMLP(11); net.eval()
    assert net(torch.randn(5, 11)).shape == (5,) and len(net.kernels()) == 6


def test_ensemble_trains_deterministically_on_separable_toy():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(600, 11)); y = (X[:, 0] + X[:, 1] > 0.8).astype(int)
    cfg = {**CFG["his"], "max_epochs": 8}
    p1 = HisEnsemble(cfg, 7).fit(X[:400], y[:400], X[400:500], y[400:500]).predict_proba(X[500:])
    p2 = HisEnsemble(cfg, 7).fit(X[:400], y[:400], X[400:500], y[400:500]).predict_proba(X[500:])
    assert np.allclose(p1, p2, atol=1e-5)
    from sklearn.metrics import roc_auc_score
    assert roc_auc_score(y[500:], p1) > 0.9


def test_baselines_and_metrics():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(500, 5)); y = (X[:, 2] > 0.3).astype(int)
    b = BestSingleFeature().fit(X, y)
    assert b.j == 2 and LogReg().fit(X, y).predict_proba(X).shape == (500,)
    w = prevalence_weights(y, 0.0835)
    assert np.isclose(w[y == 1].sum() / w.sum(), 0.0835)
    s = b.predict_proba(X)
    thr = thresholds_from_validation(s, y, his_threshold(y, s), 0.01, 0.95)
    m = compute(y, s, w, predictions(s, thr))
    assert m["roc_auc"] > 0.99 and m["realised_fpr_at_fpr1"] <= 0.02
