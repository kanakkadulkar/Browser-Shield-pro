"""Stage D models: M1 gradient boosting (Optuna), M2 feature-token attention net, M4 one-class."""
from __future__ import annotations

import copy
import math

import numpy as np
import torch
import torch.nn as nn
import xgboost as xgb
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split

from .metrics import prevalence_weights

EPS = 1e-7


# ------------------------------------------------------------------ focal loss (numpy, for XGBoost)
def _sig(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def focal_value(z, y, gamma, alpha):
    p = np.clip(_sig(z), EPS, 1 - EPS)
    return np.where(y == 1, -alpha * (1 - p) ** gamma * np.log(p), -(1 - alpha) * p ** gamma * np.log(1 - p))


def focal_grad(z, y, gamma, alpha):
    """d loss / d logit, analytic."""
    p = np.clip(_sig(z), EPS, 1 - EPS)
    g1 = alpha * (gamma * p * (1 - p) ** gamma * np.log(p) - (1 - p) ** (gamma + 1))
    g0 = (1 - alpha) * (-gamma * p ** gamma * (1 - p) * np.log(1 - p) + p ** (gamma + 1))
    return np.where(y == 1, g1, g0)


def focal_objective(gamma, alpha):
    def obj(preds, dtrain):
        y, h = dtrain.get_label(), 1e-3
        g = focal_grad(preds, y, gamma, alpha)
        hess = (focal_grad(preds + h, y, gamma, alpha) - focal_grad(preds - h, y, gamma, alpha)) / (2 * h)
        return g, np.maximum(hess, 1e-4)             # focal loss is non-convex: clip to keep boosting stable
    return obj


class XgbModel:
    """Native-API XGBoost with ONE imbalance mechanism: 'class_weight' or 'focal'."""

    def __init__(self, params: dict, seed: int, es_rounds: int = 40):
        self.p, self.seed, self.es = dict(params), seed, es_rounds

    def _fit_args(self, ytr):
        p = self.p
        base = {"max_depth": int(p["max_depth"]), "eta": p["learning_rate"], "subsample": p["subsample"],
                "colsample_bytree": p["colsample_bytree"], "min_child_weight": p["min_child_weight"],
                "lambda": p["reg_lambda"], "seed": self.seed, "nthread": 1, "tree_method": "hist",
                "eval_metric": "aucpr", "verbosity": 0}
        if p["imbalance"] == "class_weight":
            n1 = max(int((ytr == 1).sum()), 1)
            return {**base, "objective": "binary:logistic", "scale_pos_weight": float((ytr == 0).sum() / n1)}, None
        return {**base, "objective": "binary:logistic", "base_score": 0.5}, focal_objective(p["focal_gamma"], p["focal_alpha"])

    def fit(self, Xtr, ytr, Xva=None, yva=None) -> "XgbModel":
        ytr = np.asarray(ytr)
        params, obj = self._fit_args(ytr)
        d = xgb.DMatrix(Xtr, label=ytr)
        evals = [(xgb.DMatrix(Xva, label=np.asarray(yva)), "val")] if Xva is not None else []
        kw = dict(early_stopping_rounds=self.es) if evals else {}
        if obj is not None:
            params = {k: v for k, v in params.items() if k != "objective"}
        self.booster = xgb.train(params, d, int(self.p["n_estimators"]), evals=evals, obj=obj,
                                 verbose_eval=False, **kw)
        self.focal = obj is not None
        return self

    def predict_proba(self, X) -> np.ndarray:
        d = xgb.DMatrix(X)
        it = (0, self.booster.best_iteration + 1) if hasattr(self.booster, "best_iteration") else (0, 0)
        if self.focal:
            return _sig(self.booster.predict(d, output_margin=True, iteration_range=it))
        return self.booster.predict(d, iteration_range=it)


def tune_xgb(Xtr, ytr, Xva, yva, mcfg: dict, hcfg: dict, seed: int) -> tuple[dict, dict]:
    """Optuna (TPE) on the TRAINING SIDE only. Objective = mean prevalence-weighted PR-AUC over
    two validation splits: (a) the group-held-out validation set, (b) a random fraction of the
    training side. Returns (best_params, info)."""
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    ytr, yva = np.asarray(ytr), np.asarray(yva)
    i_a, i_b = train_test_split(np.arange(len(ytr)), test_size=hcfg["tune_random_holdout_frac"],
                                random_state=seed, stratify=ytr)
    sp, prev = mcfg["space"], hcfg["prevalence"]

    def objective(trial):
        p = {"n_estimators": trial.suggest_int("n_estimators", *sp["n_estimators"]),
             "max_depth": trial.suggest_int("max_depth", *sp["max_depth"]),
             "learning_rate": trial.suggest_float("learning_rate", *sp["learning_rate"], log=True),
             "subsample": trial.suggest_float("subsample", *sp["subsample"]),
             "colsample_bytree": trial.suggest_float("colsample_bytree", *sp["colsample_bytree"]),
             "min_child_weight": trial.suggest_float("min_child_weight", *sp["min_child_weight"], log=True),
             "reg_lambda": trial.suggest_float("reg_lambda", *sp["reg_lambda"], log=True),
             "imbalance": trial.suggest_categorical("imbalance", sp["imbalance"])}
        if p["imbalance"] == "focal":
            p["focal_gamma"] = trial.suggest_float("focal_gamma", *sp["focal_gamma"])
            p["focal_alpha"] = trial.suggest_float("focal_alpha", *sp["focal_alpha"])
        scores = []
        for (X_f, y_f), (X_v, y_v) in [((Xtr, ytr), (Xva, yva)), ((Xtr[i_b], ytr[i_b]), (Xtr[i_a], ytr[i_a]))]:
            m = XgbModel(p, seed).fit(X_f, y_f)           # no early stopping while tuning
            scores.append(average_precision_score(y_v, m.predict_proba(X_v), sample_weight=prevalence_weights(y_v, prev)))
        return float(np.mean(scores))

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=mcfg["trials"], show_progress_bar=False)
    best = dict(study.best_params)
    best.setdefault("focal_gamma", 2.0); best.setdefault("focal_alpha", 0.75)
    return best, {"best_value": study.best_value, "trials": len(study.trials), "imbalance": best["imbalance"]}


# ------------------------------------------------------------------ M2: feature-token attention net
class FTTransformer(nn.Module):
    """One token per numeric feature (x_j * w_j + b_j) plus [CLS]; pre-norm transformer encoder."""

    def __init__(self, n_feat: int, d: int = 32, layers: int = 2, heads: int = 4, ffn: int = 64, drop: float = 0.1):
        super().__init__()
        bound = 1 / math.sqrt(d)
        self.w = nn.Parameter(torch.empty(n_feat, d).uniform_(-bound, bound))
        self.b = nn.Parameter(torch.empty(n_feat, d).uniform_(-bound, bound))
        self.cls = nn.Parameter(torch.empty(1, 1, d).uniform_(-bound, bound))
        layer = nn.TransformerEncoderLayer(d, heads, ffn, drop, activation="gelu", batch_first=True, norm_first=True)
        self.enc = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.head = nn.Sequential(nn.LayerNorm(d), nn.ReLU(), nn.Linear(d, 1))

    def forward(self, x):
        tok = x.unsqueeze(-1) * self.w + self.b
        h = self.enc(torch.cat([self.cls.expand(len(x), -1, -1), tok], dim=1))
        return self.head(h[:, 0]).squeeze(-1)                     # logit


def _nn_loss(logit, y, mech: str, pos_weight: float, gamma: float, alpha: float):
    if mech == "class_weight":
        w = torch.where(y == 1, torch.tensor(pos_weight), torch.tensor(1.0))
        return (w * nn.functional.binary_cross_entropy_with_logits(logit, y, reduction="none")).mean()
    p = torch.sigmoid(logit).clamp(EPS, 1 - EPS)
    pt = y * p + (1 - y) * (1 - p)
    at = alpha * y + (1 - alpha) * (1 - y)
    return (at * (1 - pt) ** gamma * -torch.log(pt)).mean()


class FTTModel:
    def __init__(self, cfg: dict, mech: str, gamma: float, alpha: float, seed: int):
        self.cfg, self.mech, self.gamma, self.alpha, self.seed, self.info = cfg, mech, gamma, alpha, seed, {}

    def fit(self, Xtr, ytr, Xva, yva, restore_best: bool = True) -> "FTTModel":
        c, torch_ = self.cfg, torch
        torch_.manual_seed(self.seed); gen = torch_.Generator().manual_seed(self.seed)
        f = lambda a: torch_.as_tensor(np.asarray(a), dtype=torch_.float32)
        Xtr, ytr, Xva, yva = f(Xtr), f(ytr), f(Xva), f(yva)
        self.net = FTTransformer(Xtr.shape[1], c["d_token"], c["n_layers"], c["n_heads"], c["ffn"], c["dropout"])
        opt = torch_.optim.AdamW(self.net.parameters(), lr=c["lr"], weight_decay=c["weight_decay"])
        n1 = float(ytr.sum()); pw = (len(ytr) - n1) / max(n1, 1.0)
        sched = lambda e: ((e + 1) / c["warmup_epochs"] if e < c["warmup_epochs"] else
                           0.01 + 0.99 * 0.5 * (1 + math.cos(math.pi * (e - c["warmup_epochs"]) / max(c["max_epochs"] - c["warmup_epochs"], 1))))
        lrs = torch_.optim.lr_scheduler.LambdaLR(opt, sched)
        best, wait, state = np.inf, 0, None
        for epoch in range(c["max_epochs"]):
            self.net.train()
            perm = torch_.randperm(len(ytr), generator=gen)
            for i in range(0, len(perm), c["batch_size"]):
                idx = perm[i:i + c["batch_size"]]
                loss = _nn_loss(self.net(Xtr[idx]), ytr[idx], self.mech, pw, self.gamma, self.alpha)
                opt.zero_grad(); loss.backward(); opt.step()
            lrs.step()
            self.net.eval()
            with torch_.no_grad():
                v = _nn_loss(self.net(Xva), yva, self.mech, pw, self.gamma, self.alpha).item()
            if v < best - 1e-6:
                best, wait, state = v, 0, copy.deepcopy(self.net.state_dict())
            else:
                wait += 1
                if wait >= c["es_patience"]:
                    break
        if restore_best and state is not None:
            self.net.load_state_dict(state)
        self.net.eval()
        self.info = {"epochs_run": epoch + 1, "best_val_loss": best, "imbalance": self.mech}
        return self

    def predict_proba(self, X) -> np.ndarray:
        with torch.no_grad():
            return torch.sigmoid(self.net(torch.as_tensor(np.asarray(X), dtype=torch.float32))).numpy()


# ------------------------------------------------------------------ M4: one-class
class IForest:
    """Trained on normals only. Score = anomaly score (higher = more anomalous)."""

    def __init__(self, n_estimators: int, seed: int):
        self.m = IsolationForest(n_estimators=n_estimators, random_state=seed, n_jobs=1)

    def fit(self, X_normals, *_):
        self.m.fit(X_normals); return self

    def score(self, X):
        return -self.m.decision_function(X)


class AutoEncoder:
    """Small MLP autoencoder trained on normals only; score = reconstruction MSE."""

    def __init__(self, cfg: dict, seed: int):
        self.c, self.seed, self.info = cfg, seed, {}

    def fit(self, X_normals, X_val_normals):
        torch.manual_seed(self.seed); gen = torch.Generator().manual_seed(self.seed)
        f = lambda a: torch.as_tensor(np.asarray(a), dtype=torch.float32)
        Xt, Xv = f(X_normals), f(X_val_normals)
        h, d = self.c["hidden"], Xt.shape[1]
        dims = [d] + h
        enc = [m for i in range(len(h)) for m in (nn.Linear(dims[i], dims[i + 1]), nn.ReLU())]
        dec = [m for i in range(len(h) - 1, 0, -1) for m in (nn.Linear(dims[i + 1], dims[i]), nn.ReLU())] + [nn.Linear(dims[1], d)]
        self.net = nn.Sequential(*enc, *dec)
        opt = torch.optim.Adam(self.net.parameters(), lr=self.c["lr"])
        best, wait, state = np.inf, 0, None
        for epoch in range(self.c["max_epochs"]):
            self.net.train()
            perm = torch.randperm(len(Xt), generator=gen)
            for i in range(0, len(perm), self.c["batch_size"]):
                xb = Xt[perm[i:i + self.c["batch_size"]]]
                loss = ((self.net(xb) - xb) ** 2).mean()
                opt.zero_grad(); loss.backward(); opt.step()
            self.net.eval()
            with torch.no_grad():
                v = ((self.net(Xv) - Xv) ** 2).mean().item()
            if v < best - 1e-7:
                best, wait, state = v, 0, copy.deepcopy(self.net.state_dict())
            else:
                wait += 1
                if wait >= self.c["es_patience"]:
                    break
        self.net.load_state_dict(state); self.net.eval()
        self.info = {"epochs_run": epoch + 1, "best_val_mse": best}
        return self

    def score(self, X):
        x = torch.as_tensor(np.asarray(X), dtype=torch.float32)
        with torch.no_grad():
            return ((self.net(x) - x) ** 2).mean(dim=1).numpy()
