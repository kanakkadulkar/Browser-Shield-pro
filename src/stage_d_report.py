"""Aggregate Stage D raw results into tables, bootstrap CIs, per-group spread, sweeps and figures."""
from __future__ import annotations

import glob
import json
import multiprocessing as mp
import pickle
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor

import matplotlib
import numpy as np
import pandas as pd

from .data import ROOT, load_normals
from .metrics_d import NAMES, bootstrap, compute
from .splits import build_protocol
from .stage_d import ONE_CLASS, SUPERVISED, cfgs

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = ROOT / "reports" / "stage_d"
LABEL = {"his11": "His recipe (11 raw features)", "lr": "Logistic regression (raw 11)", "single": "Best single feature (raw 11)",
         "m1_raw11": "M1 XGBoost on his 11 raw features (ablation)", "lr_bsp": "Logistic regression (my features)",
         "m1_bsp": "M1 XGBoost, my features", "m2_bsp": "M2 feature-token attention net, my features",
         "if_raw11": "M4 Isolation Forest (raw 11, his baseline)", "if_bsp": "M4 Isolation Forest (my features)",
         "ae_bsp": "M4 Autoencoder (my features)"}
COMBO = {"C2  H->EH (his gen -> his gen)": ("H", "EH"), "C3  R2->ER2 (v2 -> v2, seen families)": ("R2", "ER2"),
         "CHO R2->EHO (v2 -> HELD-OUT family)": ("R2", "EHO"), "C4a H->ER2 (his gen -> rebuilt)": ("H", "ER2"),
         "C4b R2->EH (rebuilt -> his gen)": ("R2", "EH"), "C5a R1->ER2 (v1 -> v2)": ("R1", "ER2"),
         "C5b R2->ER1 (v2 -> v1)": ("R2", "ER1")}


def load():
    return [pickle.load(open(f, "rb")) for f in sorted(glob.glob(str(OUT / "raw" / "*.pkl")))]


def assemble(jobs, reading, seed, kind, src, ek, fold=None):
    parts = sorted([j for j in jobs if j["reading"] == reading and j["seed"] == seed and (fold is None or j["fold"] == fold)],
                   key=lambda j: j["fold"])
    ys, ss, rs, fs, thr = [], [], [], [], defaultdict(list)
    for i, j in enumerate(parts):
        e = j["eval"][(kind, src, ek)]; n = len(e["y"]); t = j["info"][(kind, src)]["thr"]
        ys.append(e["y"]); ss.append(e["s"]); rs.append(e["reg"]); fs.append(np.full(n, i))
        for k, v in t.items():
            thr[k].append(np.full(n, v))
    return {"y": np.concatenate(ys), "s": np.concatenate(ss), "reg": np.concatenate(rs), "fold": np.concatenate(fs),
            "thr": {k: np.concatenate(v) for k, v in thr.items()}, "prob": bool(parts[0]["info"][(kind, src)]["prob"])}


def _task(args):
    key, runs, prev, mcfg, reps, seed = args
    return key, bootstrap(runs, prev, mcfg, reps, seed)


def fmt(t, d=3):
    if t is None or np.isnan(t[0]):
        return "n/a"
    return f"{t[0]:.{d}f} [{t[1]:.{d}f}, {t[2]:.{d}f}]"


def f1(x, d=3):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"


def main():
    D, sc, syn, spl = cfgs()
    jobs = load()
    prev, mcfg = D["honest"]["prevalence"], D["metrics"]
    seeds = D["seeds"]
    print(f"{len(jobs)} jobs", flush=True)
    # ---------------- bootstrap tasks
    tasks = []
    for r in D["readings"]:
        for cname, (src, ek) in COMBO.items():
            for kind in SUPERVISED:
                tasks.append(((r, cname, kind), [assemble(jobs, r, s, kind, src, ek) for s in seeds], prev, mcfg,
                              mcfg["bootstrap_reps"], mcfg["bootstrap_seed"]))
        for ek in ("EH", "ER2", "EHO"):
            for kind in ONE_CLASS:
                tasks.append(((r, f"OC {ek}", kind), [assemble(jobs, r, s, kind, "none", ek) for s in seeds], prev, mcfg,
                              mcfg["bootstrap_reps"], mcfg["bootstrap_seed"]))
    res = {}
    with ProcessPoolExecutor(9, mp_context=mp.get_context("spawn")) as ex:
        for key, b in ex.map(_task, tasks):
            res[key] = b
    (OUT / "main_results.json").write_text(json.dumps({"|".join(k): {m: list(v) for m, v in b.items()} for k, b in res.items()}, indent=1))

    L = []
    # ---------------- per-group spread (seed-mean, no bootstrap)
    spread = {}
    for r in D["readings"]:
        folds = sorted({j["fold"] for j in jobs if j["reading"] == r})
        for cname, (src, ek) in COMBO.items():
            for kind in SUPERVISED:
                per = []
                for f in folds:
                    ms = [compute(assemble(jobs, r, s, kind, src, ek, f), prev, mcfg) for s in seeds]
                    per.append({k: float(np.nanmean([m[k] for m in ms])) for k in ("roc_auc", "pr_auc", "orec_fpr1", "tr_fpr_val1", "tr_rec_val1", "cnt_fpr_val1")})
                spread[(r, cname, kind)] = (folds, per)
    for r in D["readings"]:
        L.append(f"\n## READING {r}\n")
        for section, combos in (("Primary", ["C3  R2->ER2 (v2 -> v2, seen families)", "CHO R2->EHO (v2 -> HELD-OUT family)"]),):
            for cname in combos:
                L.append(f"\n### {cname}: ranking quality (oracle thresholds on the held-out group)\n")
                L.append("| Model | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE |\n|---|---|---|---|---|---|")
                for kind in SUPERVISED:
                    b = res[(r, cname, kind)]
                    L.append(f"| {LABEL[kind]} | {fmt(b['roc_auc'])} | {fmt(b['pr_auc'])} | {fmt(b['orec_fpr1'])} | {fmt(b['orec_fpr01'])} | {fmt(b['ece'])} |")
                L.append(f"\n### {cname}: threshold transfer (thresholds fixed on validation of the training side)\n")
                L.append("| Model | FPR @ val-1% thr | Recall @ val-1% thr | FPR @ his rule | Recall @ his rule | F1 @ his rule | FPR on counts-only normals (val-1%) | (his rule) | per-group FPR @ val-1% [min..max] |\n|---|---|---|---|---|---|---|---|---|")
                for kind in SUPERVISED:
                    b = res[(r, cname, kind)]; folds, per = spread[(r, cname, kind)]
                    fp = [p["tr_fpr_val1"] for p in per]
                    L.append(f"| {LABEL[kind]} | {fmt(b['tr_fpr_val1'])} | {fmt(b['tr_rec_val1'])} | {fmt(b['tr_fpr_his'])} | {fmt(b['tr_rec_his'])} | {fmt(b['tr_f1_his'])} | {fmt(b['cnt_fpr_val1'])} | {fmt(b['cnt_fpr_his'])} | {min(fp):.3f} .. {max(fp):.3f} |")
        L.append(f"\n### Cross-generator transfer: ROC-AUC / PR-AUC (prevalence 8.35%), [95% CI on ROC]\n")
        cn = list(COMBO)
        L.append("| Model | " + " | ".join(c.split(" (")[0] for c in cn) + " |\n|---|" + "---|" * len(cn))
        for kind in SUPERVISED:
            L.append(f"| {LABEL[kind]} | " + " | ".join(f"{res[(r, c, kind)]['roc_auc'][0]:.3f} / {res[(r, c, kind)]['pr_auc'][0]:.3f}" for c in cn) + " |")
        L.append("\n### M4 one-class (trained on normals only, never sees attacks): evidence about inflation, NOT detection\n")
        L.append("| Model | his generator: ROC / PR / recall@1%FPR | rebuilt v2 (seen families) | held-out family |\n|---|---|---|---|")
        for kind in ONE_CLASS:
            cells = []
            for ek in ("EH", "ER2", "EHO"):
                b = res[(r, f"OC {ek}", kind)]
                cells.append(f"{b['roc_auc'][0]:.3f} / {b['pr_auc'][0]:.3f} / {b['orec_fpr1'][0]:.3f}")
            L.append(f"| {LABEL[kind]} | " + " | ".join(cells) + " |")
        L.append("\n### Per-group spread (seed-mean per validation group), R2->ER2 and held-out family\n")
        L.append("| Cond | Model | " + " | ".join(f"group {i+1}" for i in range(len(spread[(r, cn[1], 'his11')][0]))) + " | spread (max-min) PR-AUC |\n|---|---|" + "---|" * (len(spread[(r, cn[1], 'his11')][0]) + 1))
        for cname in (cn[1], cn[2]):
            for kind in SUPERVISED:
                folds, per = spread[(r, cname, kind)]
                pr = [p["pr_auc"] for p in per]
                L.append(f"| {cname.split(' ')[0]} | {LABEL[kind]} | " + " | ".join(f"ROC {p['roc_auc']:.3f} PR {p['pr_auc']:.3f} FPR {p['tr_fpr_val1']:.3f}" for p in per) + f" | {max(pr)-min(pr):.3f} |")
    # ---------------- headline: counts-only false alarms
    L.append("\n## HEADLINE: false-alarm rate on counts-only normals (uptime unknown), thresholds fixed on validation (1% FPR)\n")
    L.append("| Reading | Model (trained on rebuilt v2, held-out family excluded) | FPR counts-only normals | FPR other normals | overall FPR |\n|---|---|---|---|---|")
    for r in D["readings"]:
        for kind in ["his11", "lr", "m1_raw11", "lr_bsp", "m1_bsp", "m2_bsp"]:
            b = res[(r, "C3  R2->ER2 (v2 -> v2, seen families)", kind)]
            L.append(f"| {r} | {LABEL[kind]} | {fmt(b['cnt_fpr_val1'])} | {fmt(b['oth_fpr_val1'])} | {fmt(b['tr_fpr_val1'])} |")
    n_cnt = {r: sum(j["sizes"]["eval_counts_only_normals"] for j in jobs if j["reading"] == r and j["seed"] == seeds[0]) for r in D["readings"]}
    L.append(f"\nCounts-only normals per reading (summed over folds, one seed): {n_cnt}. Small, so intervals are wide.")
    # ---------------- training info
    L.append("\n## Training details\n")
    ch = defaultdict(Counter)
    for j in jobs:
        for (kind, src), inf in j["info"].items():
            if kind == "m1_bsp":
                ch[(j["reading"], src)][inf["imbalance"]] += 1
    L.append("M1 (my features): imbalance mechanism chosen by the tuning objective (count of fold-seed fits)\n")
    L.append("| Reading | Source | class_weight | focal |\n|---|---|---|---|")
    for (r, src), c in sorted(ch.items()):
        L.append(f"| {r} | {src} | {c['class_weight']} | {c['focal']} |")
    ep = [inf["epochs_run"] for j in jobs for (k, s_), inf in j["info"].items() if k == "m2_bsp" and "epochs_run" in inf]
    L.append(f"\nM2 epochs run: median {np.median(ep):.0f}, min {min(ep)}, max {max(ep)} (max allowed {D['m2']['max_epochs']}).")
    (OUT / "tables.md").write_text("\n".join(L))
    # ---------------- sweep
    sweep_df = sweep_tables(jobs, D)
    sweep_df.to_csv(OUT / "sweep_all.csv", index=False)
    for r in D["readings"]:
        d = sweep_df[sweep_df.reading == r]
        sweep_figure(d, OUT / f"sweep_recall_{r}.png", r)
        on = onset(d, D); on.to_csv(OUT / f"sweep_onset_{r}.csv", index=False)
    print("report written", flush=True)


def sweep_tables(jobs, D):
    rng = np.random.default_rng(D["metrics"]["bootstrap_seed"])
    models = [(k, "R2") for k in SUPERVISED] + [("his11", "H"), ("his11", "R1"), ("m1_bsp", "R1")] + [(k, "none") for k in ONE_CLASS]
    fams = D["sweep"]["families"] + ["network_only_v1"]
    rows = []
    for reading in D["readings"]:
        for kind, src in models:
            for fam in fams:
                for st in D["sweep"]["strengths"]:
                    hits_a, hits_n = [], []
                    for seed in D["seeds"]:
                        ha, hn = [], []
                        for j in jobs:
                            if j["reading"] != reading or j["seed"] != seed:
                                continue
                            sw = j["sweep"][(kind, src)]
                            if (fam, st) not in sw["cells"]:
                                continue
                            ha.append(sw["cells"][(fam, st)] > sw["thr"]["fpr"]); hn.append(sw["s_norm"] > sw["thr"]["fpr"])
                        if ha:
                            hits_a.append(np.concatenate(ha)); hits_n.append(np.concatenate(hn))
                    if not hits_a:
                        continue
                    rec = np.mean([h.mean() for h in hits_a]); fpr = np.mean([h.mean() for h in hits_n])
                    bs = [np.mean([rng.choice(h, len(h)).mean() for h in hits_a]) for _ in range(150)]
                    rows.append({"reading": reading, "kind": kind, "src": src, "family": fam, "s": st,
                                 "recall": rec, "lo": np.quantile(bs, .025), "hi": np.quantile(bs, .975), "realised_fpr": fpr})
    return pd.DataFrame(rows)


def sweep_figure(d, path, reading):
    fams = [("main_thread", "main_thread"), ("worker_pool", "worker_pool"), ("network_only", "network_only (v2)"),
            ("throttled", "throttled  [HELD-OUT family]")]
    style = {("his11", "R2"): ("#d62728", "-", "his recipe"), ("m1_bsp", "R2"): ("#1f77b4", "-", "M1 XGBoost, my features"),
             ("m2_bsp", "R2"): ("#9467bd", "-", "M2 attention net, my features"), ("lr", "R2"): ("#2ca02c", ":", "logistic regression (raw 11)"),
             ("ae_bsp", "none"): ("#7f7f7f", "--", "M4 autoencoder (normals only)")}
    fig, axes = plt.subplots(1, 4, figsize=(17, 3.9), sharey=True)
    for ax, (fam, title) in zip(axes, fams):
        for (k, s_), (c, ls, lab) in style.items():
            x = d[(d.family == fam) & (d.kind == k) & (d.src == s_)].sort_values("s")
            ax.plot(x["s"], x["recall"], color=c, ls=ls, marker="o", ms=3, label=lab)
            ax.fill_between(x["s"], x["lo"], x["hi"], color=c, alpha=.1)
        ax.axvspan(0, 1, color="k", alpha=.04); ax.set_title(title, fontsize=10); ax.set_ylim(-.02, 1.02); ax.grid(alpha=.3)
        ax.set_xlabel("signal strength s (shaded = standard range)")
    axes[0].set_ylabel("recall at val-derived 1% FPR threshold")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=5, frameon=False, fontsize=8)
    fig.suptitle(f"Reading {reading}: detection vs signal strength  [simulated miner signal, assumed effect sizes]", fontsize=10)
    fig.tight_layout(rect=(0, .08, 1, .94)); fig.savefig(path, dpi=130); plt.close(fig)


def onset(d, D):
    thr = D["sweep"]["works_threshold"]; rows = []
    for (kind, src, fam), x in d.groupby(["kind", "src", "family"]):
        x = x.sort_values("s"); ok = x[x["recall"] >= thr]
        rows.append({"kind": kind, "src": src, "family": fam, "weakest_s_working": ok["s"].min() if len(ok) else np.nan,
                     "recall_s0": float(x[x.s == 0.0]["recall"].iloc[0]), "recall_s1": float(x[x.s == 1.0]["recall"].iloc[0]),
                     "recall_floor": float(x.iloc[0]["recall"]), "fpr_floor": float(x.iloc[0]["realised_fpr"])})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()
