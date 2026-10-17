"""REPRODUCTION OF THE DESCRIBED METHOD of the original CryptoShield project.

Not his checkpoint: his pickles cannot be loaded (TensorFlow not installed) and his
anomaly generator was never saved as a script. Everything here is re-implemented from
CryptoShield_Final.ipynb (cells 28-38), with the deviations listed in
docs/STAGE_C_REPORT.md. Torch replaces Keras; numbers copied from the notebook are in
configs/stage_c.yaml.
"""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import precision_recall_curve
from sklearn.preprocessing import StandardScaler

from .features import FEATURES

EPS = 1e-7  # keras backend epsilon


# ----------------------------------------------------------------- features (cell 28)
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """His seven ratio/interaction features, verbatim. Returns 18 columns."""
    d = df[FEATURES].copy()
    d["lag_per_dom"] = d["lag_per_second"] / (d["dom_per_second"] + 1e-6)
    d["network_per_dom"] = d["network_per_second"] / (d["dom_per_second"] + 1e-6)
    d["post_per_network"] = d["post_request_count"] / (d["network_request_count"] + 1e-6)
    d["cpu_stress_score"] = (1 - d["idle_ratio"]) * d["lag_per_second"]
    d["stealth_score"] = d["visibility_hidden"] * (1 - d["idle_ratio"])
    d["loop_pressure"] = d["event_loop_lag_ms"] * d["lag_per_second"]
    d["domain_concentration"] = d["post_request_count"] / (d["unique_domains_contacted"] + 1e-6)
    return d


# ------------------------------------------------- his tiered anomaly generator (cell 28)
LAG_LIKE = ["event_loop_lag_ms", "lag_per_second", "dom_per_second", "network_per_second"]


def his_fit(normals: pd.DataFrame) -> dict:
    """Clip cap (p99) and the percentiles of the CLIPPED normals, per feature."""
    cap = normals[FEATURES].quantile(0.99)
    clipped = normals[FEATURES].clip(upper=cap, axis=1)
    return {"cap": cap, "p75": clipped.quantile(0.75), "p90": clipped.quantile(0.90),
            "p99": clipped.quantile(0.99), "std": clipped.std()}


def his_clip(df: pd.DataFrame, fit: dict) -> pd.DataFrame:
    return df[FEATURES].clip(upper=fit["cap"], axis=1)


def his_normal_noise(clipped: pd.DataFrame, fit: dict, rng: np.random.Generator,
                     frac: float = 0.08) -> pd.DataFrame:
    out = clipped.copy()
    for c in FEATURES:
        out[c] = (out[c] + rng.normal(0, fit["std"][c] * frac, len(out))).clip(lower=0)
    return out


def his_attacks(n: int, fit: dict, rng: np.random.Generator, noise: float = 0.15,
                split=(0.4, 0.4, 0.2)) -> pd.DataFrame:
    """Three tiers (clear / moderate / borderline), each column drawn independently."""
    n_a, n_b = int(n * split[0]), int(n * split[1])
    n_c = n - n_a - n_b
    cols = []
    for c in FEATURES:
        p75, p90, p99 = fit["p75"][c], fit["p90"][c], fit["p99"][c]
        if c == "idle_ratio":
            a, b, t = rng.uniform(0.02, 0.20, n_a), rng.uniform(0.20, 0.40, n_b), rng.uniform(0.35, 0.60, n_c)
        elif c in LAG_LIKE:
            a, b, t = (rng.uniform(p99 * 2.0, p99 * 4.0, n_a), rng.uniform(p90 * 1.2, p99 * 2.0, n_b),
                       rng.uniform(p75 * 1.0, p90 * 1.2, n_c))
        else:
            a, b, t = (rng.uniform(p90 * 1.5, p99 * 3.0, n_a), rng.uniform(p75 * 1.2, p90 * 1.5, n_b),
                       rng.uniform(p75 * 0.9, p75 * 1.2, n_c))
        cols.append(np.concatenate([a, b, t]).clip(min=0))
    df = pd.DataFrame(np.column_stack(cols), columns=FEATURES)
    df = df.iloc[rng.permutation(len(df))].reset_index(drop=True)
    for c in FEATURES:
        df[c] = (df[c] + rng.normal(0, df[c].std() * noise, len(df))).clip(lower=0)
    return df


# ------------------------------------------------------------ preprocessing wrapper
class Prep:
    """clip (optional) -> engineer (if 18 features) -> StandardScaler. Carried with the model."""

    def __init__(self, mode: str, cap: pd.Series | None = None):
        assert mode in ("coded11", "described18")
        self.mode, self.cap, self.scaler = mode, cap, StandardScaler()

    def raw(self, df: pd.DataFrame) -> pd.DataFrame:
        d = df[FEATURES]
        if self.cap is not None:
            d = d.clip(upper=self.cap, axis=1)
        return engineer_features(d) if self.mode == "described18" else d

    def fit(self, df: pd.DataFrame) -> np.ndarray:
        return self.scaler.fit_transform(self.raw(df).to_numpy(float))

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.scaler.transform(self.raw(df).to_numpy(float))


# ------------------------------------------------------------------- the network
class AttnMLP(nn.Module):
    """His Attention-MLP: Dense64-BN-ReLU-Drop .5, residual block, 64-wide sigmoid gate,
    Dense32 / Dense16 with BN, sigmoid output. (The gate is over hidden units, not inputs.)"""

    def __init__(self, d: int, drop=(0.5, 0.5, 0.4)):
        super().__init__()
        bn = lambda k: nn.BatchNorm1d(k, momentum=0.01, eps=1e-3)  # keras momentum .99, eps 1e-3
        self.d1, self.b1 = nn.Linear(d, 64), bn(64)
        self.d2, self.b2 = nn.Linear(64, 64), bn(64)
        self.d3, self.b3 = nn.Linear(64, 64), bn(64)
        self.att = nn.Linear(64, 64)
        self.d4, self.b4 = nn.Linear(64, 32), bn(32)
        self.d5, self.b5 = nn.Linear(32, 16), bn(16)
        self.out = nn.Linear(16, 1)
        self.r1, self.r2, self.r3 = nn.Dropout(drop[0]), nn.Dropout(drop[1]), nn.Dropout(drop[2])
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight); nn.init.zeros_(m.bias)  # keras glorot_uniform

    def kernels(self):  # layers with an L2 kernel regulariser in his code (not the output layer)
        return [self.d1.weight, self.d2.weight, self.d3.weight, self.att.weight, self.d4.weight, self.d5.weight]

    def forward(self, x):
        x = self.r1(torch.relu(self.b1(self.d1(x))))
        skip = x
        x = torch.relu(self.b2(self.d2(x)))
        x = self.b3(self.d3(x))
        x = self.r2(torch.relu(x + skip))
        x = x * torch.sigmoid(self.att(x))
        x = self.r3(self.b4(torch.relu(self.d4(x))))
        x = self.b5(torch.relu(self.d5(x)))
        return torch.sigmoid(self.out(x)).squeeze(-1)


def focal_loss(y, p, gamma=2.0, alpha=0.85, fn_weight=3.0) -> torch.Tensor:
    """Per-sample asymmetric focal loss, exactly as coded in the notebook (cell 30)."""
    p = p.clamp(EPS, 1 - EPS)
    bce = -(y * torch.log(p) + (1 - y) * torch.log(1 - p))
    p_t = y * p + (1 - y) * (1 - p)
    alpha_t = alpha * y + (1 - alpha) * (1 - y)
    focal = alpha_t * (1 - p_t) ** gamma * bce
    return (1.0 + (fn_weight - 1.0) * (y * (1 - p))) * focal


def train_attn_mlp(Xtr, ytr, Xva, yva, cfg: dict, seed: int) -> tuple[AttnMLP, dict]:
    """Adam 3e-4, batch 64, <=150 epochs, EarlyStopping(val_loss, 20, restore best),
    ReduceLROnPlateau(.5, 8, 1e-6). Class weights 'balanced' are applied per sample ON TOP of
    the focal loss, as the described method says (see report: his Keras custom loss returns a
    scalar, so how Keras applied class_weight cannot be reproduced without TensorFlow)."""
    torch.manual_seed(seed)
    gen = torch.Generator().manual_seed(seed)
    f = lambda a: torch.as_tensor(np.asarray(a), dtype=torch.float32)
    Xtr, ytr, Xva, yva = f(Xtr), f(ytr), f(Xva), f(yva)
    net = AttnMLP(Xtr.shape[1], tuple(cfg["dropout"]))
    opt = torch.optim.Adam(net.parameters(), lr=cfg["lr"], eps=1e-7)
    n1 = float(ytr.sum()); n0 = len(ytr) - n1
    cw = torch.tensor([len(ytr) / (2 * n0), len(ytr) / (2 * n1)])
    fl = cfg["focal"]; l2 = cfg["l2"]
    penalty = lambda: l2 * sum((k ** 2).sum() for k in net.kernels())
    best, wait, best_lr, wait_lr, best_state, stopped = np.inf, 0, np.inf, 0, None, None
    for epoch in range(cfg["max_epochs"]):
        net.train()
        perm = torch.randperm(len(ytr), generator=gen)
        for i in range(0, len(perm), cfg["batch_size"]):
            idx = perm[i:i + cfg["batch_size"]]
            if len(idx) < 2:
                continue
            p = net(Xtr[idx])
            w = cw[ytr[idx].long()]
            loss = (w * focal_loss(ytr[idx], p, **fl)).mean() + penalty()
            opt.zero_grad(); loss.backward(); opt.step()
        net.eval()
        with torch.no_grad():
            val = (focal_loss(yva, net(Xva), **fl).mean() + penalty()).item()
        if val < best:
            best, wait, best_state = val, 0, copy.deepcopy(net.state_dict())
        else:
            wait += 1
        if val < best_lr - cfg["rlrop_min_delta"]:
            best_lr, wait_lr = val, 0
        else:
            wait_lr += 1
            if wait_lr >= cfg["rlrop_patience"]:
                for g in opt.param_groups:
                    g["lr"] = max(g["lr"] * cfg["rlrop_factor"], cfg["rlrop_min_lr"])
                wait_lr = 0
        if wait >= cfg["es_patience"]:
            stopped = epoch + 1
            break
    net.load_state_dict(best_state); net.eval()
    return net, {"epochs_run": epoch + 1, "early_stopped_at": stopped, "best_val_loss": best}


class HisEnsemble:
    """0.5 * Attention-MLP + 0.5 * XGBoost on the same scaled features."""

    def __init__(self, cfg: dict, seed: int):
        self.cfg, self.seed, self.info = cfg, seed, {}

    def fit(self, Xtr, ytr, Xva, yva) -> "HisEnsemble":
        from xgboost import XGBClassifier
        self.net, self.info = train_attn_mlp(Xtr, ytr, Xva, yva, self.cfg, self.seed)
        ytr = np.asarray(ytr)
        self.xgb = XGBClassifier(**self.cfg["xgb"], scale_pos_weight=float((ytr == 0).sum() / max((ytr == 1).sum(), 1)),
                                 random_state=self.seed, eval_metric="logloss", n_jobs=1).fit(Xtr, ytr)
        return self

    def predict_proba(self, X) -> np.ndarray:
        with torch.no_grad():
            dl = self.net(torch.as_tensor(np.asarray(X), dtype=torch.float32)).numpy()
        return self.cfg["blend"]["dl"] * dl + self.cfg["blend"]["xgb"] * self.xgb.predict_proba(X)[:, 1]


def his_threshold(y_val, p_val, recall_min: float = 0.97) -> float:
    """His rule (cell 38): max F1 subject to recall >= recall_min on validation, else max recall."""
    prec, rec, thr = precision_recall_curve(y_val, p_val)
    f1 = 2 * prec[:-1] * rec[:-1] / (prec[:-1] + rec[:-1] + 1e-9)
    mask = rec[:-1] >= recall_min
    idx = int(np.where(mask, f1, 0).argmax()) if mask.any() else int(np.argmax(rec[:-1]))
    return float(thr[idx])
