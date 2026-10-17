"""Stage B: adversarial-validity check (synthetic attacks vs real normals).

Question: how well can a classifier tell *synthetic attack* from *real normal*
using each feature alone, and which features carry that signal? Run on DEV data
only (the locked test set is never touched), with leave-one-group-out folds so
no group is on both sides.

Run for two attack sets under each reading of "final":
  friend  : the 1,000 rows of synthetic_anomalies.csv
  rebuilt : src/synth.py injection into real dev rows (groups inherited)
"""
from __future__ import annotations

import json

import matplotlib
import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score

from .data import ROOT, dedupe_exact, load_config, load_friend_synthetic, load_normals
from .features import FEATURES, NON_SIGNAL_FEATURES, SIGNAL_FEATURES, implied_uptimes, regime
from .splits import assign_batches, build_protocol
from .synth import TIERS, generate_for_groups

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _model(seed: int) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(max_depth=3, max_iter=80, learning_rate=0.1, random_state=seed)


def _auc(y, s) -> float:
    return float(roc_auc_score(y, s)) if len(set(y)) == 2 else float("nan")


def friend_attacks(dev_normals: pd.DataFrame, val_groups: list[str], scfg: dict, seed: int) -> pd.DataFrame:
    """Friend's synthetic rows, deduped, test batches removed, dev batches mapped to val groups."""
    syn, _ = dedupe_exact(load_friend_synthetic())
    batch, test_b = assign_batches(len(syn), scfg["synthetic_batches"], scfg["synthetic_test_batches"], seed)
    syn = syn.assign(batch=batch)
    syn = syn[~syn["batch"].isin(test_b)].copy()
    sizes = dev_normals["group"].value_counts()
    w = np.array([sizes[g] for g in val_groups], float)
    rng = np.random.default_rng(seed)
    bs = sorted(syn["batch"].unique())
    # every validation group gets >=1 batch; the rest are assigned proportionally to size
    mapping = {b: val_groups[i] for i, b in enumerate(bs[:len(val_groups)])}
    for b in bs[len(val_groups):]:
        mapping[b] = val_groups[rng.choice(len(val_groups), p=w / w.sum())]
    syn["group"] = syn["batch"].map(mapping)
    return syn.drop(columns="batch").reset_index(drop=True)


def evaluate(normals: pd.DataFrame, attacks: pd.DataFrame, val_groups: list[str], seed: int) -> dict:
    """Leave-one-group-out adversarial check. Returns pooled-OOF AUCs and importances."""
    df = pd.concat([normals[FEATURES + ["group"]].assign(y=0),
                    attacks[FEATURES + ["group"]].assign(y=1)], ignore_index=True)
    if "tier" in attacks:
        df["tier"] = [None] * len(normals) + attacks["tier"].tolist()
        df["family"] = [None] * len(normals) + attacks["family"].tolist()
    y = df["y"].to_numpy()
    sets = {"all": FEATURES, "signal_only": SIGNAL_FEATURES, "non_signal_only": NON_SIGNAL_FEATURES}
    sets.update({f: [f] for f in FEATURES})
    oof = {k: np.full(len(df), np.nan) for k in sets}
    perm: list[pd.Series] = []
    fold_auc = {k: [] for k in sets}
    for g in val_groups:
        va = (df["group"] == g).to_numpy()
        tr = ~va
        if len(set(y[va])) < 2:
            continue
        for k, cols in sets.items():
            m = _model(seed).fit(df.loc[tr, cols], y[tr])
            p = m.predict_proba(df.loc[va, cols])[:, 1]
            oof[k][va] = p
            fold_auc[k].append(_auc(y[va], p))
            if k == "all":
                pi = permutation_importance(m, df.loc[va, cols], y[va], scoring="roc_auc",
                                            n_repeats=5, random_state=seed)
                perm.append(pd.Series(pi.importances_mean, index=cols))
    ok = ~np.isnan(oof["all"])
    res = {
        "n_normal": int((y == 0).sum()), "n_attack": int((y == 1).sum()),
        "folds_used": len(fold_auc["all"]),
        "auc_all": _auc(y[ok], oof["all"][ok]),
        "auc_signal_only": _auc(y[ok], oof["signal_only"][ok]),
        "auc_non_signal_only": _auc(y[ok], oof["non_signal_only"][ok]),
        "fold_auc_all": [round(a, 4) for a in fold_auc["all"]],
        "single_feature": {}, "perm_importance_auc_drop": {},
    }
    for f in FEATURES:
        rank = _auc(y[ok], df[f].to_numpy()[ok])
        res["single_feature"][f] = {"oof_tree_auc": _auc(y[ok], oof[f][ok]),
                                    "rank_auc": max(rank, 1 - rank)}
    res["perm_importance_auc_drop"] = pd.concat(perm, axis=1).mean(axis=1).sort_values(ascending=False).round(4).to_dict()
    if "tier" in df:
        res["by_tier"] = {}
        for t in TIERS:
            m = ok & ((df["tier"] == t) | (df["y"] == 0)).to_numpy()
            res["by_tier"][t] = {
                "n_attack": int(((df["tier"] == t) & ok).sum()),
                "auc_all": _auc(y[m], oof["all"][m]),
                "auc_non_signal_only": _auc(y[m], oof["non_signal_only"][m]),
                "max_single_feature_oof_auc": max(_auc(y[m], oof[f][m]) for f in FEATURES),
                "best_single_feature": max(FEATURES, key=lambda f: _auc(y[m], oof[f][m])),
            }
        res["by_family_auc_all"] = {}
        for fam in sorted(attacks["family"].unique()):
            m = ok & ((df["family"] == fam) | (df["y"] == 0)).to_numpy()
            res["by_family_auc_all"][fam] = _auc(y[m], oof["all"][m])
    return res


def structure_report(real: pd.DataFrame, sets: dict[str, pd.DataFrame]) -> dict:
    """Cross-feature fingerprints: do the three rates share one uptime? regime mix? out-of-range?"""
    hi = real[FEATURES].max()
    p999 = real[FEATURES].quantile(0.999)
    out = {}
    for name, d in {"real_normal": real, **sets}.items():
        reg = regime(d)
        t = implied_uptimes(d[reg == "U"]).dropna(thresh=2)
        spread = (t.max(axis=1) / t.min(axis=1) - 1).abs()
        out[name] = {
            "rows": len(d),
            "regime_share": {k: round(float(v), 4) for k, v in reg.value_counts(normalize=True).items()},
            "rates_share_one_uptime": round(float((spread < 1e-2).mean()), 4) if len(t) else None,
            "rows_with_any_feature_above_real_max": round(float((d[FEATURES] > hi).any(axis=1).mean()), 4),
            "rows_with_any_feature_above_real_p99.9": round(float((d[FEATURES] > p999).any(axis=1).mean()), 4),
        }
    return out


def main() -> dict:
    cfg, scfg = load_config(), load_config("split")
    synth_cfg = yaml.safe_load(open(ROOT / "configs" / "synth.yaml"))
    seed = cfg["seed"]
    a, sa = load_normals("A"); b, sb = load_normals("B")
    proto = build_protocol(a, b)
    results = {"seed": seed, "test_groups_locked": proto["test_groups"], "readings": {}}
    for r in ("A", "B"):
        d = proto["readings"][r]
        dev, vg = d["dev"], d["val_groups"]
        fr = friend_attacks(dev, vg, scfg, seed)
        rb = generate_for_groups(dev, synth_cfg, synth_cfg["attack_to_normal_ratio"], seed)
        results["readings"][r] = {
            "dev_normals": len(dev), "validation_folds": vg,
            "friend": evaluate(dev, fr, vg, seed),
            "rebuilt": evaluate(dev, rb, vg, seed),
            "structure": structure_report(dev, {"friend_synthetic": fr, "rebuilt_synthetic": rb}),
            "rebuilt_family_counts": rb["family"].value_counts().to_dict(),
            "rebuilt_tier_counts": rb["tier"].value_counts().to_dict(),
        }
    out = ROOT / "reports" / "stage_b"
    out.mkdir(parents=True, exist_ok=True)
    (out / "adversarial_validity.json").write_text(json.dumps(results, indent=2, default=float))
    _figure(results, out / "single_feature_leakage.png")
    _tables(results, out / "summary.md")
    return results


def _figure(res: dict, path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for ax, r in zip(axes, ("A", "B")):
        x = np.arange(len(FEATURES)); w = 0.4
        ax.barh(x - w / 2, [res["readings"][r]["friend"]["single_feature"][f]["oof_tree_auc"] for f in FEATURES],
                w, label="friend's synthetic", color="#c0504d")
        ax.barh(x + w / 2, [res["readings"][r]["rebuilt"]["single_feature"][f]["oof_tree_auc"] for f in FEATURES],
                w, label="rebuilt (injection)", color="#4f81bd")
        ax.axvline(0.5, color="k", lw=0.8, ls=":"); ax.axvline(0.8, color="gray", lw=0.8, ls="--")
        ax.set_yticks(x); ax.set_yticklabels(FEATURES); ax.invert_yaxis(); ax.set_xlim(0.4, 1.0)
        ax.set_title(f"Reading {r}: single-feature synthetic-vs-real AUC\n(leave-one-group-out, dev only)")
        ax.set_xlabel("OOF ROC-AUC (0.5 = indistinguishable)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, frameon=False)
    fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig(path, dpi=130); plt.close(fig)


def _tables(res: dict, path) -> None:
    L = []
    for r in ("A", "B"):
        R = res["readings"][r]
        L += [f"## Reading {r}  (dev normals {R['dev_normals']}, validation folds {len(R['validation_folds'])})", "",
              "| feature | friend: tree AUC | friend: rank AUC | rebuilt: tree AUC | rebuilt: rank AUC |", "|---|---|---|---|---|"]
        for f in FEATURES:
            fr, rb = R["friend"]["single_feature"][f], R["rebuilt"]["single_feature"][f]
            L.append(f"| {f} | {fr['oof_tree_auc']:.3f} | {fr['rank_auc']:.3f} | {rb['oof_tree_auc']:.3f} | {rb['rank_auc']:.3f} |")
        L += ["", "| model | friend | rebuilt |", "|---|---|---|"]
        for k, lab in (("auc_all", "all 11 features"), ("auc_signal_only", "signal channels only"),
                       ("auc_non_signal_only", "non-signal channels only")):
            L.append(f"| {lab} | {R['friend'][k]:.3f} | {R['rebuilt'][k]:.3f} |")
        L += ["", "Rebuilt, by strength tier:", "", "| tier | attacks | all-feature AUC | non-signal AUC | best single feature (AUC) |", "|---|---|---|---|---|"]
        for t, v in R["rebuilt"]["by_tier"].items():
            L.append(f"| {t} | {v['n_attack']} | {v['auc_all']:.3f} | {v['auc_non_signal_only']:.3f} | {v['best_single_feature']} ({v['max_single_feature_oof_auc']:.3f}) |")
        L.append("")
    path.write_text("\n".join(L))


if __name__ == "__main__":
    main()
    print((ROOT / "reports" / "stage_b" / "summary.md").read_text())
