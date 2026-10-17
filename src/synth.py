"""Anomaly-injection generator for simulated miner workload (and benign-heavy negatives).

Each synthetic row starts from a REAL normal row of the same group, so the joint
structure of every channel we do not touch (DOM, idle, visibility, ...) stays
real, and the row inherits that row's group (no cross-split leakage). Only the
channels in cfg["families"] are modified, then the three rate features are
recomputed with the collector's own convention (src/features.derive_rate).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .features import FEATURES, derive_rate, recover_uptime_ms, regime

TIERS = ("weak", "medium", "strong")


def _interp(rng, lo: float, hi: float, s: np.ndarray) -> np.ndarray:
    """Geometric interpolation lo->hi by strength s (linear if lo == 0)."""
    if hi == lo:
        return np.full_like(s, lo, dtype=float)
    if lo > 0:
        return lo * (hi / lo) ** s
    return hi * s


def _tier(s: np.ndarray) -> np.ndarray:
    return np.where(s < 1 / 3, TIERS[0], np.where(s < 2 / 3, TIERS[1], TIERS[2]))


def _inject(base: pd.DataFrame, T: np.ndarray, p: dict, s: np.ndarray, rng,
            dom_mult: np.ndarray | None = None, borrow_T: np.ndarray | None = None) -> pd.DataFrame:
    """Apply one family's effect to base rows (vectorised). T = uptime ms (NaN for U0).

    Counts-only (U0) rows have no uptime, yet cumulative request counts scale with uptime.
    v1 borrowed one from the other rows of the *batch*; a counts-only family's batch contains
    only counts-only rows, so nothing could be borrowed and it fell back to a constant 60 s
    (bug). v2 (`borrow_T` given) draws a PER-ROW uptime from the group's observed uptimes."""
    n = len(base)
    out = base[FEATURES].copy().astype(float)
    has_t = ~np.isnan(T)
    d_lag = _interp(rng, *p["d_lag"], s)
    rate = _interp(rng, *p["pool_per_min"], s) * rng.lognormal(0.0, 0.2, n)
    share = p["post_share"][0] + rng.random(n) * (p["post_share"][1] - p["post_share"][0])
    d_unique = np.maximum(0, np.floor(p["d_unique"][0] + s * (p["d_unique"][1] - p["d_unique"][0])
                                      + rng.random(n))).astype(int)

    # Uptime used to scale cumulative request counts (U0 rows have none: borrow one).
    if borrow_T is not None and not has_t.all():
        t_eff = np.where(has_t, T, rng.choice(borrow_T, n))                      # v2
    else:
        t_eff = np.where(has_t, T, rng.choice(T[has_t], n) if has_t.any() else 60000.0)  # v1 (unchanged)
    reqs = np.round(rate * t_eff / 60000.0)
    posts = np.minimum(reqs, np.round(reqs * share))

    lag_frac = np.where(has_t, out["event_loop_lag_ms"].to_numpy() / np.where(has_t, T, 1.0), 0.0)
    new_frac = np.minimum(0.95, lag_frac + d_lag)
    out["event_loop_lag_ms"] = np.where(has_t, np.round(new_frac * np.where(has_t, T, 1.0)),
                                        out["event_loop_lag_ms"])
    if dom_mult is not None:
        out["dom_mutation_count"] = np.round(out["dom_mutation_count"] * dom_mult)
    out["network_request_count"] += reqs
    out["post_request_count"] += posts
    out["unique_domains_contacted"] += d_unique

    up = np.where(has_t, T, 0.0)
    out["dom_per_second"] = derive_rate(out["dom_mutation_count"], up)
    out["lag_per_second"] = derive_rate(out["event_loop_lag_ms"], up)
    out["network_per_second"] = derive_rate(out["network_request_count"], up)
    return out


def generate(bases: pd.DataFrame, n: int, cfg: dict, seed: int, kind: str = "attack",
             family: str | None = None, strength: float | None = None,
             keep_unchanged: bool = False, version: int | None = None,
             exclude_families: tuple = ()) -> pd.DataFrame:
    """Generate n synthetic rows from `bases` (real normals of ONE group set).

    kind='attack' -> label 1 with the miner families; kind='benign_heavy' -> label 0.
    Sweep options (default None = the standard generator, unchanged): `family` forces one
    family; `strength` fixes s for every row (s<0 extrapolates below the weakest standard
    effect, s>1 above the strongest). `keep_unchanged=True` keeps rows whose injected effect
    rounded to nothing (they are then identical to a real normal row: an undetectable miner);
    the sweep needs them, otherwise the weak end would be biased to the largest effects.
    Used only by the Stage C effect-size sweep.
    `version` 1 (default; or cfg["version"]) keeps the original uptime fallback; 2 fixes ONLY that
    (see _inject). `exclude_families` drops families from the mixture (Stage D hold-out).
    Returns FEATURES + group, family, strength, tier, label. Rows whose vector
    ends up identical to their base (no effective change) are dropped, so the
    result can have slightly fewer than n rows.
    """
    rng = np.random.default_rng(seed)
    b = bases.reset_index(drop=True)
    T_all = recover_uptime_ms(b).to_numpy()
    reg = regime(b).to_numpy()
    elig_U = np.where((reg == "U") & (T_all >= cfg["min_uptime_ms"]))[0]
    elig_U0 = np.where(reg == "U0")[0]
    ver = version if version is not None else cfg.get("version", 1)
    borrow = T_all[elig_U] if ver == 2 else None

    if kind == "attack":
        fams = cfg["families"]
        names = [family] if family else [k for k in fams if k not in exclude_families]
        w = np.array([fams[k]["weight"] for k in names], float)
        # a family needing a regime with no eligible base rows is folded into the first U family
        fam_idx = rng.choice(len(names), n, p=w / w.sum())
        for i, k in enumerate(names):
            if fams[k]["regime"] == "U0" and len(elig_U0) == 0:
                fam_idx[fam_idx == i] = next(j for j, m in enumerate(names) if fams[m]["regime"] == "U")
    else:
        names, fam_idx = ["benign_heavy"], np.zeros(n, int)
    if len(elig_U) == 0:
        return pd.DataFrame(columns=FEATURES + ["group", "family", "strength", "tier", "label"])

    pieces = []
    for i, k in enumerate(names):
        m = int((fam_idx == i).sum())
        if m == 0:
            continue
        p = cfg["families"][k] if kind == "attack" else cfg["benign_heavy"]
        pool = elig_U0 if (kind == "attack" and p["regime"] == "U0") else elig_U
        idx = rng.choice(pool, m)
        s = rng.random(m) if strength is None else np.full(m, float(strength))
        T = np.where(reg[idx] == "U", T_all[idx], np.nan)
        dm = None if kind == "attack" else _interp(rng, *p["dom_mult"], s)
        gen = _inject(b.iloc[idx], T, p, s, rng, dm, borrow)
        changed = (gen.to_numpy() != b.iloc[idx][FEATURES].to_numpy(float)).any(axis=1)
        if keep_unchanged:
            changed = np.ones_like(changed)
        gen = gen[changed]
        gen["group"] = b.iloc[idx]["group"].to_numpy()[changed]
        gen["family"] = k
        gen["strength"] = s[changed]
        gen["tier"] = _tier(s[changed])
        gen["label"] = 1 if kind == "attack" else 0
        pieces.append(gen)
    return pd.concat(pieces, ignore_index=True)


def generate_for_groups(normals: pd.DataFrame, cfg: dict, ratio: float, seed: int,
                        kind: str = "attack", **kw) -> pd.DataFrame:
    """Per-group generation: attacks for group g come only from group g's real rows."""
    parts = []
    for j, (g, df) in enumerate(sorted(normals.groupby("group"))):
        n = int(round(ratio * len(df)))
        if n:
            parts.append(generate(df, n, cfg, seed + j, kind, **kw))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
