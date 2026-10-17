"""Feature schema and the collector's rate convention.

The friend's collector derives three "per_second" features as
    rate = count / page_uptime_ms     if page_uptime_ms > 0
    rate = count                      otherwise
(measured: matches 96-99% of raw rows). So the "per second" values are really
per *millisecond* when uptime > 0 and a plain count when it is 0. The two
regimes differ by ~1000x, which is why we re-implement the convention here
instead of "cleaning" it: the baseline must see the data as his model did.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FEATURES: list[str] = [
    "idle_ratio", "lag_per_second", "dom_per_second", "network_per_second",
    "event_loop_lag_ms", "dom_mutation_count", "network_request_count",
    "post_request_count", "unique_domains_contacted",
    "visibility_hidden", "visibility_changes",
]

# (count column, derived rate column), all divided by the same uptime.
RATE_PAIRS: list[tuple[str, str]] = [
    ("dom_mutation_count", "dom_per_second"),
    ("event_loop_lag_ms", "lag_per_second"),
    ("network_request_count", "network_per_second"),
]

# Channels where a miner would plausibly leave a trace (assumption, documented
# in docs/STAGE_B_REPORT.md) vs. channels our generator leaves untouched.
SIGNAL_FEATURES = ["lag_per_second", "event_loop_lag_ms", "network_per_second",
                   "network_request_count", "post_request_count",
                   "unique_domains_contacted"]
NON_SIGNAL_FEATURES = [f for f in FEATURES if f not in SIGNAL_FEATURES]

# Smallest uptime (ms) accepted when recovering uptime from count/rate.
MIN_UPTIME_MS = 1.0


def derive_rate(count: np.ndarray, uptime_ms: np.ndarray) -> np.ndarray:
    """Collector convention: count/uptime_ms if uptime>0 else the raw count."""
    count = np.asarray(count, dtype=float)
    up = np.asarray(uptime_ms, dtype=float)
    pos = up > 0
    return np.where(pos, count / np.where(pos, up, 1.0), count)


def implied_uptimes(df: pd.DataFrame) -> pd.DataFrame:
    """Uptime implied by each (count, rate) pair; NaN where undefined.

    In the uptime>0 regime all three agree (same denominator). In the uptime==0
    regime rate == count so the implied value is exactly 1 and is discarded.
    """
    out = {}
    for count, rate in RATE_PAIRS:
        c, r = df[count].to_numpy(float), df[rate].to_numpy(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where((c > 0) & (r > 0), c / r, np.nan)
        out[count] = np.where(t > MIN_UPTIME_MS * 1.5, t, np.nan)
    return pd.DataFrame(out, index=df.index)


def recover_uptime_ms(df: pd.DataFrame) -> pd.Series:
    """Best-effort uptime (ms) per row; NaN when it cannot be recovered."""
    t = implied_uptimes(df)
    return t.bfill(axis=1).iloc[:, 0]


def regime(df: pd.DataFrame) -> pd.Series:
    """'U' uptime>0 (uptime recoverable) | 'U0' counts-only | 'zero' | 'other'."""
    up = recover_uptime_ms(df)
    u0 = (df["dom_mutation_count"] == 0) & (df["event_loop_lag_ms"] == 0) & \
         (df["idle_ratio"] == 0) & (df["network_request_count"] > 0)
    allzero = (df[["dom_mutation_count", "event_loop_lag_ms",
                   "network_request_count", "post_request_count"]] == 0).all(axis=1)
    r = np.where(up.notna(), "U", np.where(u0, "U0", np.where(allzero, "zero", "other")))
    return pd.Series(r, index=df.index, name="regime")
