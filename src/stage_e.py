"""Stage E jobs: M1, fair (tuned) M2 and a counts-only model; raw member scores are stored.

One job = (reading, validation group, seed), source R2 (generator v2, held-out family excluded).
DEV DATA ONLY: the locked test groups are never read. Calibration, stacking, regime handling and
thresholds are computed afterwards (src/stage_e_analysis.py) from these arrays, fitted on the
VALIDATION arrays only.
"""
from __future__ import annotations

import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .data import ROOT, load_normals
from .features import FEATURES, regime
from .features2 import build_bsp
from .models2 import FTTModel, XgbModel, tune_xgb
from .models3 import ftt_cfg, tune_ftt
from .splits import build_protocol
from .stage_c import _frame, split_inner
from .stage_d import Pipe, cfgs
from .synth import generate, generate_for_groups

RAW = ROOT / "reports" / "stage_e" / "raw"


def ecfg():
    return yaml.safe_load(open(ROOT / "configs" / "stage_e.yaml"))


class CountsOnlyModel:
    """Separate model for counts-only rows (uptime unrecoverable); fit on TRAINING counts-only rows only."""

    def __init__(self, feats):
        self.feats = feats

    def fit(self, df, y, cfg) -> bool:
        b = build_bsp(df)
        co = b["counts_only"].to_numpy() == 1
        n0, n1 = int(((y == 0) & co).sum()), int(((y == 1) & co).sum())
        self.n_norm, self.n_att = n0, n1
        if n0 < cfg["min_train_normals"] or n1 < cfg["min_train_attacks"]:
            self.ok = False
            return False
        self.sc = StandardScaler().fit(b.loc[co, self.feats])
        self.lr = LogisticRegression(max_iter=2000, class_weight="balanced", C=1.0).fit(self.sc.transform(b.loc[co, self.feats]), y[co])
        self.ok = True
        return True

    def score(self, df):
        if not self.ok:
            return np.full(len(df), np.nan)
        return self.lr.predict_proba(self.sc.transform(build_bsp(df)[self.feats]))[:, 1]


def run_job(reading: str, fold_group: str, seed: int) -> dict:
    import torch
    torch.set_num_threads(1)
    D, sc, syn, spl = cfgs()
    E = ecfg()
    a, _ = load_normals("A"); b, _ = load_normals("B")
    proto = build_protocol(a, b)
    dev = proto["readings"][reading]["dev"]                          # DEV ONLY
    assert not set(dev["group"]) & set(proto["test_groups"])
    ev = dev[dev["group"] == fold_group].reset_index(drop=True)
    side = dev[dev["group"] != fold_group].reset_index(drop=True)
    tr, va, inner = split_inner(side, spl["min_fold_rows"], D["honest"]["inner_val_random_frac"], seed)
    ho = D["generator"]["heldout_family"]
    rt, re_ = D["honest"]["train_attack_ratio"], D["honest"]["eval_attack_ratio"]
    g = lambda base, ratio, sd, **kw: generate_for_groups(base, syn, ratio, sd, version=2, **kw)
    ex = {"exclude_families": (ho,)}
    a_tr, a_va = g(tr, rt, seed * 100 + 1, **ex), g(va, rt, seed * 100 + 2, **ex)
    sets = {"ER2": g(ev, re_, seed * 100 + 3, **ex), "EHO": g(ev, re_, seed * 100 + 9, family=ho)}
    assert ho not in set(a_tr["family"]) | set(a_va["family"]), "held-out family leaked into training"
    df_tr, ytr = _frame(tr, a_tr); df_va, yva = _frame(va, a_va)
    pipe = Pipe("bsp")
    Xtr, Xva = pipe.fit(df_tr), pipe.transform(df_va)
    t0 = time.time()
    info = {}
    # M1 (identical procedure to Stage D)
    best1, i1 = tune_xgb(Xtr, ytr, Xva, yva, D["m1"], D["honest"], seed)
    m1 = XgbModel(best1, seed, D["m1"]["early_stopping_rounds"]).fit(Xtr, ytr, Xva, yva)
    info["m1"] = {"params": best1, **i1}
    # M2, same tuning budget / objective / validation scheme as M1, own imbalance choice
    best2, i2 = tune_ftt(Xtr, ytr, Xva, yva, E["m2_tuned"], D["m2"], D["honest"], seed)
    cfg2 = ftt_cfg(best2, D["m2"], E["m2_tuned"]["final_fit"])
    m2 = FTTModel(cfg2, best2["imbalance"], best2["focal_gamma"], best2["focal_alpha"], seed).fit(Xtr, ytr, Xva, yva)
    info["m2"] = {"params": best2, **i2, **m2.info}
    # counts-only model (training counts-only rows only)
    com = CountsOnlyModel(E["regime"]["counts_only_model"]["features"])
    ok = com.fit(df_tr, ytr, E["regime"]["counts_only_model"])
    info["co"] = {"available": ok, "train_counts_only_normals": com.n_norm, "train_counts_only_attacks": com.n_att}
    # training range for the "unsure" rule (raw bsp features of normals + attacks)
    Btr = build_bsp(df_tr)
    lo, hi = Btr.min().to_numpy(), Btr.max().to_numpy()
    delta = E["threshold_policy"]["unsure"]["delta"]
    oor = lambda df: ((build_bsp(df).to_numpy() < lo - delta * (hi - lo)) | (build_bsp(df).to_numpy() > hi + delta * (hi - lo))).any(axis=1)

    def pack(df, y, reg, fam):
        X = pipe.transform(df)
        return {"y": y, "reg": reg, "fam": fam, "co": build_bsp(df)["counts_only"].to_numpy().astype(int),
                "oor": oor(df), "s_m1": m1.predict_proba(X), "s_m2": m2.predict_proba(X), "s_co": com.score(df)}

    reg_va, reg_ev = regime(va).to_numpy(), regime(ev).to_numpy()
    out = {"reading": reading, "fold": fold_group, "seed": seed, "inner_val": inner, "info": info,
           "sizes": {"train_norm": len(tr), "val_norm": len(va), "eval_norm": len(ev), "train_att": len(a_tr),
                     "val_att": len(a_va), "eval_att": {k: len(v) for k, v in sets.items()},
                     "val_counts_only_normals": int((reg_va == "U0").sum()), "eval_counts_only_normals": int((reg_ev == "U0").sum())},
           "val": pack(df_va, yva, np.r_[reg_va, np.full(len(a_va), "att")], np.r_[np.full(len(va), "norm"), a_va["family"].to_numpy()]),
           "eval": {}, "sweep": {}}
    for k, att in sets.items():
        df, y = _frame(ev, att)
        out["eval"][k] = pack(df, y, np.r_[reg_ev, np.full(len(att), "att")], np.r_[np.full(len(ev), "norm"), att["family"].to_numpy()])
    for fam in D["sweep"]["families"]:
        for st in D["sweep"]["strengths"]:
            att = generate(ev, D["sweep"]["n_per_cell"], syn, seed * 100 + 8, family=fam, strength=st,
                           keep_unchanged=True, version=2)
            if len(att):
                X = pipe.transform(att)
                out["sweep"][(fam, st)] = {"s_m1": m1.predict_proba(X), "s_m2": m2.predict_proba(X), "s_co": com.score(att),
                                           "co": build_bsp(att)["counts_only"].to_numpy().astype(int), "oor": oor(att)}
    out["fit_seconds"] = round(time.time() - t0, 1)
    return out


def _job(args):
    t0 = time.time()
    res = run_job(*args)
    RAW.mkdir(parents=True, exist_ok=True)
    with open(RAW / ("_".join(map(str, args)) + ".pkl"), "wb") as fh:
        pickle.dump(res, fh)
    return "_".join(map(str, args)), round(time.time() - t0, 1)


if __name__ == "__main__":
    D, sc, syn, spl = cfgs()
    E = ecfg()
    a, _ = load_normals("A"); b, _ = load_normals("B")
    proto = build_protocol(a, b)
    jobs = [(r, gname, sd) for r in E["readings"] for gname in proto["readings"][r]["val_groups"] for sd in E["seeds"]]
    jobs = [j for j in jobs if not (RAW / ("_".join(map(str, j)) + ".pkl")).exists()]
    n_workers = int(os.environ.get("WORKERS", 9))
    print(f"{len(jobs)} jobs, {n_workers} workers", flush=True)
    import multiprocessing as mp
    with ProcessPoolExecutor(n_workers, mp_context=mp.get_context("spawn")) as ex:
        futs = {ex.submit(_job, j): j for j in jobs}
        for f in as_completed(futs):
            try:
                print("done", *f.result(), flush=True)
            except Exception as e:
                import traceback
                print("FAILED", futs[f], repr(e), traceback.format_exc()[-800:], flush=True)
