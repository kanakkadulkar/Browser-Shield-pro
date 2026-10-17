"""Export the trained pipeline to JSON for in-browser JavaScript evaluation."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression

from .data import ROOT, load_normals
from .features2 import BSP_FEATURES, build_bsp
from .models2 import XgbModel, tune_xgb
from .splits import build_protocol
from .stage_c import _frame, split_inner
from .stage_d import Pipe, cfgs
from .synth import generate_for_groups


def lg(p):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def export_bundle(out_paths: list[Path]):
    final = {
        "pipeline": {
            "threshold_policy": {
                "danger_validation_fpr": 0.0025,
                "suspicious_validation_fpr": 0.05,
                "unsure": {"delta": 0.15}
            }
        },
        "generator": {
            "heldout_family": "throttled",
            "train_attack_ratio": 0.0911
        }
    }
    D, sc, syn, spl = cfgs()
    a, _ = load_normals("A")
    b, _ = load_normals("B")
    proto = build_protocol(a, b)
    dev = proto["readings"]["A"]["dev"]

    pol = final["pipeline"]["threshold_policy"]
    ho = final["generator"]["heldout_family"]
    seed = 42
    tr, va, inner = split_inner(dev, spl["min_fold_rows"], D["honest"]["inner_val_random_frac"], seed)
    rt = final["generator"]["train_attack_ratio"]
    g = lambda base, sd: generate_for_groups(base, syn, rt, sd, version=2, exclude_families=(ho,))
    a_tr, a_va = g(tr, seed * 100 + 1), g(va, seed * 100 + 2)
    df_tr, ytr = _frame(tr, a_tr)
    df_va, yva = _frame(va, a_va)

    pipe = Pipe("bsp")
    Xtr = pipe.fit(df_tr)
    Xva = pipe.transform(df_va)

    m1cfg = {**D["m1"], "trials": 20}
    best, tinfo = tune_xgb(Xtr, ytr, Xva, yva, m1cfg, D["honest"], seed)
    m1 = XgbModel(best, seed, D["m1"]["early_stopping_rounds"]).fit(Xtr, ytr, Xva, yva)

    s_va = m1.predict_proba(Xva)
    platt = LogisticRegression(C=1e6, max_iter=5000).fit(lg(s_va).reshape(-1, 1), yva)
    cal = lambda s: platt.predict_proba(lg(s).reshape(-1, 1))[:, 1]
    c_va = cal(s_va)

    t_dang = float(np.quantile(c_va[yva == 0], 1 - pol["danger_validation_fpr"]))
    t_susp = float(np.quantile(c_va[yva == 0], 1 - pol["suspicious_validation_fpr"]))

    B_tr = build_bsp(df_tr)
    lo = B_tr.min().to_numpy().tolist()
    hi = B_tr.max().to_numpy().tolist()
    d = float(pol["unsure"]["delta"])

    # Extract booster trees in JSON format
    tree_dumps = m1.booster.get_dump(dump_format="json")
    trees_json = [json.loads(t) for t in tree_dumps]

    # Scaler parameters
    scaler_mean = pipe.scaler.mean_.tolist()
    scaler_scale = pipe.scaler.scale_.tolist()

    # Normal baselines for SHAP / explanation heuristics
    normal_mean = df_tr.loc[ytr == 0, [
        "idle_ratio", "event_loop_lag_ms", "dom_mutation_count",
        "network_request_count", "post_request_count",
        "unique_domains_contacted", "visibility_hidden", "visibility_changes"
    ]].mean().to_dict()

    bundle = {
        "version": "1.0.0",
        "model_name": "BrowserShield-Pro M1 (XGBoost + Platt Calibration)",
        "features": BSP_FEATURES,
        "feature_count": len(BSP_FEATURES),
        "scaler": {
            "mean": scaler_mean,
            "scale": scaler_scale
        },
        "trees": trees_json,
        "num_trees": len(trees_json),
        "platt": {
            "coef": float(platt.coef_[0][0]),
            "intercept": float(platt.intercept_[0])
        },
        "thresholds": {
            "dangerous": t_dang,
            "suspicious": t_susp,
            "delta_oor": d
        },
        "bounds": {
            "min": lo,
            "max": hi
        },
        "normal_baselines": normal_mean,
        "training_metadata": {
            "num_train_samples": len(df_tr),
            "num_val_samples": len(df_va),
            "num_trees": len(trees_json),
            "best_params": {k: float(v) if isinstance(v, (np.floating, float)) else int(v) if isinstance(v, (np.integer, int)) else v for k, v in best.items()}
        }
    }

    for path in out_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(bundle, f, indent=2)
        print(f"Exported model bundle to {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    out_paths = [
        ROOT / "extension" / "model_bundle.json",
        ROOT / "demo" / "model_bundle.json"
    ]
    export_bundle(out_paths)
