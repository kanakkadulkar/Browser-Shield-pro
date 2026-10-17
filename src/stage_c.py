"""Stage C jobs: his recipe (reproduction of the described method) + trivial baselines.

Honest-protocol job  = one (reading, validation group, seed): train on the other dev groups,
evaluate on the held-out group. DEV DATA ONLY: the locked test groups are never read.
His-protocol job     = one (reading, seed): his data, his generator, random 70/15/15, no dedupe.

Per honest job, two training sources are fitted per model:
  H = his tiered generator   R = rebuilt generator (src/synth.py)
and every fitted model is scored on both evaluation sets (EH, ER): this yields conditions 2, 3
and the cross-generator transfer 4a (H->ER), 4b (R->EH) from the same fits.
"""
from __future__ import annotations

import os
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

from .baselines import BestSingleFeature, LogReg
from .data import ROOT, UNKNOWN, load_config, load_normals
from .features import FEATURES
from .hisrecipe import (HisEnsemble, Prep, his_attacks, his_clip, his_fit, his_normal_noise,
                        his_threshold)
from .metrics import predictions, prevalence_weights, thresholds_from_validation
from .splits import build_protocol
from .synth import generate, generate_for_groups

KINDS = ["his11", "his18", "lr", "single"]
STAGEC_DIR = os.environ.get("STAGEC_DIR", "stage_c")      # v1 (default) or e.g. stage_c_v2
RAW = ROOT / "reports" / STAGEC_DIR / "raw"


def cfg_all():
    sc = yaml.safe_load(open(ROOT / "configs" / "stage_c.yaml"))
    syn = yaml.safe_load(open(ROOT / "configs" / "synth.yaml"))
    if os.environ.get("GEN_VERSION") == "2":                     # generator v2 (counts-only uptime fix)
        syn["version"] = 2
    return sc, syn, load_config("split")


class Scorer:
    """A fitted model plus its own preprocessing and its validation-derived thresholds."""

    def __init__(self, prep, est, thr, info):
        self.prep, self.est, self.thr, self.info = prep, est, thr, info

    def score(self, df: pd.DataFrame) -> np.ndarray:
        return self.est.predict_proba(self.prep.transform(df))


def fit_scorer(kind, cap, tr_df, ytr, va_df, yva, seed, sc) -> Scorer:
    mode = "described18" if kind == "his18" else "coded11"
    prep = Prep(mode, cap)
    Xtr, Xva = prep.fit(tr_df), prep.transform(va_df)
    if kind in ("his11", "his18"):
        est = HisEnsemble(sc["his"], seed).fit(Xtr, ytr, Xva, yva)
    elif kind == "lr":
        est = LogReg().fit(Xtr, ytr)
    else:
        est = BestSingleFeature().fit(Xtr, ytr)
    p_val = est.predict_proba(Xva)
    m = sc["metrics"]
    thr = thresholds_from_validation(p_val, np.asarray(yva), his_threshold(yva, p_val, sc["his"]["recall_min"]),
                                     m["fpr_target"], m["recall_target"])
    info = dict(getattr(est, "info", {}))
    if kind == "single":
        info.update(feature=FEATURES[est.j], train_auc=est.auc)
    return Scorer(prep, est, thr, info)


def _frame(norm: pd.DataFrame, att: pd.DataFrame):
    df = pd.concat([norm[FEATURES], att[FEATURES]], ignore_index=True)
    y = np.r_[np.zeros(len(norm), int), np.ones(len(att), int)]
    return df, y


def split_inner(side: pd.DataFrame, min_rows: int, frac: float, seed: int):
    """Inner validation (early stopping + thresholds): the smallest remaining group with >= min_rows
    when at least two such groups remain on the training side; otherwise a random fraction."""
    sizes = side["group"].value_counts()
    cand = sorted([g for g, n in sizes.items() if n >= min_rows], key=lambda g: (sizes[g], g))
    if len(cand) >= 2:
        v = side["group"] == cand[0]
        return side[~v].reset_index(drop=True), side[v].reset_index(drop=True), f"group:{cand[0]}"
    rng = np.random.default_rng(seed)
    v = rng.random(len(side)) < frac
    return side[~v].reset_index(drop=True), side[v].reset_index(drop=True), "random"


def run_honest_job(reading: str, fold_group: str, seed: int) -> dict:
    import torch
    torch.set_num_threads(1)
    sc, syn, scfg = cfg_all()
    a, _ = load_normals("A"); b, _ = load_normals("B")
    proto = build_protocol(a, b)
    dev = proto["readings"][reading]["dev"]            # DEV ONLY; test frame is never touched
    assert not set(dev["group"]) & set(proto["test_groups"])
    ev = dev[dev["group"] == fold_group].reset_index(drop=True)
    side = dev[dev["group"] != fold_group].reset_index(drop=True)
    tr, va, inner = split_inner(side, scfg["min_fold_rows"], sc["honest"]["inner_val_random_frac"], seed)
    fit = his_fit(tr)                                   # his generator parameters from TRAIN normals only
    rt, re_ = sc["his"]["attack_fraction"], sc["honest"]["eval_attack_ratio"]
    R = {"tr": generate_for_groups(tr, syn, rt, seed * 100 + 1), "va": generate_for_groups(va, syn, rt, seed * 100 + 2),
         "ev": generate_for_groups(ev, syn, re_, seed * 100 + 3)}
    H = {"tr": his_attacks(round(rt * len(tr)), fit, np.random.default_rng(seed * 100 + 4)),
         "va": his_attacks(round(rt * len(va)), fit, np.random.default_rng(seed * 100 + 5)),
         "ev": his_attacks(round(re_ * len(ev)), fit, np.random.default_rng(seed * 100 + 6))}
    # his pipeline: clip at train p99 (applied by Prep at inference too), noise on TRAIN normals only
    tr_noisy = his_normal_noise(his_clip(tr, fit), fit, np.random.default_rng(seed * 100 + 7))
    train_sets = {"H": (_frame(tr_noisy, H["tr"]), _frame(va, H["va"]), fit["cap"]),
                  "R": (_frame(tr, R["tr"]), _frame(va, R["va"]), None)}
    eval_sets = {"EH": _frame(ev, H["ev"]), "ER": _frame(ev, R["ev"])}
    out = {"reading": reading, "fold": fold_group, "seed": seed, "inner_val": inner,
           "sizes": {"train_norm": len(tr), "val_norm": len(va), "eval_norm": len(ev),
                     "train_att": {k: len(v["tr"]) for k, v in (("H", H), ("R", R))},
                     "eval_att": {"EH": len(H["ev"]), "ER": len(R["ev"])}},
           "eval": {}, "sweep": {}, "info": {}}
    scorers = {}
    t0 = time.time()
    for src, ((trdf, ytr), (vadf, yva), cap) in train_sets.items():
        for kind in KINDS:
            scorers[(kind, src)] = fit_scorer(kind, cap, trdf, ytr, vadf, yva, seed, sc)
            out["info"][(kind, src)] = {**scorers[(kind, src)].info, "thr": scorers[(kind, src)].thr}
    out["fit_seconds"] = round(time.time() - t0, 1)
    for (kind, src), scr in scorers.items():
        s_norm = scr.score(ev[FEATURES])
        for ek, (edf, y) in eval_sets.items():
            s = np.r_[s_norm, scr.score(edf.iloc[len(ev):])]
            out["eval"][(kind, src, ek)] = {"y": y, "s": s, "w": prevalence_weights(y, sc["honest"]["prevalence"]),
                                            "preds": predictions(s, scr.thr)}
        # effect-size sweep: SIMULATED miner signal, ASSUMED effect sizes
        sw = {"s_norm": s_norm, "thr": scr.thr, "cells": {}}
        for fam in sc["sweep"]["families"]:
            for st in sc["sweep"]["strengths"]:
                att = generate(ev, sc["sweep"]["n_per_cell"], syn, seed * 100 + 8, family=fam,
                               strength=st, keep_unchanged=True)
                if len(att):
                    sw["cells"][(fam, st)] = scr.score(att[FEATURES])
        out["sweep"][(kind, src)] = sw
    return out


def run_his_protocol_job(reading: str, seed: int) -> dict:
    """His headline setup, applied to the DEV portion of his data: random 70/15/15, no dedupe,
    clip/noise/scaler fitted on ALL rows before splitting (as in his notebook)."""
    import torch
    torch.set_num_threads(1)
    sc, _, _ = cfg_all()
    a_d, _ = load_normals("A"); b_d, _ = load_normals("B")
    proto = build_protocol(a_d, b_d)
    nd, st = load_normals(reading, dedupe=False)
    nd = nd[~nd["group"].isin(proto["test_groups"])].reset_index(drop=True)
    rng = np.random.default_rng(seed)
    fit = his_fit(nd)
    clipped = his_clip(nd, fit)
    noisy = his_normal_noise(clipped, fit, rng, sc["his"]["normal_noise"])
    att = his_attacks(round(sc["his"]["attack_fraction"] * len(nd)), fit, rng, sc["his"]["attack_noise"],
                      tuple(sc["his"]["tier_split"]))
    df, y = _frame(noisy, att)
    df["_y"] = y
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    y = df.pop("_y").to_numpy()
    sp = sc["his"]["split"]
    i_tr, i_tmp = train_test_split(np.arange(len(df)), test_size=sp["val"] + sp["test"], random_state=seed, stratify=y)
    i_va, i_te = train_test_split(i_tmp, test_size=sp["test"] / (sp["val"] + sp["test"]), random_state=seed, stratify=y[i_tmp])
    out = {"reading": reading, "seed": seed, "n_normals_dev_rows_no_dedupe": len(nd),
           "sizes": {"train": len(i_tr), "val": len(i_va), "test": len(i_te)},
           "test_pos": int(y[i_te].sum()), "eval": {}, "info": {}}
    for kind in KINDS:
        mode = "described18" if kind == "his18" else "coded11"
        prep = Prep(mode, None)
        X_all = prep.fit(df)                       # scaler fitted on ALL rows, as he did (leak kept on purpose)
        if kind in ("his11", "his18"):
            est = HisEnsemble(sc["his"], seed).fit(X_all[i_tr], y[i_tr], X_all[i_va], y[i_va])
        elif kind == "lr":
            est = LogReg().fit(X_all[i_tr], y[i_tr])
        else:
            est = BestSingleFeature().fit(X_all[i_tr], y[i_tr])
        p_va = est.predict_proba(X_all[i_va]); p_te = est.predict_proba(X_all[i_te])
        m = sc["metrics"]
        thr = thresholds_from_validation(p_va, y[i_va], his_threshold(y[i_va], p_va, sc["his"]["recall_min"]),
                                         m["fpr_target"], m["recall_target"])
        out["eval"][(kind, "HIS", "TEST")] = {"y": y[i_te], "s": p_te, "w": np.ones(len(i_te)),
                                              "preds": predictions(p_te, thr)}
        out["info"][(kind, "HIS")] = {**getattr(est, "info", {}), "thr": thr}
    return out


def _job(args):
    kind, a = args
    t0 = time.time()
    res = run_honest_job(*a) if kind == "honest" else run_his_protocol_job(*a)
    name = "_".join([kind, *map(str, a)]).replace("/", "-")
    RAW.mkdir(parents=True, exist_ok=True)
    with open(RAW / f"{name}.pkl", "wb") as fh:
        pickle.dump(res, fh)
    return name, round(time.time() - t0, 1)


def job_list(sc, only_fold: str | None = None, seeds=None):
    a, _ = load_normals("A"); b, _ = load_normals("B")
    proto = build_protocol(a, b)
    jobs = []
    for r in sc["readings"]:
        for sd in (seeds or sc["seeds"]):
            jobs.append(("his", (r, sd)))
            for g in proto["readings"][r]["val_groups"]:
                if only_fold is None or g == only_fold:
                    jobs.append(("honest", (r, g, sd)))
    return jobs


if __name__ == "__main__":
    sc, _, _ = cfg_all()
    n_workers = int(os.environ.get("WORKERS", max(1, (os.cpu_count() or 2) - 1)))
    jobs = [j for j in job_list(sc) if not (RAW / ("_".join([j[0], *map(str, j[1])]) + ".pkl")).exists()]
    print(f"{len(jobs)} jobs, {n_workers} workers", flush=True)
    import multiprocessing as mp
    with ProcessPoolExecutor(n_workers, mp_context=mp.get_context("spawn")) as ex:
        futs = {ex.submit(_job, j): j for j in jobs}
        for f in as_completed(futs):
            try:
                print("done", *f.result(), flush=True)
            except Exception as e:  # keep going; report at the end
                print("FAILED", futs[f], repr(e), flush=True)
