"""Stage E: Optuna tuning for M2 with the SAME budget, objective and validation scheme as M1."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split

from .metrics import prevalence_weights
from .models2 import FTTModel


def ftt_cfg(p: dict, base: dict, final: dict | None = None) -> dict:
    """Merge sampled hyperparameters into the M2 config. `final` switches to early-stopped training."""
    c = {**base, "d_token": int(p["d_token"]), "n_layers": int(p["n_layers"]), "n_heads": int(p["n_heads"]),
         "ffn": int(p["ffn"]), "dropout": float(p["dropout"]), "lr": float(p["lr"]),
         "weight_decay": float(p["weight_decay"]), "batch_size": int(p["batch_size"])}
    if final is None:                                   # tuning: fixed epochs, no early stopping
        c.update(max_epochs=int(p["epochs"]), es_patience=10 ** 6, warmup_epochs=max(1, int(p["epochs"]) // 10))
    else:                                               # final: early stopping on validation
        c.update(final)
    return c


def tune_ftt(Xtr, ytr, Xva, yva, space_cfg: dict, base_cfg: dict, hcfg: dict, seed: int) -> tuple[dict, dict]:
    """Same objective as M1: mean prevalence-weighted PR-AUC on (a) the group-held-out validation set
    and (b) a random fraction of the training side. M2 picks its OWN imbalance mechanism."""
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    ytr, yva = np.asarray(ytr), np.asarray(yva)
    i_a, i_b = train_test_split(np.arange(len(ytr)), test_size=hcfg["tune_random_holdout_frac"],
                                random_state=seed, stratify=ytr)
    sp, prev = space_cfg["space"], hcfg["prevalence"]

    def objective(trial):
        p = {"d_token": trial.suggest_categorical("d_token", sp["d_token"]),
             "n_layers": trial.suggest_categorical("n_layers", sp["n_layers"]),
             "n_heads": trial.suggest_categorical("n_heads", sp["n_heads"]),
             "ffn": trial.suggest_categorical("ffn", sp["ffn"]),
             "dropout": trial.suggest_float("dropout", *sp["dropout"]),
             "lr": trial.suggest_float("lr", *sp["lr"], log=True),
             "weight_decay": trial.suggest_float("weight_decay", *sp["weight_decay"], log=True),
             "batch_size": trial.suggest_categorical("batch_size", sp["batch_size"]),
             "epochs": trial.suggest_int("epochs", *sp["epochs"]),
             "imbalance": trial.suggest_categorical("imbalance", sp["imbalance"])}
        if p["imbalance"] == "focal":
            p["focal_gamma"] = trial.suggest_float("focal_gamma", *sp["focal_gamma"])
            p["focal_alpha"] = trial.suggest_float("focal_alpha", *sp["focal_alpha"])
        cfg = ftt_cfg(p, base_cfg)
        g, a = p.get("focal_gamma", 2.0), p.get("focal_alpha", 0.75)
        scores = []
        for (X_f, y_f), (X_v, y_v) in [((Xtr, ytr), (Xva, yva)), ((Xtr[i_b], ytr[i_b]), (Xtr[i_a], ytr[i_a]))]:
            m = FTTModel(cfg, p["imbalance"], g, a, seed).fit(X_f, y_f, X_f[:64], y_f[:64], restore_best=False)
            scores.append(average_precision_score(y_v, m.predict_proba(X_v), sample_weight=prevalence_weights(y_v, prev)))
        return float(np.mean(scores))

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=space_cfg["trials"], show_progress_bar=False)
    best = dict(study.best_params)
    best.setdefault("focal_gamma", 2.0); best.setdefault("focal_alpha", 0.75)
    return best, {"best_value": study.best_value, "trials": len(study.trials), "imbalance": best["imbalance"]}
