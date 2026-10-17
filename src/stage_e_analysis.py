"""Stage E analysis: calibration, stacked ensemble, counts-only regime variants, threshold policy.

Everything that is FITTED (calibrators, stacker, regime thresholds, deployment thresholds) is fitted on
the fold's VALIDATION arrays only. All selection rules were written in configs/stage_e.yaml before any
Stage E result existed and are applied mechanically here. Dev folds only; locked test set untouched.
"""
from __future__ import annotations

import glob
import json
import pickle

import matplotlib
import numpy as np
import pandas as pd
import yaml
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score

from .data import ROOT
from .metrics_d import bootstrap, compute, ece, fold_weights
from .stage_d import cfgs

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = ROOT / "reports" / "stage_e"
VARIANTS = ["V0", "Va", "Vb", "Vab"]
BASES = ["m1", "m2", "ens"]


def lg(p):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


class FoldCtx:
    """Everything fitted from one fold's validation set for one calibration method."""

    def __init__(self, job, method, E):
        self.job, self.method, self.E = job, method, E
        v = job["val"]; self.v = v; y = v["y"]
        self.cal = {k: self._fit_cal(v[f"s_{k}"], y) for k in ("m1", "m2")}
        c = {k: self.cal[k](v[f"s_{k}"]) for k in ("m1", "m2")}
        self.stack = LogisticRegression(C=E["ensemble"]["stacker"]["c"], max_iter=2000).fit(np.c_[lg(c["m1"]), lg(c["m2"])], y)
        co = v["co"] == 1
        ok = (not np.isnan(v["s_co"]).all()) and (y[co] == 1).sum() >= E["regime"]["calibrator_min_val_attacks"] and (y[co] == 0).sum() >= 5
        self.co_avail = not np.isnan(v["s_co"]).all()
        self.co_cal = self._fit_cal(v["s_co"][co], y[co]) if ok else (lambda s: s)
        self.co_calibrated = bool(ok)

    def _fit_cal(self, s, y):
        if self.method == "platt":
            m = LogisticRegression(C=self.E["calibration"]["platt"]["c"], max_iter=5000).fit(lg(s).reshape(-1, 1), y)
            return lambda x: m.predict_proba(lg(x).reshape(-1, 1))[:, 1]
        m = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(s, y)
        return lambda x: m.predict(x)

    def scores(self, a):
        m1, m2 = self.cal["m1"](a["s_m1"]), self.cal["m2"](a["s_m2"])
        ens = self.stack.predict_proba(np.c_[lg(m1), lg(m2)])[:, 1]
        co = np.full(len(m1), np.nan)
        if self.co_avail:
            ok = ~np.isnan(a["s_co"])
            co[ok] = self.co_cal(a["s_co"][ok])
        return {"m1": m1, "m2": m2, "ens": ens, "co": co}

    def variant_score(self, sc, a, base, variant):
        s = sc[base].copy()
        if variant in ("Vb", "Vab"):
            use = (a["co"] == 1) & ~np.isnan(sc["co"])
            s[use] = sc["co"][use]
        return s

    def thresholds(self, base, variant, q):
        """(thr_other, thr_co) from validation normals only. V0/Vb: one global threshold."""
        sv = self.variant_score(self.scores(self.v), self.v, base, variant)
        y, co = self.v["y"], self.v["co"] == 1
        g = float(np.quantile(sv[y == 0], 1 - q))
        if variant in ("Va", "Vab"):
            n_co = int(((y == 0) & co).sum())
            t_oth = float(np.quantile(sv[(y == 0) & ~co], 1 - q))
            t_co = float(np.quantile(sv[(y == 0) & co], 1 - q)) if n_co >= self.E["regime"]["regime_threshold_min_val_normals"] else g
            return t_oth, t_co
        return g, g

    def decide(self, a, base, variant, q, sc=None):
        sc = sc or self.scores(a)
        s = self.variant_score(sc, a, base, variant)
        t_oth, t_co = self.thresholds(base, variant, q)
        return s > np.where(a["co"] == 1, t_co, t_oth)


def load(dirname):
    return [pickle.load(open(f, "rb")) for f in sorted(glob.glob(str(ROOT / "reports" / dirname / "raw" / "*.pkl")))]


def cat(parts, key):
    return np.concatenate([p[key] for p in parts])


class Analysis:
    def __init__(self):
        self.D, _, _, _ = cfgs()
        self.E = yaml.safe_load(open(ROOT / "configs" / "stage_e.yaml"))
        self.prev = self.D["honest"]["prevalence"]; self.mcfg = self.D["metrics"]
        self.jobs = load("stage_e")
        self.seeds, self.readings = self.E["seeds"], self.E["readings"]
        self.ctx = {}
        for j in self.jobs:
            for m in self.E["calibration"]["methods"]:
                self.ctx[(j["reading"], j["fold"], j["seed"], m)] = FoldCtx(j, m, self.E)

    def parts(self, reading, seed):
        return sorted([j for j in self.jobs if j["reading"] == reading and j["seed"] == seed], key=lambda j: j["fold"])

    def pooled(self, reading, seed, es, method, fold=None):
        ps = [p for p in self.parts(reading, seed) if fold is None or p["fold"] == fold]
        arr = {k: [] for k in ("y", "reg", "co", "oor", "fam", "fold")}
        sc = {k: [] for k in ("m1", "m2", "ens", "co")}
        raw = {k: [] for k in ("s_m1", "s_m2", "s_co")}
        for i, p in enumerate(ps):
            a = p["eval"][es]; s = self.ctx[(reading, p["fold"], seed, method)].scores(a)
            for k in ("y", "reg", "co", "oor", "fam"):
                arr[k].append(a[k])
            arr["fold"].append(np.full(len(a["y"]), i))
            for k in sc:
                sc[k].append(s[k])
            for k in raw:
                raw[k].append(a[k])
        out = {k: np.concatenate(v) for k, v in arr.items()}
        out["sc"] = {k: np.concatenate(v) for k, v in sc.items()}
        out["raw"] = {k: np.concatenate(v) for k, v in raw.items()}
        out["parts"] = ps
        return out

    def decisions(self, reading, seed, es, method, base, variant, q, fold=None):
        ps = [p for p in self.parts(reading, seed) if fold is None or p["fold"] == fold]
        return np.concatenate([self.ctx[(reading, p["fold"], seed, method)].decide(p["eval"][es], base, variant, q) for p in ps])

    def run_for(self, reading, es, method, key, kind="cal"):
        """metrics_d run dicts (one per seed). kind='cal': calibrated base score `key` in {m1,m2,ens};
        kind='raw': raw member score `key` in {s_m1,s_m2}. Transfer metrics use the validation-1% threshold
        of the SAME score (his threshold rule does not apply to these scores)."""
        runs = []
        for seed in self.seeds:
            P = self.pooled(reading, seed, es, method)
            sc = P["sc"][key] if kind == "cal" else P["raw"][key]
            thr = {k: [] for k in ("main", "fpr", "fpr01", "rec")}
            for p in P["parts"]:
                ctx = self.ctx[(reading, p["fold"], seed, method)]
                sv = ctx.scores(p["val"])[key] if kind == "cal" else p["val"][key]
                yv = p["val"]["y"]
                t1 = float(np.quantile(sv[yv == 0], 1 - self.mcfg["fpr_targets"][0]))
                t01 = float(np.quantile(sv[yv == 0], 1 - self.mcfg["fpr_targets"][1]))
                n = len(p["eval"][es]["y"])
                for k, t in (("main", t1), ("fpr", t1), ("fpr01", t01), ("rec", t1)):
                    thr[k].append(np.full(n, t))
            runs.append({"y": P["y"], "s": sc, "reg": P["reg"], "fold": P["fold"],
                         "thr": {k: np.concatenate(v) for k, v in thr.items()}, "prob": True})
        return runs


def fmt(t, d=3):
    return "n/a" if t is None or np.isnan(t[0]) else f"{t[0]:.{d}f} [{t[1]:.{d}f}, {t[2]:.{d}f}]"


def boot_rates(items, reps, seed, ci=0.95):
    """items: list (per seed) of dict(dec, fold, mask_* arrays). Rows resampled within (fold, cell)."""
    rng = np.random.default_rng(seed)
    cells = []
    for it in items:
        c = {}
        for name in ("n_co", "n_oth", "att", "att_co"):
            c[name] = [np.where(it[name] & (it["fold"] == f))[0] for f in np.unique(it["fold"])]
        cells.append(c)
    def stat(it, idx_sets):
        out = {}
        for name, key in (("fpr_co", "n_co"), ("fpr_oth", "n_oth"), ("rec_all", "att"), ("rec_co", "att_co")):
            idx = np.concatenate(idx_sets[key]) if idx_sets[key] else np.array([], int)
            out[name] = it["dec"][idx].mean() if len(idx) else np.nan
        idx = np.concatenate(idx_sets["n_co"] + idx_sets["n_oth"])
        out["fpr_all"] = it["dec"][idx].mean()
        return out
    names = ["fpr_co", "fpr_oth", "fpr_all", "rec_all", "rec_co"]
    pt = {k: float(np.nanmean([stat(it, c)[k] for it, c in zip(items, cells)])) for k in names}
    boots = {k: [] for k in names}
    for _ in range(reps):
        vals = []
        for it, c in zip(items, cells):
            rs = {k: [rng.choice(a, len(a)) if len(a) else a for a in v] for k, v in c.items()}
            vals.append(stat(it, rs))
        for k in names:
            boots[k].append(np.nanmean([v[k] for v in vals]) if not all(np.isnan(v[k]) for v in vals) else np.nan)
    a = (1 - ci) / 2
    return {k: (pt[k], float(np.nanquantile(boots[k], a)), float(np.nanquantile(boots[k], 1 - a))) for k in names}


# =============================================================================== main
def main():
    from .stage_d_report import assemble as assemble_d
    an = Analysis(); E, D, prev, mcfg = an.E, an.D, an.prev, an.mcfg
    reps, bseed = mcfg["bootstrap_reps"], mcfg["bootstrap_seed"]
    jobs_d = load("stage_d")
    L, res = ["# Stage E tables (dev folds only; simulated miner signal, assumed effect sizes)\n"], {"choices": {}}
    P_ = "A"

    # ---- 0. M1 reproduces Stage D exactly?
    diffs = []
    for j in an.jobs:
        jd = next(x for x in jobs_d if x["reading"] == j["reading"] and x["fold"] == j["fold"] and x["seed"] == j["seed"])
        for es in ("ER2", "EHO"):
            ed = jd["eval"][("m1_bsp", "R2", es)]
            assert np.array_equal(ed["y"], j["eval"][es]["y"]), "evaluation sets differ from Stage D"
            diffs.append(float(np.abs(ed["s"] - j["eval"][es]["s_m1"]).max()))
    res["m1_vs_stage_d_max_abs_score_diff"] = max(diffs)
    L.append(f"**Reproducibility:** Stage E evaluation sets are identical to Stage D's; M1 scores differ from Stage D's stored M1/R2 scores by at most {max(diffs):.2e}.\n")

    # ---- 1. calibration method (rule: lowest mean member ECE on Reading A, R2->ER2; tie -> platt)
    ece_tab = {}
    for method in E["calibration"]["methods"]:
        vals = {"m1": [], "m2": []}
        for seed in an.seeds:
            P = an.pooled(P_, seed, "ER2", method)
            w = fold_weights(P["y"], P["fold"], prev)
            for k in vals:
                vals[k].append(ece(P["y"], P["sc"][k], w, mcfg["ece_bins"]))
        ece_tab[method] = {k: float(np.mean(v)) for k, v in vals.items()}
    raw_ece = {}
    for k in ("m1", "m2"):
        v = []
        for seed in an.seeds:
            P = an.pooled(P_, seed, "ER2", "platt"); w = fold_weights(P["y"], P["fold"], prev)
            v.append(ece(P["y"], P["raw"][f"s_{k}"], w, mcfg["ece_bins"]))
        raw_ece[k] = float(np.mean(v))
    mean_ece = {m: np.mean(list(t.values())) for m, t in ece_tab.items()}
    chosen_method = "platt" if mean_ece["platt"] <= mean_ece["isotonic"] + 1e-4 else "isotonic"
    res["choices"]["calibration"] = chosen_method
    res["ece_member"] = {"raw": raw_ece, **ece_tab}
    L.append("## 1. Calibration (fit on validation only). ECE on Reading A, R2->ER2 (seed mean)\n")
    L.append("| Member | raw | Platt | isotonic |\n|---|---|---|---|")
    for k in ("m1", "m2"):
        L.append(f"| {k.upper()} | {raw_ece[k]:.3f} | {ece_tab['platt'][k]:.3f} | {ece_tab['isotonic'][k]:.3f} |")
    L.append(f"\nRule (lowest mean member ECE, tie -> Platt) selects: **{chosen_method}** (mean ECE Platt {mean_ece['platt']:.4f}, isotonic {mean_ece['isotonic']:.4f}).\n")

    # ---- 2. fair M2
    L.append("## 2. Fair M2: same tuning budget as M1 (20 Optuna trials, same objective and validation scheme), own imbalance choice\n")
    boot_cache = {}
    for reading in an.readings:
        for es, esl in (("ER2", "seen families (R2->ER2)"), ("EHO", "HELD-OUT family")):
            runs = {
                "His recipe (Stage D)": [assemble_d(jobs_d, reading, s, "his11", "R2", es) for s in an.seeds],
                "M1 XGBoost (tuned)": an.run_for(reading, es, chosen_method, "s_m1", "raw"),
                "M2 untuned (Stage D, M1's imbalance choice)": [assemble_d(jobs_d, reading, s, "m2_bsp", "R2", es) for s in an.seeds],
                "M2 TUNED (own imbalance choice)": an.run_for(reading, es, chosen_method, "s_m2", "raw")}
            L.append(f"\n### Reading {reading}, {esl}\n")
            L.append("| Model | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE (raw) | Realised FPR @ val-1% | Recall @ val-1% | FPR counts-only normals |\n|---|---|---|---|---|---|---|---|---|")
            for name, r in runs.items():
                b = bootstrap(r, prev, mcfg, reps, bseed); boot_cache[(reading, es, name)] = b
                L.append(f"| {name} | {fmt(b['roc_auc'])} | {fmt(b['pr_auc'])} | {fmt(b['orec_fpr1'])} | {fmt(b['orec_fpr01'])} | {fmt(b['ece'])} | {fmt(b['tr_fpr_val1'])} | {fmt(b['tr_rec_val1'])} | {fmt(b['cnt_fpr_val1'])} |")
        # tuning summary
        i1 = [j["info"]["m1"] for j in an.jobs if j["reading"] == reading]; i2 = [j["info"]["m2"] for j in an.jobs if j["reading"] == reading]
        L.append(f"\nReading {reading} tuning: M1 best objective mean {np.mean([i['best_value'] for i in i1]):.3f} (imbalance: class_weight {sum(i['imbalance']=='class_weight' for i in i1)}, focal {sum(i['imbalance']=='focal' for i in i1)}); "
                 f"M2 best objective mean {np.mean([i['best_value'] for i in i2]):.3f} (class_weight {sum(i['imbalance']=='class_weight' for i in i2)}, focal {sum(i['imbalance']=='focal' for i in i2)}); "
                 f"M2 final epochs median {np.median([i['epochs_run'] for i in i2]):.0f}.")
    res["m2_tuned_vs_m1"] = {r: {"m1_pr": boot_cache[(r, "ER2", "M1 XGBoost (tuned)")]["pr_auc"], "m2t_pr": boot_cache[(r, "ER2", "M2 TUNED (own imbalance choice)")]["pr_auc"],
                                 "m2u_pr": boot_cache[(r, "ER2", "M2 untuned (Stage D, M1's imbalance choice)")]["pr_auc"],
                                 "his_pr": boot_cache[(r, "ER2", "His recipe (Stage D)")]["pr_auc"]} for r in an.readings}

    # ---- 3. counts-only regime variants (rule applied per base on Reading A, ER2, FPR target 1%)
    L.append("\n## 3. Counts-only regime handling (calibration: %s; thresholds fixed on validation, 1%% FPR target)\n" % chosen_method)
    co_avail = {r: (sum(j["info"]["co"]["available"] for j in an.jobs if j["reading"] == r), sum(1 for j in an.jobs if j["reading"] == r)) for r in an.readings}
    L.append(f"Separate counts-only model available (enough training counts-only rows) in fold-seed fits: {co_avail}. Where it is unavailable, Vb/Vab fall back to V0/Va for that fold.\n")
    var_stats, choice_var = {}, {}
    for reading in an.readings:
        for base in BASES:
            for var in VARIANTS:
                items = []
                for seed in an.seeds:
                    P = an.pooled(reading, seed, "ER2", chosen_method)
                    dec = an.decisions(reading, seed, "ER2", chosen_method, base, var, 0.01)
                    y, reg, co = P["y"], P["reg"], P["co"]
                    items.append({"dec": dec, "fold": P["fold"], "n_co": (y == 0) & (reg == "U0"), "n_oth": (y == 0) & (reg == "U"),
                                  "att": y == 1, "att_co": (y == 1) & (co == 1)})
                var_stats[(reading, base, var)] = boot_rates(items, reps, bseed)
    for reading in an.readings:
        L.append(f"\n### Reading {reading} (R2 -> ER2, seen families) [95% CI]\n")
        L.append("| Base | Variant | FPR counts-only normals | FPR other normals | Overall FPR | Recall (all attacks) | Recall (counts-only attacks) |\n|---|---|---|---|---|---|---|")
        for base in BASES:
            for var in VARIANTS:
                s = var_stats[(reading, base, var)]
                L.append(f"| {base} | {var} | {fmt(s['fpr_co'])} | {fmt(s['fpr_oth'])} | {fmt(s['fpr_all'])} | {fmt(s['rec_all'])} | {fmt(s['rec_co'])} |")
    # group counts for counts-only normals + per-group counts-only FPR
    L.append("\n### Group counts (counts-only normals per held-out group) and per-group counts-only FPR (seed mean), Reading A and B\n")
    L.append("| Reading | Group | counts-only normals | other normals | " + " | ".join(f"{b}/{v}" for b in BASES for v in ("V0", "Vab")) + " |\n|---|---|---|---|" + "---|" * 6)
    for reading in an.readings:
        parts = an.parts(reading, an.seeds[0])
        for i, p in enumerate(parts):
            row = []
            for base in BASES:
                for var in ("V0", "Vab"):
                    v = []
                    for seed in an.seeds:
                        P = an.pooled(reading, seed, "ER2", chosen_method, fold=p["fold"])
                        dec = an.decisions(reading, seed, "ER2", chosen_method, base, var, 0.01, fold=p["fold"])
                        m = (P["y"] == 0) & (P["reg"] == "U0")
                        v.append(dec[m].mean() if m.any() else np.nan)
                    row.append(f"{np.nanmean(v):.3f}")
            sz = p["sizes"]
            L.append(f"| {reading} | group {i+1} | {sz['eval_counts_only_normals']} | {sz['eval_norm'] - sz['eval_counts_only_normals']} | " + " | ".join(row) + " |")
    rule = E["regime"]["selection_rule"]
    for base in BASES:
        v0 = var_stats[(P_, base, "V0")]; best, why = "V0", "no eligible variant beats V0 by the required margin"
        cand = []
        for var in VARIANTS[1:]:
            s = var_stats[(P_, base, var)]
            if s["rec_all"][0] >= v0["rec_all"][0] - rule["eligible_if"]["recall_not_lower_than_V0_by_more_than"] and \
               s["fpr_oth"][0] <= v0["fpr_oth"][0] + rule["eligible_if"]["other_normals_fpr_not_higher_than_V0_by_more_than"]:
                cand.append((s["fpr_co"][0], VARIANTS.index(var), var))
        if cand:
            c = min(cand)
            if v0["fpr_co"][0] - c[0] >= rule["require_improvement_over_V0_of_at_least"]:
                best, why = c[2], f"counts-only FPR {v0['fpr_co'][0]:.3f} -> {c[0]:.3f}"
        choice_var[base] = {"variant": best, "why": why}
    res["choices"]["regime_variant_per_base"] = choice_var
    L.append("\n**Selection rule applied (Reading A):** " + "; ".join(f"{b}: **{c['variant']}** ({c['why']})" for b, c in choice_var.items()) + "\n")

    # ---- 4. ensemble vs best member
    L.append("## 4. Stacked ensemble vs its members (calibrated, %s)\n" % chosen_method)
    from .stage_d_report import assemble as _a  # noqa: F401
    ens_runs, pr_group = {}, {}
    for reading in an.readings:
        for es, esl in (("ER2", "seen families"), ("EHO", "held-out family")):
            L.append(f"\n### Reading {reading}, {esl}\n")
            L.append("| Score | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE |\n|---|---|---|---|---|---|")
            for key, name in (("m1", "M1 calibrated"), ("m2", "M2 (tuned) calibrated"), ("ens", "Stacked ensemble")):
                b = bootstrap(an.run_for(reading, es, chosen_method, key, "cal"), prev, mcfg, reps, bseed)
                ens_runs[(reading, es, key)] = b
                L.append(f"| {name} | {fmt(b['roc_auc'])} | {fmt(b['pr_auc'])} | {fmt(b['orec_fpr1'])} | {fmt(b['orec_fpr01'])} | {fmt(b['ece'])} |")
        folds = [p["fold"] for p in an.parts(reading, an.seeds[0])]
        for key in ("m1", "m2", "ens"):
            pr_group[(reading, key)] = []
            for f in folds:
                v = []
                for seed in an.seeds:
                    P = an.pooled(reading, seed, "ER2", chosen_method, fold=f)
                    w = fold_weights(P["y"], P["fold"], prev)
                    v.append(average_precision_score(P["y"], P["sc"][key], sample_weight=w))
                pr_group[(reading, key)].append(float(np.mean(v)))
    L.append("\n### Per-group PR-AUC (seed mean, R2->ER2) and the paired comparison\n")
    L.append("| Reading | Score | " + " | ".join(f"group {i+1}" for i in range(3)) + " | spread (max-min) |\n|---|---|---|---|---|---|")
    for reading in an.readings:
        for key in ("m1", "m2", "ens"):
            g = pr_group[(reading, key)]
            L.append(f"| {reading} | {key} | " + " | ".join(f"{x:.3f}" for x in g) + " | " * (3 - len(g)) + f" {max(g)-min(g):.3f} |")
    verdict = {}
    for reading in an.readings:
        pm = {k: ens_runs[(reading, "ER2", k)]["pr_auc"][0] for k in ("m1", "m2")}
        best = max(pm, key=pm.get); g = pr_group[(reading, best)]; spread = max(g) - min(g)
        imp = ens_runs[(reading, "ER2", "ens")]["pr_auc"][0] - pm[best]
        paired = [e - b for e, b in zip(pr_group[(reading, "ens")], g)]
        verdict[reading] = {"best_member": best, "ensemble_pr": ens_runs[(reading, "ER2", "ens")]["pr_auc"][0], "best_member_pr": pm[best],
                            "improvement": imp, "best_member_group_spread": spread, "beats_by_more_than_spread": bool(imp > spread),
                            "paired_group_diffs": paired}
    res["ensemble_verdict"] = verdict
    for r, v in verdict.items():
        L.append(f"\n**Reading {r}:** ensemble PR-AUC {v['ensemble_pr']:.3f} vs best member ({v['best_member'].upper()}) {v['best_member_pr']:.3f}: improvement {v['improvement']:+.3f}; "
                 f"that member's per-group spread is {v['best_member_group_spread']:.3f}; paired per-group differences {[round(x, 3) for x in v['paired_group_diffs']]}. "
                 f"**Beats its best member by more than the per-group spread: {'YES' if v['beats_by_more_than_spread'] else 'NO'}.**")
    v = verdict[P_]
    final_base = "ens" if v["beats_by_more_than_spread"] else v["best_member"]
    final_variant = choice_var[final_base]["variant"]
    res["choices"]["final_base"], res["choices"]["final_variant"] = final_base, final_variant
    L.append(f"\n**Final base by rule:** {final_base.upper()} with regime variant {final_variant}.\n")

    # ---- reliability curves
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.3))
    P = an.pooled(P_, an.seeds[0], "ER2", chosen_method); w = fold_weights(P["y"], P["fold"], prev)
    edges = np.linspace(0, 1, 11)
    def curve(s):
        b = np.clip(np.digitize(s, edges[1:-1]), 0, 9); xs, ys, ns = [], [], []
        for k in range(10):
            m = b == k
            if m.sum() > 5:
                xs.append(np.average(s[m], weights=w[m])); ys.append(np.average(P["y"][m], weights=w[m]))
        return xs, ys
    for ax, (key, name) in zip(axes, (("m1", "M1"), ("m2", "M2 (tuned)"), ("ens", "Stacked ensemble"))):
        ax.plot([0, 1], [0, 1], "k:", lw=1)
        if key != "ens":
            ax.plot(*curve(P["raw"][f"s_{key}"]), "o-", color="#d62728", label="raw")
            Pi = an.pooled(P_, an.seeds[0], "ER2", "isotonic"); 
            ax.plot(*curve(an.pooled(P_, an.seeds[0], "ER2", "platt")["sc"][key]), "s-", color="#1f77b4", label="Platt")
            ax.plot(*curve(Pi["sc"][key]), "^-", color="#2ca02c", label="isotonic")
        else:
            ax.plot(*curve(P["sc"]["ens"]), "s-", color="#1f77b4", label=f"stacked ({chosen_method} members)")
        ax.set_title(f"{name}: reliability (Reading A, R2->ER2, seed {an.seeds[0]})", fontsize=9)
        ax.set_xlabel("predicted probability (prevalence 8.35%)"); ax.set_ylabel("observed attack rate"); ax.legend(fontsize=8); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(OUT / "reliability_A.png", dpi=130); plt.close(fig)

    # ---- 5. threshold policy on the final pipeline
    tp = E["threshold_policy"]; levels = tp["danger_validation_fpr_levels"]
    L.append(f"## 5. Threshold policy for the final pipeline ({final_base.upper()}, {final_variant}, {chosen_method})\n")
    L.append("Candidate levels (validation-quantile FPR for 'dangerous'), pooled over held-out dev groups, R2->ER2:\n")
    L.append("| Reading | Level | Pooled realised FPR | Worst-group FPR | Per-group FPR | Recall |\n|---|---|---|---|---|---|")
    lvl_stats = {}
    for reading in an.readings:
        folds = [p["fold"] for p in an.parts(reading, an.seeds[0])]
        for q in levels:
            fp, rc, pg = [], [], {f: [] for f in folds}
            for seed in an.seeds:
                P = an.pooled(reading, seed, "ER2", chosen_method)
                dec = an.decisions(reading, seed, "ER2", chosen_method, final_base, final_variant, q)
                fp.append(dec[P["y"] == 0].mean()); rc.append(dec[P["y"] == 1].mean())
                for i, f in enumerate(folds):
                    m = (P["fold"] == i) & (P["y"] == 0); pg[f].append(dec[m].mean())
            gl = [float(np.mean(pg[f])) for f in folds]
            lvl_stats[(reading, q)] = {"fpr": float(np.mean(fp)), "worst": max(gl), "per_group": gl, "recall": float(np.mean(rc))}
            L.append(f"| {reading} | {q} | {np.mean(fp):.3f} | {max(gl):.3f} | {', '.join(f'{x:.3f}' for x in gl)} | {np.mean(rc):.3f} |")
    ok = [q for q in levels if lvl_stats[(P_, q)]["fpr"] <= 0.01 and lvl_stats[(P_, q)]["worst"] <= 0.02]
    chosen_q = max(ok) if ok else min(levels)
    res["choices"]["danger_validation_fpr_level"] = chosen_q
    L.append(f"\nRule (largest level with pooled FPR <= 0.01 and worst group <= 0.02 on Reading A) selects **{chosen_q}**" + ("" if ok else " (none qualified: smallest level)") + ".\n")
    L.append("### Per held-out group at the chosen policy (seed mean): verdicts = unsure | dangerous | suspicious | safe\n")
    L.append("| Reading | Set | Group | FPR dangerous (all normals) | FPR dangerous (decided only) | Recall dangerous | Recall danger+suspicious | Unsure: normals | Unsure: attacks | FPR counts-only normals |\n|---|---|---|---|---|---|---|---|---|---|")
    pol = {}
    for reading in an.readings:
        folds = [p["fold"] for p in an.parts(reading, an.seeds[0])]
        for es in ("ER2", "EHO"):
            for i, f in enumerate(folds):
                acc = {k: [] for k in ("fpr", "fpr_dec", "rec", "rec_s", "un_n", "un_a", "fpr_co")}
                for seed in an.seeds:
                    P = an.pooled(reading, seed, es, chosen_method, fold=f)
                    dq = an.decisions(reading, seed, es, chosen_method, final_base, final_variant, chosen_q, fold=f)
                    d5 = an.decisions(reading, seed, es, chosen_method, final_base, final_variant, tp["suspicious_validation_fpr"], fold=f)
                    y, oor = P["y"], P["oor"].astype(bool)
                    dang, susp = dq & ~oor, d5 & ~dq & ~oor
                    n0, n1 = y == 0, y == 1
                    co = n0 & (P["reg"] == "U0")
                    acc["fpr"].append(dang[n0].mean()); acc["fpr_dec"].append(dang[n0 & ~oor].sum() / max((n0 & ~oor).sum(), 1))
                    acc["rec"].append(dang[n1].mean()); acc["rec_s"].append((dang | susp)[n1].mean())
                    acc["un_n"].append(oor[n0].mean()); acc["un_a"].append(oor[n1].mean())
                    acc["fpr_co"].append(dang[co].mean() if co.any() else np.nan)
                m = {k: float(np.nanmean(v)) for k, v in acc.items()}; pol[(reading, es, f)] = m
                L.append(f"| {reading} | {es} | group {i+1} | {m['fpr']:.3f} | {m['fpr_dec']:.3f} | {m['rec']:.3f} | {m['rec_s']:.3f} | {m['un_n']:.3f} | {m['un_a']:.3f} | {m['fpr_co']:.3f} |")
    res["policy_per_group"] = {"|".join([r, e, f[:6]]): v for (r, e, f), v in pol.items()}
    # ---- 6. sweep of the final pipeline vs his recipe (Stage D)
    L.append("\n## 6. Effect-size sweep of the final pipeline (simulated miner signal, assumed effect sizes; recall counts unsure as a miss)\n")
    fams, sts = D["sweep"]["families"], D["sweep"]["strengths"]
    rows = []
    for reading in an.readings:
        for fam in fams:
            for st in sts:
                rec, un, rec_h = [], [], []
                for seed in an.seeds:
                    ha, hu, hh = [], [], []
                    for p in an.parts(reading, seed):
                        cell = p["sweep"].get((fam, st))
                        if cell is None:
                            continue
                        ctx = an.ctx[(reading, p["fold"], seed, chosen_method)]
                        dec = ctx.decide(cell, final_base, final_variant, chosen_q)
                        ha.append((dec & ~cell["oor"].astype(bool))); hu.append(cell["oor"].astype(bool))
                        jd = next(x for x in jobs_d if x["reading"] == reading and x["fold"] == p["fold"] and x["seed"] == seed)
                        sw = jd["sweep"][("his11", "R2")]
                        hh.append(sw["cells"][(fam, st)] > sw["thr"]["fpr"])
                    if ha:
                        rec.append(np.concatenate(ha).mean()); un.append(np.concatenate(hu).mean()); rec_h.append(np.concatenate(hh).mean())
                rows.append({"reading": reading, "family": fam, "s": st, "final_recall": np.mean(rec), "final_unsure": np.mean(un), "his_recall": np.mean(rec_h)})
    sw = pd.DataFrame(rows); sw.to_csv(OUT / "sweep_final_vs_his.csv", index=False)
    thr_ = D["sweep"]["works_threshold"]
    L.append("| Reading | Family | His recipe onset s | Final onset s | His recall s=0 | Final recall s=0 | His recall s=1 | Final recall s=1 | Final unsure at s=1.5 |\n|---|---|---|---|---|---|---|---|---|")
    for reading in an.readings:
        for fam in fams:
            x = sw[(sw.reading == reading) & (sw.family == fam)].sort_values("s")
            on = lambda c: (x[x[c] >= thr_]["s"].min() if (x[c] >= thr_).any() else np.nan)
            f_ = lambda v: "never" if pd.isna(v) else f"{v:.2f}"
            r0, r1 = x[x.s == 0.0].iloc[0], x[x.s == 1.0].iloc[0]; u15 = x[x.s == 1.5].iloc[0]["final_unsure"]
            L.append(f"| {reading} | {fam} | {f_(on('his_recall'))} | {f_(on('final_recall'))} | {r0.his_recall:.3f} | {r0.final_recall:.3f} | {r1.his_recall:.3f} | {r1.final_recall:.3f} | {u15:.3f} |")
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.8), sharey=True)
    for ax, fam in zip(axes, fams):
        x = sw[(sw.reading == P_) & (sw.family == fam)].sort_values("s")
        ax.plot(x["s"], x["his_recall"], "r-o", ms=3, label="his recipe (val-1% thr)"); ax.plot(x["s"], x["final_recall"], "b-o", ms=3, label="final pipeline (policy)")
        ax.axvspan(0, 1, color="k", alpha=.04); ax.set_title(fam + ("  [HELD-OUT]" if fam == D["generator"]["heldout_family"] else ""), fontsize=10); ax.grid(alpha=.3); ax.set_ylim(-.02, 1.02)
        ax.set_xlabel("signal strength s")
    axes[0].set_ylabel("recall"); axes[0].legend(fontsize=8)
    fig.suptitle("Reading A, simulated miner signal, assumed effect sizes", fontsize=10); fig.tight_layout(); fig.savefig(OUT / "sweep_final_A.png", dpi=130); plt.close(fig)

    (OUT / "tables.md").write_text("\n".join(L))
    (OUT / "results.json").write_text(json.dumps(res, indent=1, default=lambda o: o if not isinstance(o, np.generic) else o.item()))
    print(json.dumps(res["choices"], indent=1, default=str))


if __name__ == "__main__":
    main()
