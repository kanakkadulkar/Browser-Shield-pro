"""Stage E item 5: why did M1 (my features) trained on his generator score 0.938 on his own attacks
while logistic regression / M2 got ~0.997?  Dev data only, Reading A, same data as Stage D."""
from __future__ import annotations

import glob
import json
import pickle

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import average_precision_score, roc_auc_score

from .data import ROOT, load_normals
from .features import FEATURES
from .hisrecipe import his_attacks, his_fit
from .metrics import prevalence_weights
from .models2 import XgbModel
from .splits import build_protocol
from .stage_c import _frame, split_inner
from .stage_d import Pipe, cfgs


def main():
    D, sc, syn, spl = cfgs()
    E = yaml.safe_load(open(ROOT / "configs" / "stage_e.yaml"))
    a, _ = load_normals("A"); b, _ = load_normals("B")
    proto = build_protocol(a, b)
    dev = proto["readings"]["A"]["dev"]
    rt, re_ = D["honest"]["train_attack_ratio"], D["honest"]["eval_attack_ratio"]
    dp = E["oddity"]["default_params"]
    rows, stage_d_info = [], []
    for f in sorted(glob.glob(str(ROOT / "reports" / "stage_d" / "raw" / "A_*.pkl"))):
        job = pickle.load(open(f, "rb"))
        fold, seed = job["fold"], job["seed"]
        ev = dev[dev.group == fold].reset_index(drop=True)
        side = dev[dev.group != fold].reset_index(drop=True)
        tr, va, _ = split_inner(side, spl["min_fold_rows"], D["honest"]["inner_val_random_frac"], seed)
        fit = his_fit(tr)
        a_tr = his_attacks(round(rt * len(tr)), fit, np.random.default_rng(seed * 100 + 4))
        a_va = his_attacks(round(rt * len(va)), fit, np.random.default_rng(seed * 100 + 5))
        a_ev = his_attacks(round(re_ * len(ev)), fit, np.random.default_rng(seed * 100 + 6))
        (df_tr, ytr), (df_va, yva), (df_ev, yev) = _frame(tr, a_tr), _frame(va, a_va), _frame(ev, a_ev)
        pipe = Pipe("bsp"); Xtr, Xva, Xev = pipe.fit(df_tr), pipe.transform(df_va), pipe.transform(df_ev)
        w = prevalence_weights(yev, D["honest"]["prevalence"])
        tuned = job["info"][("m1_bsp", "H")]["tuned"]
        stage_d_info.append({"fold": fold[:6], "seed": seed, "imbalance": tuned["imbalance"], "n_estimators": tuned["n_estimators"],
                             "max_depth": tuned["max_depth"], "lr": round(tuned["learning_rate"], 3), "min_child_weight": round(tuned["min_child_weight"], 2)})
        variants = {"tuned_as_in_stage_d": tuned,
                    "default_class_weight": {**dp, "imbalance": "class_weight"},
                    "default_focal": {**dp, "imbalance": "focal"}}
        for name, params in variants.items():
            for es in (True, False):
                m = XgbModel(params, seed, D["m1"]["early_stopping_rounds"])
                m.fit(Xtr, ytr, Xva if es else None, yva if es else None)
                p = m.predict_proba(Xev)
                rows.append({"fold": fold[:6], "seed": seed, "fit": name, "early_stopping": es,
                             "trees_used": (m.booster.best_iteration + 1) if es else int(params["n_estimators"]),
                             "roc_auc": roc_auc_score(yev, p), "pr_auc": average_precision_score(yev, p, sample_weight=w)})
        # reference: the stored Stage D scores of the other models on the same eval set
        for kind in ("lr_bsp", "m2_bsp", "m1_bsp"):
            e = job["eval"][(kind, "H", "EH")]
            rows.append({"fold": fold[:6], "seed": seed, "fit": f"stage_d_stored:{kind}", "early_stopping": None, "trees_used": np.nan,
                         "roc_auc": roc_auc_score(e["y"], e["s"]), "pr_auc": average_precision_score(e["y"], e["s"], sample_weight=prevalence_weights(e["y"], D["honest"]["prevalence"]))})
    df = pd.DataFrame(rows)
    out = ROOT / "reports" / "stage_e"; out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "oddity_fits.csv", index=False)
    summ = df.groupby(["fit", "early_stopping"], dropna=False)[["roc_auc", "pr_auc", "trees_used"]].agg(["mean", "min", "max"]).round(3)
    summ.to_csv(out / "oddity_summary.csv")
    info = pd.DataFrame(stage_d_info); info.to_csv(out / "oddity_stage_d_tuned_params.csv", index=False)
    print(summ.to_string()); print(); print(info.to_string())


if __name__ == "__main__":
    main()


def r2_trees():
    """Same check for the primary setting: M1 trained on rebuilt v2 attacks (Stage D tuned params, early stopping)."""
    from .synth import generate_for_groups
    D, sc, syn, spl = cfgs()
    a, _ = load_normals("A"); b, _ = load_normals("B")
    dev = build_protocol(a, b)["readings"]["A"]["dev"]
    ho = D["generator"]["heldout_family"]
    rt, re_ = D["honest"]["train_attack_ratio"], D["honest"]["eval_attack_ratio"]
    rows = []
    for f in sorted(glob.glob(str(ROOT / "reports" / "stage_d" / "raw" / "A_*.pkl"))):
        job = pickle.load(open(f, "rb")); fold, seed = job["fold"], job["seed"]
        ev = dev[dev.group == fold].reset_index(drop=True); side = dev[dev.group != fold].reset_index(drop=True)
        tr, va, _ = split_inner(side, spl["min_fold_rows"], D["honest"]["inner_val_random_frac"], seed)
        g = lambda base, ratio, sd, **kw: generate_for_groups(base, syn, ratio, sd, version=2, **kw)
        a_tr, a_va = g(tr, rt, seed * 100 + 1, exclude_families=(ho,)), g(va, rt, seed * 100 + 2, exclude_families=(ho,))
        a_ev = g(ev, re_, seed * 100 + 3, exclude_families=(ho,))
        (df_tr, ytr), (df_va, yva), (df_ev, yev) = _frame(tr, a_tr), _frame(va, a_va), _frame(ev, a_ev)
        pipe = Pipe("bsp"); Xtr, Xva, Xev = pipe.fit(df_tr), pipe.transform(df_va), pipe.transform(df_ev)
        tuned = job["info"][("m1_bsp", "R2")]["tuned"]
        m = XgbModel(tuned, seed, D["m1"]["early_stopping_rounds"]).fit(Xtr, ytr, Xva, yva)
        rows.append({"fold": fold[:6], "seed": seed, "trees_tuned": int(tuned["n_estimators"]), "trees_used_with_es": m.booster.best_iteration + 1,
                     "roc_er2": roc_auc_score(yev, m.predict_proba(Xev))})
    df = pd.DataFrame(rows); df.to_csv(ROOT / "reports" / "stage_e" / "oddity_r2_trees.csv", index=False)
    print("\nM1 trained on rebuilt v2 (primary setting): trees actually used under early stopping")
    print(df.to_string()); print(df[["trees_tuned", "trees_used_with_es", "roc_er2"]].describe().round(3).loc[["mean", "min", "max"]])


if __name__ == "__main__":
    r2_trees()
