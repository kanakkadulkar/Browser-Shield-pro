"""Stage D jobs: own features + M1/M2/M4 vs his recipe and trivial baselines.

One job = (reading, validation group, seed). DEV DATA ONLY (locked test groups are never read).
Training sources: H (his generator), R1 (rebuilt v1), R2 (rebuilt v2); all trained WITHOUT the
held-out family. Evaluation sets: EH, ER1, ER2 (seen families) and EHO (held-out family only).
"""
from __future__ import annotations

import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd
import yaml
from sklearn.preprocessing import RobustScaler, StandardScaler

from .baselines import BestSingleFeature, LogReg
from .data import ROOT, load_normals
from .features import FEATURES, regime
from .features2 import build_bsp
from .hisrecipe import (HisEnsemble, Prep, his_attacks, his_clip, his_fit, his_normal_noise,
                        his_threshold)
from .metrics import thresholds_from_validation
from .models2 import AutoEncoder, FTTModel, IForest, XgbModel, tune_xgb
from .splits import build_protocol
from .stage_c import _frame, split_inner
from .synth import generate, generate_for_groups

RAW = ROOT / "reports" / "stage_d" / "raw"
SUPERVISED = ["his11", "lr", "single", "m1_raw11", "lr_bsp", "m1_bsp", "m2_bsp"]
ONE_CLASS = ["if_raw11", "if_bsp", "ae_bsp"]
RAW11_KINDS = {"his11", "lr", "single", "m1_raw11"}


def cfgs():
    D = yaml.safe_load(open(ROOT / "configs" / "stage_d.yaml"))
    sc = yaml.safe_load(open(ROOT / "configs" / "stage_c.yaml"))
    syn = yaml.safe_load(open(ROOT / "configs" / "synth.yaml"))          # v1 params == v2 params
    spl = yaml.safe_load(open(ROOT / "configs" / "split.yaml"))
    return D, sc, syn, spl


class Pipe:
    """Feature pipeline carried with the model: raw 11 columns (+ his clip cap) or bsp_v1."""

    def __init__(self, feat: str, cap=None):
        self.feat = feat
        self.prep = Prep("coded11", cap) if feat == "raw11" else None
        self.scaler = StandardScaler() if feat == "bsp" else None

    def fit(self, df):
        if self.feat == "raw11":
            return self.prep.fit(df)
        return self.scaler.fit_transform(build_bsp(df).to_numpy(float))

    def transform(self, df):
        if self.feat == "raw11":
            return self.prep.transform(df)
        return self.scaler.transform(build_bsp(df).to_numpy(float))


class Scorer:
    def __init__(self, pipe, est, thr, info, prob):
        self.pipe, self.est, self.thr, self.info, self.prob = pipe, est, thr, info, prob

    def score(self, df):
        X = self.pipe.transform(df)
        return self.est.score(X) if hasattr(self.est, "score") else self.est.predict_proba(X)


def _thr(p_val, yva, his_rule, mcfg, with_attacks=True):
    s_n = p_val[yva == 0]
    t = {"fpr": float(np.quantile(s_n, 1 - mcfg["fpr_targets"][0])),
         "fpr01": float(np.quantile(s_n, 1 - mcfg["fpr_targets"][1]))}
    if with_attacks:
        t["main"] = his_rule
        t["rec"] = float(np.quantile(p_val[yva == 1], 1 - mcfg["recall_target"]))
    else:
        t["main"], t["rec"] = t["fpr"], float("nan")
    return t


def fit_supervised(kind, src, data, seed, D, sc):
    feat = "bsp" if kind.endswith("_bsp") else "raw11"
    use_his_norm = src == "H" and feat == "raw11"
    cap = data["cap"] if use_his_norm else None
    (trn, atr), (van, ava) = data["train"][src], data["val"][src]
    trn = data["tr_noisy"] if use_his_norm else trn
    df_tr, ytr = _frame(trn, atr); df_va, yva = _frame(van, ava)
    pipe = Pipe(feat, cap)
    Xtr, Xva = pipe.fit(df_tr), pipe.transform(df_va)
    info, prob = {}, True
    if kind == "his11":
        est = HisEnsemble(sc["his"], seed).fit(Xtr, ytr, Xva, yva)
    elif kind in ("lr", "lr_bsp"):
        est = LogReg().fit(Xtr, ytr)
    elif kind == "single":
        est = BestSingleFeature().fit(Xtr, ytr); prob = False
        info = {"feature": FEATURES[est.j], "train_auc": est.auc}
    elif kind in ("m1_raw11", "m1_bsp"):
        best, tinfo = tune_xgb(Xtr, ytr, Xva, yva, D["m1"], D["honest"], seed)
        est = XgbModel(best, seed, D["m1"]["early_stopping_rounds"]).fit(Xtr, ytr, Xva, yva)
        info = {"tuned": best, **tinfo}
        data.setdefault("tuned", {})[(kind, src)] = best
    elif kind == "m2_bsp":
        b = data["tuned"][("m1_bsp", src)]                       # same imbalance mechanism as M1 chose
        est = FTTModel(D["m2"], b["imbalance"], b["focal_gamma"], b["focal_alpha"], seed).fit(Xtr, ytr, Xva, yva)
    else:
        raise ValueError(kind)
    info = {**getattr(est, "info", {}), **info}
    p_val = est.predict_proba(Xva)
    thr = _thr(p_val, yva, his_threshold(yva, p_val, sc["his"]["recall_min"]), D["metrics"])
    return Scorer(pipe, est, thr, info, prob)


def fit_one_class(kind, data, seed, D):
    """Trained on the training side's NORMALS only (no attacks, no source)."""
    tr, va = data["tr"], data["va"]
    if kind == "if_raw11":
        sc_ = RobustScaler().fit(tr[FEATURES]); tf = lambda d: sc_.transform(d[FEATURES])
        est = IForest(D["m4"]["iforest"]["n_estimators"], seed).fit(tf(tr)); pipe = None
        score = lambda d: est.score(tf(d))
        info = {}
    elif kind == "if_bsp":
        tf = lambda d: build_bsp(d).to_numpy(float)
        est = IForest(D["m4"]["iforest"]["n_estimators"], seed).fit(tf(tr)); score = lambda d: est.score(tf(d)); info = {}
    else:
        ss = StandardScaler().fit(build_bsp(tr).to_numpy(float)); tf = lambda d: ss.transform(build_bsp(d).to_numpy(float))
        est = AutoEncoder(D["m4"]["ae"], seed).fit(tf(tr), tf(va)); score = lambda d: est.score(tf(d)); info = est.info
    s_va = score(va)
    t = {"fpr": float(np.quantile(s_va, 1 - D["metrics"]["fpr_targets"][0])),
         "fpr01": float(np.quantile(s_va, 1 - D["metrics"]["fpr_targets"][1]))}
    t["main"], t["rec"] = t["fpr"], float("nan")

    class _S:                                          # thin scorer with the same interface
        pass
    s = _S(); s.score = score; s.thr = t; s.info = info; s.prob = False
    return s


def run_job(reading: str, fold_group: str, seed: int) -> dict:
    import torch
    torch.set_num_threads(1)
    D, sc, syn, spl = cfgs()
    a, _ = load_normals("A"); b, _ = load_normals("B")
    proto = build_protocol(a, b)
    dev = proto["readings"][reading]["dev"]                         # DEV ONLY
    assert not set(dev["group"]) & set(proto["test_groups"])
    ev = dev[dev["group"] == fold_group].reset_index(drop=True)
    side = dev[dev["group"] != fold_group].reset_index(drop=True)
    tr, va, inner = split_inner(side, spl["min_fold_rows"], D["honest"]["inner_val_random_frac"], seed)
    ho = D["generator"]["heldout_family"]
    rt, re_ = D["honest"]["train_attack_ratio"], D["honest"]["eval_attack_ratio"]
    fit = his_fit(tr)
    gen = lambda base, ratio, sd, v, **kw: generate_for_groups(base, syn, ratio, sd, version=v, **kw)
    ex = {"exclude_families": (ho,)}
    A = {"H": {"tr": his_attacks(round(rt * len(tr)), fit, np.random.default_rng(seed * 100 + 4)),
               "va": his_attacks(round(rt * len(va)), fit, np.random.default_rng(seed * 100 + 5))}}
    for src, v in (("R1", 1), ("R2", 2)):
        A[src] = {"tr": gen(tr, rt, seed * 100 + 1, v, **ex), "va": gen(va, rt, seed * 100 + 2, v, **ex)}
    E = {"EH": his_attacks(round(re_ * len(ev)), fit, np.random.default_rng(seed * 100 + 6)),
         "ER1": gen(ev, re_, seed * 100 + 3, 1, **ex), "ER2": gen(ev, re_, seed * 100 + 3, 2, **ex),
         "EHO": generate_for_groups(ev, syn, re_, seed * 100 + 9, version=2, family=ho)}
    assert not (set(A["R1"]["tr"]["family"]) | set(A["R2"]["tr"]["family"]) | set(A["R1"]["va"]["family"]) |
                set(A["R2"]["va"]["family"])) & {ho}, "held-out family leaked into training"
    data = {"cap": fit["cap"], "tr": tr, "va": va,
            "tr_noisy": his_normal_noise(his_clip(tr, fit), fit, np.random.default_rng(seed * 100 + 7)),
            "train": {s: (tr, A[s]["tr"]) for s in A}, "val": {s: (va, A[s]["va"]) for s in A}}
    reg_ev = regime(ev).to_numpy()
    out = {"reading": reading, "fold": fold_group, "seed": seed, "inner_val": inner,
           "sizes": {"train_norm": len(tr), "val_norm": len(va), "eval_norm": len(ev),
                     "train_att": {s: len(A[s]["tr"]) for s in A}, "eval_att": {k: len(v) for k, v in E.items()},
                     "eval_counts_only_normals": int((reg_ev == "U0").sum())},
           "eval": {}, "sweep": {}, "info": {}}
    t0 = time.time()
    scorers = {}
    for src in D["sources"]:
        order = ["his11", "lr", "single", "lr_bsp", "m1_raw11", "m1_bsp", "m2_bsp"]   # m2 needs m1_bsp's mechanism
        for kind in order:
            scorers[(kind, src)] = fit_supervised(kind, src, data, seed, D, sc)
    for kind in ONE_CLASS:
        scorers[(kind, "none")] = fit_one_class(kind, data, seed, D)
    out["fit_seconds"] = round(time.time() - t0, 1)
    sweep_specs = [(f, st, f, 2) for f in D["sweep"]["families"] for st in D["sweep"]["strengths"]]
    sweep_specs += [("network_only", st, "network_only_v1", 1) for st in D["sweep"]["strengths"]]
    cells_df = {}
    for fam, st, key, ver in sweep_specs:
        att = generate(ev, D["sweep"]["n_per_cell"], syn, seed * 100 + 8, family=fam, strength=st,
                       keep_unchanged=True, version=ver)
        if len(att):
            cells_df[(key, st)] = att
    for (kind, src), scr in scorers.items():
        s_norm = scr.score(ev[FEATURES])
        out["info"][(kind, src)] = {**scr.info, "thr": scr.thr, "prob": scr.prob}
        for ek, att in E.items():
            y = np.r_[np.zeros(len(ev), int), np.ones(len(att), int)]
            s = np.r_[s_norm, scr.score(att[FEATURES])] if len(att) else s_norm
            fam = np.r_[np.full(len(ev), "norm"), att["family"].to_numpy() if "family" in att else np.full(len(att), "his")]
            out["eval"][(kind, src, ek)] = {"y": y, "s": s, "reg": np.r_[reg_ev, np.full(len(att), "att")], "fam": fam}
        out["sweep"][(kind, src)] = {"s_norm": s_norm, "thr": scr.thr,
                                     "cells": {k: scr.score(v[FEATURES]) for k, v in cells_df.items()}}
    return out


def _job(args):
    t0 = time.time()
    res = run_job(*args)
    RAW.mkdir(parents=True, exist_ok=True)
    name = "_".join(map(str, args))
    with open(RAW / f"{name}.pkl", "wb") as fh:
        pickle.dump(res, fh)
    return name, round(time.time() - t0, 1)


if __name__ == "__main__":
    D, sc, syn, spl = cfgs()
    a, _ = load_normals("A"); b, _ = load_normals("B")
    proto = build_protocol(a, b)
    jobs = [(r, g, sd) for r in D["readings"] for g in proto["readings"][r]["val_groups"] for sd in D["seeds"]]
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
                print("FAILED", futs[f], repr(e), traceback.format_exc()[-600:], flush=True)
