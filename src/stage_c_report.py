"""Aggregate Stage C raw results -> tables, bootstrap CIs, sweep curves, figures.

Reads reports/stage_c/raw/*.pkl (written by src/stage_c.py). Never touches the locked test set.
"""
from __future__ import annotations

import glob
import json
import multiprocessing as mp
import pickle
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

import matplotlib
import numpy as np
import pandas as pd

from .data import ROOT, load_normals
from .features import FEATURES
from .metrics import METRIC_NAMES, bootstrap, prevalence_weights
from .stage_c import KINDS, cfg_all
from .splits import build_protocol

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import os
OUT = ROOT / "reports" / os.environ.get("STAGEC_DIR", "stage_c")
COND = {"C1": ("HIS", "TEST"), "C2": ("H", "EH"), "C3": ("R", "ER"), "C4a": ("H", "ER"), "C4b": ("R", "EH")}
COND_LABEL = {"C1": "1. His protocol (his data + generator, random split, no dedupe)",
              "C2": "2. Honest protocol, his generator", "C3": "3. Honest protocol, rebuilt generator",
              "C4a": "4a. Train his generator -> test rebuilt", "C4b": "4b. Train rebuilt -> test his generator"}
KIND_LABEL = {"his11": "His recipe, as coded (11 features)", "his18": "His recipe, as described (18 features)",
              "lr": "Logistic regression", "single": "Best single feature"}


def load_raw():
    honest, his = [], []
    for f in sorted(glob.glob(str(OUT / "raw" / "*.pkl"))):
        r = pickle.load(open(f, "rb"))
        (honest if "fold" in r else his).append(r)
    return honest, his


def pooled_runs(honest, his, reading, cond, kind):
    """One pooled run dict per seed (folds concatenated for the honest conditions)."""
    src, ek = COND[cond]
    runs = []
    if cond == "C1":
        for r in sorted((r for r in his if r["reading"] == reading), key=lambda r: r["seed"]):
            runs.append(r["eval"][(kind, src, ek)])
        return runs
    for seed in sorted({r["seed"] for r in honest}):
        parts = [r["eval"][(kind, src, ek)] for r in honest if r["reading"] == reading and r["seed"] == seed]
        runs.append({"y": np.concatenate([p["y"] for p in parts]), "s": np.concatenate([p["s"] for p in parts]),
                     "w": np.concatenate([p["w"] for p in parts]),
                     "preds": {k: np.concatenate([p["preds"][k] for p in parts]) for k in parts[0]["preds"]}})
    return runs


def _boot_task(args):
    key, runs, reps, seed = args
    return key, bootstrap(runs, reps, seed)


def fmt(t, d=3):
    m, lo, hi = t
    return f"{m:.{d}f} [{lo:.{d}f}, {hi:.{d}f}]"


def main_tables(honest, his, sc):
    tasks = []
    for reading in sc["readings"]:
        for cond in COND:
            for kind in KINDS:
                tasks.append(((reading, cond, kind), pooled_runs(honest, his, reading, cond, kind),
                              sc["metrics"]["bootstrap_reps"], sc["metrics"]["bootstrap_seed"]))
    res = {}
    with ProcessPoolExecutor(9, mp_context=mp.get_context("spawn")) as ex:
        for key, b in ex.map(_boot_task, tasks):
            res[key] = b
    return res


def per_fold(honest, sc, reading):
    from .metrics import compute
    rows = []
    for cond in ("C2", "C3", "C4a", "C4b"):
        src, ek = COND[cond]
        for kind in ("his11", "lr", "single"):
            for fold in sorted({r["fold"] for r in honest if r["reading"] == reading}):
                ms = []
                for r in honest:
                    if r["reading"] == reading and r["fold"] == fold:
                        e = r["eval"][(kind, src, ek)]
                        ms.append(compute(e["y"], e["s"], e["w"], e["preds"]))
                sz = next(r for r in honest if r["reading"] == reading and r["fold"] == fold)["sizes"]
                rows.append({"cond": cond, "kind": kind, "fold": fold, "n_norm": sz["eval_norm"],
                             "n_att": sz["eval_att"][ek], **{k: float(np.nanmean([m[k] for m in ms])) for k in
                                                              ("f1", "recall", "fpr", "pr_auc", "recall_at_fpr1", "realised_fpr_at_fpr1")}})
    return pd.DataFrame(rows)


def eff_size(sc_syn, fam, s):
    p = sc_syn["families"][fam]
    out = {}
    for k in ("d_lag", "pool_per_min"):
        lo, hi = p[k]
        out[k] = 0.0 if hi == lo == 0 else (lo * (hi / lo) ** s if lo > 0 else hi * s)
    return out


def sweep_tables(honest, sc, syn, reading):
    """Pooled across folds, averaged over seeds. Returns long DataFrame."""
    from sklearn.metrics import average_precision_score
    cfg_s = sc["sweep"]; prev = sc["honest"]["prevalence"]
    rng = np.random.default_rng(sc["metrics"]["bootstrap_seed"])
    rows = []
    plot_models = [("his11", "R"), ("his11", "H"), ("lr", "R"), ("single", "R")]
    for (kind, src) in plot_models:
        for fam in cfg_s["families"]:
            for st in cfg_s["strengths"]:
                per_seed = []
                for seed in sorted({r["seed"] for r in honest}):
                    h_att, h_n, s_att, s_n = [], [], [], []
                    for r in honest:
                        if r["reading"] != reading or r["seed"] != seed:
                            continue
                        sw = r["sweep"][(kind, src)]
                        if (fam, st) not in sw["cells"]:
                            continue
                        a = sw["cells"][(fam, st)]
                        h_att.append(a > sw["thr"]["fpr"]); h_n.append(sw["s_norm"] > sw["thr"]["fpr"])
                        s_att.append(a); s_n.append(sw["s_norm"])
                    if h_att:
                        per_seed.append((np.concatenate(h_att), np.concatenate(h_n), np.concatenate(s_att), np.concatenate(s_n)))
                if not per_seed:
                    continue
                def metrics(sel):
                    rec = np.mean([ha[sel[i][0]].mean() for i, (ha, *_r) in enumerate(per_seed)])
                    fpr = np.mean([hn[sel[i][1]].mean() for i, (_a, hn, *_r) in enumerate(per_seed)])
                    return rec, fpr
                full = [(np.arange(len(p[0])), np.arange(len(p[1]))) for p in per_seed]
                rec, fpr = metrics(full)
                def ap(sel):
                    v = []
                    for i, (_ha, _hn, sa, sn) in enumerate(per_seed):
                        y = np.r_[np.zeros(len(sel[i][1])), np.ones(len(sel[i][0]))].astype(int)
                        s = np.r_[sn[sel[i][1]], sa[sel[i][0]]]
                        v.append(average_precision_score(y, s, sample_weight=prevalence_weights(y, prev)))
                    return np.mean(v)
                prauc = ap(full)
                rb, pb, fb = [], [], []
                for b in range(150):
                    sel = [(rng.choice(len(p[0]), len(p[0])), rng.choice(len(p[1]), len(p[1]))) for p in per_seed]
                    r_, f_ = metrics(sel); rb.append(r_); fb.append(f_)
                    if b < 60:
                        pb.append(ap(sel))
                rows.append({"kind": kind, "src": src, "family": fam, "s": st, "recall_at_fpr1": rec,
                             "recall_lo": np.quantile(rb, .025), "recall_hi": np.quantile(rb, .975),
                             "realised_fpr": fpr, "pr_auc": prauc, "pr_lo": np.quantile(pb, .025),
                             "pr_hi": np.quantile(pb, .975), **eff_size(syn, fam, st)})
    return pd.DataFrame(rows)


def sweep_figure(df, path, metric, ylabel, title):
    fams = list(df["family"].unique())
    fig, axes = plt.subplots(1, len(fams), figsize=(4.2 * len(fams), 3.9), sharey=True)
    style = {("his11", "R"): ("#1f77b4", "-", "his recipe, trained on rebuilt"),
             ("his11", "H"): ("#d62728", "--", "his recipe, trained on his generator"),
             ("lr", "R"): ("#2ca02c", "-", "logistic regression (rebuilt)"),
             ("single", "R"): ("#7f7f7f", ":", "best single feature (rebuilt)")}
    lo_c, hi_c = ("recall_lo", "recall_hi") if metric == "recall_at_fpr1" else ("pr_lo", "pr_hi")
    for ax, fam in zip(axes, fams):
        for (k, s_), (c, ls, lab) in style.items():
            d = df[(df.family == fam) & (df.kind == k) & (df.src == s_)].sort_values("s")
            ax.plot(d["s"], d[metric], color=c, ls=ls, marker="o", ms=3, label=lab)
            ax.fill_between(d["s"], d[lo_c], d[hi_c], color=c, alpha=0.12)
        ax.axvspan(0, 1, color="k", alpha=0.04); ax.set_title(fam); ax.set_xlabel("signal strength s (shaded = standard range)")
        ax.set_ylim(-0.02, 1.02); ax.grid(alpha=0.3)
    axes[0].set_ylabel(ylabel)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, fontsize=8)
    fig.suptitle(title + "  [simulated miner signal, assumed effect sizes]", fontsize=10)
    fig.tight_layout(rect=(0, 0.08, 1, 0.94)); fig.savefig(path, dpi=130); plt.close(fig)


def onset_table(df, sc):
    thr = sc["sweep"]["works_threshold"]
    rows = []
    for (kind, src, fam), d in df.groupby(["kind", "src", "family"]):
        d = d.sort_values("s")
        ok = d[d["recall_at_fpr1"] >= thr]
        first = ok["s"].min() if len(ok) else None
        top = d.iloc[-1]; floor = d.iloc[0]
        rows.append({"kind": kind, "src": src, "family": fam, "weakest_s_working": first,
                     "d_lag_at_onset": (float(ok.iloc[0]["d_lag"]) if len(ok) else None),
                     "pool_per_min_at_onset": (float(ok.iloc[0]["pool_per_min"]) if len(ok) else None),
                     "recall_at_strongest": float(top["recall_at_fpr1"]), "recall_at_weakest": float(floor["recall_at_fpr1"]),
                     "realised_fpr_at_weakest": float(floor["realised_fpr"])})
    return pd.DataFrame(rows)


def his_generator_artefacts(sc):
    """Stage-B-style adversarial check of HIS tiered generator (dev data only)."""
    from .adversarial import evaluate, structure_report
    from .hisrecipe import his_attacks, his_fit
    a, _ = load_normals("A"); b, _ = load_normals("B")
    proto = build_protocol(a, b)
    out = {}
    for r in ("A", "B"):
        dev, vg = proto["readings"][r]["dev"], proto["readings"][r]["val_groups"]
        att = his_attacks(round(0.25 * len(dev)), his_fit(dev), np.random.default_rng(42))
        sizes = dev["group"].value_counts(); w = np.array([sizes[g] for g in vg], float)
        grp = np.random.default_rng(42).choice(vg, len(att), p=w / w.sum())
        att["group"] = grp
        ev = evaluate(dev, att, vg, 42)
        st = structure_report(dev, {"his_tiered": att})
        out[r] = {"auc_all": ev["auc_all"], "auc_non_signal_only": ev["auc_non_signal_only"],
                  "best_single": max(((f, v["oof_tree_auc"]) for f, v in ev["single_feature"].items()), key=lambda t: t[1]),
                  "structure": st["his_tiered"], "real_structure": st["real_normal"]}
    return out


def planned_test_counts():
    a, _ = load_normals("A"); b, _ = load_normals("B")
    p = build_protocol(a, b)
    t = p["readings"]["A"]["test"]
    prev = 0.0835
    return [{"test_group_rank_in_reading_A": [2, 4][i], "normals": int(n), "attacks_at_prevalence": round(prev / (1 - prev) * n),
             "attacks_at_eval_ratio_0.25": round(0.25 * n)} for i, n in enumerate(t["group"].value_counts().sort_values(ascending=False).tolist())]


def main():
    sc, syn, _ = cfg_all()
    honest, his = load_raw()
    print(f"{len(honest)} honest jobs, {len(his)} his-protocol jobs", flush=True)
    res = main_tables(honest, his, sc)
    ser = {f"{k[0]}|{k[1]}|{k[2]}": {m: list(v) for m, v in b.items()} for k, b in res.items()}
    (OUT / "main_results.json").write_text(json.dumps(ser, indent=1))
    infos = []
    for r in honest + his:
        for k, v in r["info"].items():
            if "epochs_run" in v:
                infos.append({"reading": r["reading"], "kind": k[0], "src": k[1], "seed": r["seed"], "epochs": v["epochs_run"],
                              "early_stopped": v["early_stopped_at"] is not None})
    pd.DataFrame(infos).to_csv(OUT / "training_epochs.csv", index=False)
    singles = defaultdict(list)
    for r in honest + his:
        for k, v in r["info"].items():
            if k[0] == "single":
                if "feature" in v:
                    singles[(r["reading"], k[1])].append(v["feature"])
    L = []
    for reading in sc["readings"]:
        L.append(f"\n### Reading {reading}: at his threshold rule (max F1 s.t. val recall >= 0.97)\n")
        L.append("| Condition | Model | Precision | Recall | F1 | FPR |\n|---|---|---|---|---|---|")
        for cond in COND:
            for kind in KINDS:
                b = res[(reading, cond, kind)]
                L.append(f"| {COND_LABEL[cond]} | {KIND_LABEL[kind]} | " + " | ".join(fmt(b[m]) for m in ("precision", "recall", "f1", "fpr")) + " |")
        L.append(f"\n### Reading {reading}: threshold-free and fixed operating points\n")
        L.append("| Condition | Model | ROC-AUC | PR-AUC (prev 8.35%) | Recall @ FPR<=1% (realised FPR) | FPR @ recall~95% (realised recall) |\n|---|---|---|---|---|---|")
        for cond in COND:
            for kind in KINDS:
                b = res[(reading, cond, kind)]
                L.append(f"| {COND_LABEL[cond]} | {KIND_LABEL[kind]} | {fmt(b['roc_auc'])} | {fmt(b['pr_auc'])} | "
                         f"{fmt(b['recall_at_fpr1'])} ({b['realised_fpr_at_fpr1'][0]:.3f}) | {fmt(b['fpr_at_recall95'])} ({b['realised_recall_at_rec95'][0]:.3f}) |")
    for reading in sc["readings"]:
        pf = per_fold(honest, sc, reading)
        pf.to_csv(OUT / f"per_fold_{reading}.csv", index=False)
        L.append(f"\n### Reading {reading}: per validation group (mean over seeds)\n")
        L.append("| Cond | Model | Group | Eval normals | Eval attacks | F1 | Recall | FPR | PR-AUC | Recall@1%FPR (realised FPR) |\n|---|---|---|---|---|---|---|---|---|---|")
        for _, r in pf.iterrows():
            L.append(f"| {r.cond} | {KIND_LABEL[r.kind]} | {r.fold[:6]} | {r.n_norm} | {r.n_att} | {r.f1:.3f} | {r.recall:.3f} | {r.fpr:.3f} | {r.pr_auc:.3f} | {r.recall_at_fpr1:.3f} ({r.realised_fpr_at_fpr1:.3f}) |")
    L.append("\n### Best single feature chosen\n")
    for k, v in singles.items():
        L.append(f"- reading {k[0]}, trained on {k[1]}: " + ", ".join(f"{f} x{n}" for f, n in pd.Series(v).value_counts().items()))
    sweeps = {}
    for reading in sc["readings"]:
        sw = sweep_tables(honest, sc, syn, reading)
        sw.to_csv(OUT / f"sweep_{reading}.csv", index=False)
        on = onset_table(sw, sc); on.to_csv(OUT / f"sweep_onset_{reading}.csv", index=False)
        sweep_figure(sw, OUT / f"sweep_recall_{reading}.png", "recall_at_fpr1", "recall at FPR<=1% (threshold from validation)", f"Reading {reading}: detection vs signal strength")
        sweep_figure(sw, OUT / f"sweep_prauc_{reading}.png", "pr_auc", "PR-AUC (prevalence 8.35%)", f"Reading {reading}: PR-AUC vs signal strength")
        sweeps[reading] = on
        L.append(f"\n### Reading {reading}: effect-size sweep, where each model stops working (recall@1%FPR >= {sc['sweep']['works_threshold']})\n")
        L.append("| Model (train source) | Family | Weakest s working | d_lag there | pool req/min there | Recall at strongest s | Recall at weakest s (realised FPR) |\n|---|---|---|---|---|---|---|")
        for _, r in on.sort_values(["family", "kind", "src"]).iterrows():
            f_ = lambda x, d=3: "never" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"
            L.append(f"| {KIND_LABEL[r.kind]} ({r.src}) | {r.family} | {f_(r.weakest_s_working, 2)} | {f_(r.d_lag_at_onset)} | {f_(r.pool_per_min_at_onset)} | {r.recall_at_strongest:.3f} | {r.recall_at_weakest:.3f} ({r.realised_fpr_at_weakest:.3f}) |")
    art = his_generator_artefacts(sc)
    (OUT / "his_generator_artefacts.json").write_text(json.dumps(art, indent=1, default=float))
    L.append("\n### His tiered generator under the Stage B adversarial check (dev only)\n")
    L.append("| Reading | All-feature AUC | Non-signal-only AUC | Best single feature | Rates share one uptime | Rows above real max (>=1 feature) |\n|---|---|---|---|---|---|")
    for r, v in art.items():
        L.append(f"| {r} | {v['auc_all']:.3f} | {v['auc_non_signal_only']:.3f} | {v['best_single'][0]} {v['best_single'][1]:.3f} | {v['structure']['rates_share_one_uptime']} (real {v['real_structure']['rates_share_one_uptime']}) | {v['structure']['rows_with_any_feature_above_real_max']} |")
    (OUT / "tables.md").write_text("\n".join(L))
    print("wrote tables.md")


if __name__ == "__main__":
    main()
