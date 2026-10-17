import numpy as np
import pytest
import torch
import yaml
from sklearn.metrics import roc_auc_score

from src.data import ROOT
from src.models2 import (AutoEncoder, FTTModel, FTTransformer, IForest, XgbModel, focal_grad,
                         focal_objective, focal_value, tune_xgb)

D = yaml.safe_load(open(ROOT / "configs" / "stage_d.yaml"))


def toy(n=800, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 6)); y = (X[:, 0] + 0.5 * X[:, 1] > 1.0).astype(int)
    return X, y


@pytest.mark.parametrize("gamma,alpha", [(0.5, 0.5), (2.0, 0.75), (3.0, 0.95)])
def test_focal_gradient_matches_finite_difference(gamma, alpha):
    z = np.linspace(-6, 6, 25); h = 1e-5
    for y in (0, 1):
        yy = np.full_like(z, y)
        num = (focal_value(z + h, yy, gamma, alpha) - focal_value(z - h, yy, gamma, alpha)) / (2 * h)
        assert np.allclose(focal_grad(z, yy, gamma, alpha), num, rtol=1e-3, atol=1e-6)


def test_xgb_both_mechanisms_learn_and_are_deterministic():
    X, y = toy()
    base = dict(n_estimators=60, max_depth=3, learning_rate=0.2, subsample=0.9, colsample_bytree=0.9,
                min_child_weight=1.0, reg_lambda=1.0, focal_gamma=2.0, focal_alpha=0.75)
    for mech in ("class_weight", "focal"):
        a = XgbModel({**base, "imbalance": mech}, 1).fit(X[:600], y[:600]).predict_proba(X[600:])
        b = XgbModel({**base, "imbalance": mech}, 1).fit(X[:600], y[:600]).predict_proba(X[600:])
        assert np.allclose(a, b) and roc_auc_score(y[600:], a) > 0.95 and a.min() >= 0 and a.max() <= 1


def test_tune_returns_one_mechanism():
    X, y = toy(500)
    m = {**D["m1"], "trials": 4}
    best, info = tune_xgb(X[:350], y[:350], X[350:], y[350:], m, D["honest"], 3)
    assert best["imbalance"] in ("class_weight", "focal") and info["trials"] == 4


def test_ft_transformer_shapes_and_learns():
    net = FTTransformer(6); assert net(torch.randn(5, 6)).shape == (5,)
    X, y = toy()
    cfg = {**D["m2"], "max_epochs": 12}
    p = FTTModel(cfg, "class_weight", 2.0, 0.75, 1).fit(X[:500], y[:500], X[500:650], y[500:650]).predict_proba(X[650:])
    assert roc_auc_score(y[650:], p) > 0.9
    p2 = FTTModel(cfg, "focal", 2.0, 0.75, 1).fit(X[:500], y[:500], X[500:650], y[500:650]).predict_proba(X[650:])
    assert roc_auc_score(y[650:], p2) > 0.85


def test_one_class_models_flag_outliers():
    rng = np.random.default_rng(0)
    N, V = rng.normal(size=(600, 6)), rng.normal(size=(200, 6)); O = rng.normal(5, 1, size=(100, 6))
    X = np.r_[V, O]; y = np.r_[np.zeros(200), np.ones(100)]
    assert roc_auc_score(y, IForest(100, 1).fit(N).score(X)) > 0.95
    ae = AutoEncoder({**D["m4"]["ae"], "max_epochs": 30}, 1).fit(N, V)
    assert roc_auc_score(y, ae.score(X)) > 0.9


def test_restore_best_flag_keeps_default_behaviour_and_tune_ftt_runs():
    from src.models3 import ftt_cfg, tune_ftt
    X, y = toy(500)
    cfg = {**D["m2"], "max_epochs": 6}
    a = FTTModel(cfg, "class_weight", 2.0, 0.75, 1).fit(X[:300], y[:300], X[300:400], y[300:400])
    b = FTTModel(cfg, "class_weight", 2.0, 0.75, 1).fit(X[:300], y[:300], X[300:400], y[300:400], restore_best=True)
    assert np.allclose(a.predict_proba(X[400:]), b.predict_proba(X[400:]), atol=1e-6)
    E = yaml.safe_load(open(ROOT / "configs" / "stage_e.yaml"))
    sp = {**E["m2_tuned"], "trials": 3, "space": {**E["m2_tuned"]["space"], "epochs": [3, 5]}}
    best, info = tune_ftt(X[:300], y[:300], X[300:400], y[300:400], sp, D["m2"], D["honest"], 3)
    assert best["imbalance"] in ("class_weight", "focal") and info["trials"] == 3
    c = ftt_cfg(best, D["m2"], E["m2_tuned"]["final_fit"])
    assert c["d_token"] % c["n_heads"] == 0 and c["max_epochs"] == 80
