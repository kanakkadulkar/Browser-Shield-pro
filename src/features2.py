"""Own feature set 'bsp_v1': no unit bugs, explicit regime, log-scaled counters, nothing unused.

Input: the same 11 raw columns every dataset has. The friend's "per_second" columns are per
millisecond when uptime > 0 and plain counts when uptime == 0, so we do NOT use them as rates.
We recover the uptime from (count / rate) where it exists and recompute proper per-second rates.
Rows without a recoverable uptime ("counts-only") get an explicit indicator and rates of 0,
instead of count-valued 'rates' that are ~1000x off-scale.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .features import recover_uptime_ms

BSP_FEATURES = [
    "counts_only", "log_uptime_s", "lag_fraction", "log_dom_rate", "log_net_rate", "log_post_rate",
    "post_share", "log_dom", "log_net", "log_post", "log_lag_ms", "log_unique", "idle_ratio",
    "visibility_hidden", "log_vis_changes",
]


def build_bsp(df: pd.DataFrame) -> pd.DataFrame:
    up_ms = recover_uptime_ms(df)
    has = up_ms.notna().to_numpy()
    t_ms = np.where(has, up_ms.to_numpy(float), 1.0)          # guard: never divide by 0
    t_s = t_ms / 1000.0
    f = lambda c: df[c].to_numpy(float)
    z = lambda v: np.where(has, v, 0.0)                       # rates/uptime are 0 when unknown
    net = f("network_request_count")
    out = pd.DataFrame({
        "counts_only": (~has).astype(float),
        "log_uptime_s": z(np.log1p(t_s)),
        "lag_fraction": z(np.clip(f("event_loop_lag_ms") / t_ms, 0, 1)),
        "log_dom_rate": z(np.log1p(f("dom_mutation_count") / t_s)),
        "log_net_rate": z(np.log1p(net / t_s)),
        "log_post_rate": z(np.log1p(f("post_request_count") / t_s)),
        "post_share": np.clip(f("post_request_count") / np.maximum(net, 1.0), 0, 5),
        "log_dom": np.log1p(f("dom_mutation_count")),
        "log_net": np.log1p(net),
        "log_post": np.log1p(f("post_request_count")),
        "log_lag_ms": np.log1p(f("event_loop_lag_ms")),
        "log_unique": np.log1p(f("unique_domains_contacted")),
        "idle_ratio": f("idle_ratio"),
        "visibility_hidden": f("visibility_hidden"),
        "log_vis_changes": np.log1p(f("visibility_changes")),
    }, index=df.index)
    return out[BSP_FEATURES]
