"""Stage C re-run under generator v2 vs the original v1 (same code path, same config)."""
from __future__ import annotations

import glob
import json
import pickle

import numpy as np
import pandas as pd

from .data import ROOT, load_normals
from .features import regime
from .splits import build_protocol

KINDS = [("his11", "His recipe, as coded (11)"), ("his18", "His recipe, as described (18)"),
         ("lr", "Logistic regression"), ("single", "Best single feature")]
COND = {"C3": "3. honest, rebuilt (all 4 families)", "C4a": "4a. his gen -> rebuilt", "C4b": "4b. rebuilt -> his gen"}


def fmt(t):
    return f"{t[0]:.3f} [{t[1]:.3f}, {t[2]:.3f}]"


def regime_fpr(dirname, reading, protos):
    """FPR at the validation-derived 1% threshold, by regime of the held-out normals (pooled folds, seeds)."""
    dev = protos["readings"][reading]["dev"]
    acc = {}
    for f in sorted(glob.glob(str(ROOT / "reports" / dirname / "raw" / f"honest_{reading}_*.pkl"))):
        r = pickle.load(open(f, "rb"))
        ev = dev[dev.group == r["fold"]].reset_index(drop=True); reg = regime(ev).to_numpy()
        for (kind, src), sw in r["sweep"].items():
            if src != "R":
                continue
            fp = sw["s_norm"] > sw["thr"]["fpr"]
            for rg in ("U", "U0"):
                m = reg == rg
                a = acc.setdefault((kind, rg), [0, 0]); a[0] += int(fp[m].sum()); a[1] += int(m.sum())
    return acc


def main():
    a, _ = load_normals("A"); b, _ = load_normals("B"); proto = build_protocol(a, b)
    v = {k: json.load(open(ROOT / "reports" / d / "main_results.json")) for k, d in (("v1", "stage_c"), ("v2", "stage_c_v2"))}
    L = ["# Stage C re-run: generator v1 vs v2 (v2 fixes ONLY the counts-only uptime fallback)\n",
         "Same code path, same frozen `configs/stage_c.yaml`, same seeds. All four attack families, as in Stage C.\n"]
    for reading in ("A", "B"):
        L.append(f"\n## Reading {reading}\n")
        L.append("| Condition | Model | F1 @ his rule v1 | F1 v2 | PR-AUC v1 | PR-AUC v2 | Recall @ val-1% FPR v1 | v2 | FPR @ his rule v1 | v2 |\n|---|---|---|---|---|---|---|---|---|---|")
        for c, cl in COND.items():
            for k, kl in KINDS:
                g = lambda ver, m: v[ver][f"{reading}|{c}|{k}"][m]
                L.append(f"| {cl} | {kl} | {fmt(g('v1','f1'))} | {fmt(g('v2','f1'))} | {fmt(g('v1','pr_auc'))} | {fmt(g('v2','pr_auc'))} | "
                         f"{fmt(g('v1','recall_at_fpr1'))} | {fmt(g('v2','recall_at_fpr1'))} | {g('v1','fpr')[0]:.3f} | {g('v2','fpr')[0]:.3f} |")
        L.append("\n**network_only sweep onset** (first s with recall >= 0.5 at the validation 1%-FPR threshold; effect-size columns for v1 are WRONG by construction, v2's are right)\n")
        L.append("| Model (rebuilt-trained) | v1 weakest s | v1 recall at strongest s / at weakest s | v2 weakest s | v2 recall at strongest s / at weakest s |\n|---|---|---|---|---|")
        o1 = pd.read_csv(ROOT / "reports" / "stage_c" / f"sweep_onset_{reading}.csv"); o2 = pd.read_csv(ROOT / "reports" / "stage_c_v2" / f"sweep_onset_{reading}.csv")
        for k, kl in KINDS[:1] + KINDS[2:]:
            r1 = o1[(o1.kind == k) & (o1.src == "R") & (o1.family == "network_only")].iloc[0]
            r2 = o2[(o2.kind == k) & (o2.src == "R") & (o2.family == "network_only")].iloc[0]
            f = lambda x: "never" if pd.isna(x) else f"{x:.2f}"
            L.append(f"| {kl} | {f(r1.weakest_s_working)} | {r1.recall_at_strongest:.3f} / {r1.recall_at_weakest:.3f} | {f(r2.weakest_s_working)} | {r2.recall_at_strongest:.3f} / {r2.recall_at_weakest:.3f} |")
        L.append("\n**FPR on counts-only vs other normals** (his recipe family, rebuilt-trained, validation-1% threshold; pooled over folds and seeds)\n")
        L.append("| Model | v1: counts-only | v1: other | v2: counts-only | v2: other |\n|---|---|---|---|---|")
        r1, r2 = regime_fpr("stage_c", reading, proto), regime_fpr("stage_c_v2", reading, proto)
        for k, kl in KINDS:
            c1u0, c1u = r1[(k, "U0")], r1[(k, "U")]; c2u0, c2u = r2[(k, "U0")], r2[(k, "U")]
            L.append(f"| {kl} | {c1u0[0]/c1u0[1]:.3f} ({c1u0[0]}/{c1u0[1]}) | {c1u[0]/c1u[1]:.3f} | {c2u0[0]/c2u0[1]:.3f} ({c2u0[0]}/{c2u0[1]}) | {c2u[0]/c2u[1]:.3f} |")
    (ROOT / "reports" / "stage_d" / "v1_vs_v2_stage_c.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
