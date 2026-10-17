"""FINAL EVALUATION on the locked test set. Implements configs/stage_e_final.yaml exactly. Run ONCE.

Pipeline (frozen): bsp_v1 features -> M1 (XGBoost, 20 Optuna trials, tuned on the training side) ->
Platt calibration fit on validation -> regime handling V0 (none) -> policy: 'dangerous' above the
validation-normals quantile at 0.25%, 'suspicious' above the 5% level, 'unsure' for out-of-range inputs.
Trained on ALL dev groups (inner validation by the same rule as in dev). His recipe is the comparator,
trained on the same training side and attacks. Test attacks: generator v2 from the TEST groups' real
normals, seen families and the held-out family; SIMULATED MINER SIGNAL, same generator as training.
"""
from __future__ import annotations

import hashlib
import json
import os
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import yaml
from sklearn.linear_model import LogisticRegression

from .data import ROOT, load_normals
from .features import FEATURES, regime
from .features2 import build_bsp
from .models2 import XgbModel, tune_xgb
from .splits import build_protocol, fingerprint
from .stage_c import _frame, split_inner
from .stage_d import Pipe, cfgs, fit_supervised
from .synth import generate_for_groups

OUTDIR = ROOT / "reports" / "final_eval"


def lg(p):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def verify_freeze() -> dict:
    """The frozen config must be byte-identical to its lock, or we refuse to run."""
    lock = json.load(open(ROOT / "configs" / "stage_e_final.lock"))
    path = ROOT / lock["file"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == lock["sha256"], "frozen config changed"
    return yaml.safe_load(path.read_text())


def train_final(reading, seed, dev, D, sc, syn, spl, final, trials=None):
    pol = final["pipeline"]["threshold_policy"]
    ho = final["generator"]["heldout_family"]
    tr, va, inner = split_inner(dev, spl["min_fold_rows"], D["honest"]["inner_val_random_frac"], seed)
    rt = final["generator"]["train_attack_ratio"]
    g = lambda base, sd: generate_for_groups(base, syn, rt, sd, version=2, exclude_families=(ho,))
    a_tr, a_va = g(tr, seed * 100 + 1), g(va, seed * 100 + 2)
    assert ho not in set(a_tr["family"]) | set(a_va["family"])
    df_tr, ytr = _frame(tr, a_tr); df_va, yva = _frame(va, a_va)
    pipe = Pipe("bsp"); Xtr, Xva = pipe.fit(df_tr), pipe.transform(df_va)
    m1cfg = {**D["m1"], **({"trials": trials} if trials else {})}
    best, tinfo = tune_xgb(Xtr, ytr, Xva, yva, m1cfg, D["honest"], seed)
    m1 = XgbModel(best, seed, D["m1"]["early_stopping_rounds"]).fit(Xtr, ytr, Xva, yva)
    s_va = m1.predict_proba(Xva)
    platt = LogisticRegression(C=1e6, max_iter=5000).fit(lg(s_va).reshape(-1, 1), yva)
    cal = lambda s: platt.predict_proba(lg(s).reshape(-1, 1))[:, 1]
    c_va = cal(s_va)
    t_dang = float(np.quantile(c_va[yva == 0], 1 - pol["danger_validation_fpr"]))
    t_susp = float(np.quantile(c_va[yva == 0], 1 - pol["suspicious_validation_fpr"]))
    B = build_bsp(df_tr); lo, hi = B.min().to_numpy(), B.max().to_numpy(); d = pol["unsure"]["delta"]
    oor = lambda df: ((build_bsp(df).to_numpy() < lo - d * (hi - lo)) | (build_bsp(df).to_numpy() > hi + d * (hi - lo))).any(axis=1)
    his = fit_supervised("his11", "R2", {"cap": None, "tr_noisy": None, "train": {"R2": (tr, a_tr)}, "val": {"R2": (va, a_va)}}, seed, D, sc)
    return {"pipe": pipe, "m1": m1, "cal": cal, "t_dang": t_dang, "t_susp": t_susp, "oor": oor, "his": his,
            "info": {"inner_val": inner, "tuned": best, **tinfo, "n_train_norm": len(tr), "n_val_norm": len(va),
                     "n_train_att": len(a_tr), "n_val_att": len(a_va), "t_danger": t_dang, "t_suspicious": t_susp,
                     "his_thr": his.thr, "m1_trees": int(m1.booster.best_iteration + 1)}}


def evaluate(model, test, seed, D, syn, final):
    ho = final["generator"]["heldout_family"]; re_ = D["honest"]["eval_attack_ratio"]
    sets = {"ER2": generate_for_groups(test, syn, re_, seed * 100 + 3, version=2, exclude_families=(ho,)),
            "EHO": generate_for_groups(test, syn, re_, seed * 100 + 9, version=2, family=ho)}
    reg_t = regime(test).to_numpy(); out = {}
    for k, att in sets.items():
        df, y = _frame(test, att)
        X = model["pipe"].transform(df)
        raw = model["m1"].predict_proba(X); c = model["cal"](raw)
        oor = model["oor"](df).astype(bool)
        dang = (c > model["t_dang"]) & ~oor
        susp = (c > model["t_susp"]) & ~(c > model["t_dang"]) & ~oor
        out[k] = {"y": y, "group": np.r_[test["group"].to_numpy(), att["group"].to_numpy()], "fam": np.r_[np.full(len(test), "norm"), att["family"].to_numpy()],
                  "reg": np.r_[reg_t, np.full(len(att), "att")], "co": build_bsp(df)["counts_only"].to_numpy().astype(int),
                  "oor": oor, "raw": raw, "cal": c, "dang": dang, "susp": susp, "his": model["his"].score(df)}
    return out


def _job(args):
    reading, seed, trials, test_override_path = args
    final = verify_freeze()
    D, sc, syn, spl = cfgs()
    a, _ = load_normals("A"); b, _ = load_normals("B")
    proto = build_protocol(a, b)
    dev = proto["readings"][reading]["dev"]
    test = proto["readings"][reading]["test"]
    if test_override_path:                       # dry run only: a dev group stands in as "test"
        ov = pickle.load(open(test_override_path, "rb"))
        dev, test = ov[reading]["dev"], ov[reading]["test"]
    else:
        assert fingerprint(test) == final["data"]["test_fingerprint"], "test set differs from the locked one"
    t0 = time.time()
    model = train_final(reading, seed, dev, D, sc, syn, spl, final, trials)
    res = evaluate(model, test, seed, D, syn, final)
    return {"reading": reading, "seed": seed, "info": model["info"], "eval": res,
            "test_groups": sorted(test["group"].unique()), "seconds": round(time.time() - t0, 1)}


def main(out: Path = OUTDIR, trials=None, test_override_path=None, force=False):
    final = verify_freeze()
    out.mkdir(parents=True, exist_ok=True)
    done = out / "RUN_COMPLETE"
    if done.exists() and not force:
        sys.exit("The final evaluation was already run (RUN_COMPLETE exists). One evaluation only.")
    jobs = [(r, s, trials, test_override_path) for r in ["A", "B"] for s in final["training"]["seeds"]]
    results = []
    import multiprocessing as mp
    with ProcessPoolExecutor(6, mp_context=mp.get_context("spawn")) as ex:
        futs = {ex.submit(_job, j): j for j in jobs}
        for f in as_completed(futs):
            r = f.result(); results.append(r)
            print("done", r["reading"], r["seed"], r["seconds"], flush=True)
    pickle.dump(results, open(out / "raw.pkl", "wb"))
    done.write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
    print("saved", out / "raw.pkl")


if __name__ == "__main__":
    main()
