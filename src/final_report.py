"""Turn the final-evaluation raw arrays into docs/FINAL_RESULTS.md tables (per group first, then pooled)."""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from .data import ROOT
from .metrics_d import ece, fold_weights, oracle_recall
from .stage_d import cfgs

PREV = 0.0835
REPS = 300


# ------------------------------------------------------------------ small statistics helpers
def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def rate(k, n, d=3):
    if n == 0:
        return "n/a (0/0)"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {k/n:.{d}f} [{lo:.{d}f}, {hi:.{d}f}]"


# ------------------------------------------------------------------ metric functions (same for dev and test)
def policy_counts(a):
    """a: dict(y, reg, oor, dang, susp). Returns raw counts."""
    y, reg, oor, dang, susp = a["y"], a["reg"], a["oor"].astype(bool), a["dang"], a["susp"]
    n0, n1 = y == 0, y == 1
    co, ot = n0 & (reg == "U0"), n0 & (reg == "U")
    return {"n_norm": int(n0.sum()), "n_att": int(n1.sum()), "n_co": int(co.sum()), "n_oth": int(ot.sum()),
            "n_decided_norm": int((n0 & ~oor).sum()),
            "unsure_norm": int((n0 & oor).sum()), "unsure_att": int((n1 & oor).sum()),
            "fp_dang": int(dang[n0].sum()), "fp_dang_decided": int(dang[n0 & ~oor].sum()),
            "fp_co": int(dang[co].sum()), "fp_oth": int(dang[ot].sum()),
            "tp_dang": int(dang[n1].sum()), "tp_ds": int((dang | susp)[n1].sum())}


def policy_rates(c):
    d = lambda k, n: k / n if n else np.nan
    return {"fpr_dang": d(c["fp_dang"], c["n_norm"]), "fpr_dang_decided": d(c["fp_dang_decided"], c["n_decided_norm"]),
            "fpr_co": d(c["fp_co"], c["n_co"]), "fpr_oth": d(c["fp_oth"], c["n_oth"]),
            "rec_d": d(c["tp_dang"], c["n_att"]), "rec_ds": d(c["tp_ds"], c["n_att"]),
            "unsure_norm": d(c["unsure_norm"], c["n_norm"]), "unsure_att": d(c["unsure_att"], c["n_att"])}


def ranking(a, score="cal"):
    y, s, g = a["y"], a[score], a["gid"]
    w = fold_weights(y, g, PREV)
    return {"roc_auc": roc_auc_score(y, s), "pr_auc": average_precision_score(y, s, sample_weight=w),
            "orec1": oracle_recall(y, s, g, 0.01), "orec01": oracle_recall(y, s, g, 0.001), "ece": ece(y, s, w, 10)}


def sub(a, mask):
    return {k: (v[mask] if isinstance(v, np.ndarray) and len(v) == len(mask) else v) for k, v in a.items()}


def boot_ci(runs, fn, reps=REPS, seed=12345, ci=0.95):
    """runs: per-seed dict arrays incl. gid. Rows resampled within (group, class); fn(run)->dict; seed-averaged."""
    rng = np.random.default_rng(seed)
    cells = [[np.where((r["gid"] == g) & (r["y"] == c))[0] for g in np.unique(r["gid"]) for c in (0, 1)] for r in runs]
    point = {k: float(np.nanmean([fn(r)[k] for r in runs])) for k in fn(runs[0])}
    boots = {k: [] for k in point}
    for _ in range(reps):
        vals = []
        for r, cl in zip(runs, cells):
            idx = np.concatenate([rng.choice(c, len(c)) for c in cl if len(c)])
            vals.append(fn(sub_idx(r, idx)))
        for k in point:
            boots[k].append(np.nanmean([v[k] for v in vals]) if not all(np.isnan(v[k]) for v in vals) else np.nan)
    a = (1 - ci) / 2
    return {k: (point[k], float(np.nanquantile(boots[k], a)), float(np.nanquantile(boots[k], 1 - a))) for k in point}


def sub_idx(a, idx):
    return {k: (v[idx] if isinstance(v, np.ndarray) and v.ndim == 1 and len(v) == len(a["y"]) else v) for k, v in a.items()}


def f3(t):
    return "n/a" if t is None or np.isnan(t[0]) else f"{t[0]:.3f} [{t[1]:.3f}, {t[2]:.3f}]"


# ------------------------------------------------------------------ test-side arrays
def test_runs(results, reading, es, group=None):
    """List of per-seed run dicts for the test set (optionally one group), with integer group ids."""
    out = []
    for r in sorted([x for x in results if x["reading"] == reading], key=lambda x: x["seed"]):
        e = r["eval"][es]
        names = sorted(set(e["group"]), key=lambda n: -int((e["group"][e["y"] == 0] == n).sum()))
        gid = np.array([names.index(n) for n in e["group"]])
        a = {**e, "gid": gid, "his_val1": (e["his"] > r["info"]["his_thr"]["fpr"]).astype(int),
             "his_rule": (e["his"] >= r["info"]["his_thr"]["main"]).astype(int), "seed": r["seed"], "names": names}
        if group is not None:
            a = sub_idx(a, np.where(gid == group)[0])
        out.append(a)
    return out


def his_counts(a):
    n0, n1 = a["y"] == 0, a["y"] == 1
    return {"fp1": int(a["his_val1"][n0].sum()), "tp1": int(a["his_val1"][n1].sum()),
            "fpr_rule": int(a["his_rule"][n0].sum()), "tpr_rule": int(a["his_rule"][n1].sum()), "n0": int(n0.sum()), "n1": int(n1.sum())}


# ------------------------------------------------------------------ dev-side arrays (Stage E raw, same definitions)
def dev_runs(an, reading, es, q=0.0025, q_susp=0.05):
    runs = []
    for seed in an.seeds:
        P = an.pooled(reading, seed, es, "platt")
        dq = an.decisions(reading, seed, es, "platt", "m1", "V0", q)
        d5 = an.decisions(reading, seed, es, "platt", "m1", "V0", q_susp)
        oor = P["oor"].astype(bool)
        dang = dq & ~oor
        runs.append({"y": P["y"], "reg": P["reg"], "oor": oor, "dang": dang, "susp": d5 & ~dq & ~oor,
                     "cal": P["sc"]["m1"], "gid": P["fold"], "seed": seed})
    return runs


METRICS = [("roc_auc", "ROC-AUC", 1), ("pr_auc", "PR-AUC (8.35%)", 1), ("orec1", "Oracle recall @ FPR 1%", 1),
           ("orec01", "Oracle recall @ FPR 0.1%", 1), ("ece", "ECE", -1),
           ("fpr_dang", "FPR, 'dangerous' (all normals)", -1), ("fpr_co", "FPR, counts-only normals", -1),
           ("fpr_oth", "FPR, other normals", -1), ("rec_d", "Recall, 'dangerous' alone", 1),
           ("rec_ds", "Recall, 'dangerous' + 'suspicious'", 1), ("unsure_norm", "Unsure rate, normals", -1),
           ("unsure_att", "Unsure rate, attacks", -1)]


def all_metrics(a):
    return {**ranking(a), **policy_rates(policy_counts(a))}


def per_group_mean(runs, gid):
    vals = [all_metrics(sub_idx(r, np.where(r["gid"] == gid)[0])) for r in runs]
    return {k: float(np.nanmean([v[k] for v in vals])) for k in vals[0]}


def flag(val, better, ci, rng_):
    """'' within or better; 'W' worse than the dev pooled CI; 'WW' also worse than the whole dev per-group range."""
    if np.isnan(val):
        return ""
    worse_ci = val < ci[1] if better == 1 else val > ci[2]
    worse_rng = val < rng_[0] if better == 1 else val > rng_[1]
    return " ⛔" if worse_rng else (" ⚠" if worse_ci else "")


def build_tables(results, out_md: Path):
    from .stage_e_analysis import Analysis
    an = Analysis()
    L = []
    for reading in ("A", "B"):
        for es, esl in (("ER2", "SEEN families"), ("EHO", "HELD-OUT family")):
            runs_all = test_runs(results, reading, es)
            k_groups = len(runs_all[0]["names"])
            seed0 = runs_all[0]["seed"]
            L.append(f"\n## Reading {reading}: {esl}\n")
            # --- per group first, then pooled
            for gid in list(range(k_groups)) + ["pooled"]:
                runs = runs_all if gid == "pooled" else test_runs(results, reading, es, gid)
                title = "POOLED over the test groups" if gid == "pooled" else f"Test group {gid + 1}"
                c0 = policy_counts(runs[0])
                L.append(f"\n### {title}  (seed {seed0}: {c0['n_norm']} real normals, {c0['n_att']} simulated attacks, "
                         f"{c0['n_co']} counts-only normals, {c0['unsure_norm']} + {c0['unsure_att']} unsure rows)\n")
                L.append("| Policy outcome (seed %d, raw counts, Wilson 95%% CI) | value |\n|---|---|" % seed0)
                L.append(f"| FPR, 'dangerous' (all normals) | {rate(c0['fp_dang'], c0['n_norm'])} |")
                L.append(f"| FPR, 'dangerous' among decided normals | {rate(c0['fp_dang_decided'], c0['n_decided_norm'])} |")
                L.append(f"| FPR on counts-only normals | {rate(c0['fp_co'], c0['n_co'])} |")
                L.append(f"| FPR on other normals | {rate(c0['fp_oth'], c0['n_oth'])} |")
                L.append(f"| Recall, 'dangerous' alone | {rate(c0['tp_dang'], c0['n_att'])} |")
                L.append(f"| Recall, 'dangerous' + 'suspicious' | {rate(c0['tp_ds'], c0['n_att'])} |")
                L.append(f"| Unsure rows: normals / attacks | {c0['unsure_norm']}/{c0['n_norm']} / {c0['unsure_att']}/{c0['n_att']} |")
                per_seed = [policy_rates(policy_counts(r)) for r in runs]
                L.append("\n3-seed mean [min, max across seeds] of the same rates (seeds change the attack draws and model training; normals are identical):\n")
                L.append("| " + " | ".join(["FPR dangerous", "FPR counts-only", "FPR other", "Recall dangerous", "Recall d+s", "Unsure normals", "Unsure attacks"]) + " |\n|---|---|---|---|---|---|---|")
                keys = ["fpr_dang", "fpr_co", "fpr_oth", "rec_d", "rec_ds", "unsure_norm", "unsure_att"]
                L.append("| " + " | ".join(f"{np.nanmean([p[k] for p in per_seed]):.3f} [{np.nanmin([p[k] for p in per_seed]):.3f}, {np.nanmax([p[k] for p in per_seed]):.3f}]" for k in keys) + " |")
                b = boot_ci(runs, ranking)
                L.append("\nRanking quality (seed mean, bootstrap 95% CI over rows):\n")
                L.append("| ROC-AUC | PR-AUC (8.35%) | Oracle recall @ 1% FPR | Oracle recall @ 0.1% FPR | ECE |\n|---|---|---|---|---|")
                L.append("| " + " | ".join(f3(b[k]) for k in ("roc_auc", "pr_auc", "orec1", "orec01", "ece")) + " |")
                h = his_counts(runs[0])
                hr = boot_ci([{**r, "cal": r["his"]} for r in runs], lambda a: ranking(a, "cal"))
                L.append(f"\nComparator, his recipe (same training side, same attacks; seed {seed0}): "
                         f"at validation-1% threshold FPR {rate(h['fp1'], h['n0'])}, recall {rate(h['tp1'], h['n1'])}; "
                         f"at his own rule FPR {rate(h['fpr_rule'], h['n0'])}, recall {rate(h['tpr_rule'], h['n1'])}; "
                         f"ROC-AUC {f3(hr['roc_auc'])}, PR-AUC {f3(hr['pr_auc'])}.\n")
            # --- dev vs test
            dr = dev_runs(an, reading, es)
            dev_ci = boot_ci(dr, all_metrics)
            dev_groups = sorted(np.unique(dr[0]["gid"]))
            dev_pg = {g: per_group_mean(dr, g) for g in dev_groups}
            test_cols = {f"test group {g + 1}": {k: v for k, v in per_group_mean(runs_all, g).items()} for g in range(k_groups)}
            test_cols["test pooled"] = {k: float(np.nanmean([all_metrics(r)[k] for r in runs_all])) for k in all_metrics(runs_all[0])}
            L.append(f"\n### Dev vs test, Reading {reading}, {esl}\n")
            L.append(f"Dev = the Stage E held-out dev groups (n groups = {len(dev_groups)}), same frozen pipeline, same policy. "
                     "Flags: ⚠ = test value worse than the dev pooled 95% CI; ⛔ = worse than every dev group (outside the dev per-group range).\n")
            L.append("| Metric | Dev pooled [95% CI] | Dev per-group range | " + " | ".join(test_cols) + " |\n|---|---|---|" + "---|" * len(test_cols))
            for key, name, better in METRICS:
                pg = [dev_pg[g][key] for g in dev_groups]
                rng_ = (np.nanmin(pg), np.nanmax(pg))
                cells = []
                for col, vals in test_cols.items():
                    cells.append(f"{vals[key]:.3f}{flag(vals[key], better, dev_ci[key], rng_)}")
                L.append(f"| {name} | {f3(dev_ci[key])} | {rng_[0]:.3f} to {rng_[1]:.3f} | " + " | ".join(cells) + " |")
    out_md.write_text("\n".join(L))
    return out_md


if __name__ == "__main__":
    raw = Path(sys.argv[1]); out = Path(sys.argv[2])
    build_tables(pickle.load(open(raw, "rb")), out)
    print("wrote", out)
