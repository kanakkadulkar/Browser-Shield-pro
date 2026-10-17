import numpy as np
import pandas as pd
import pytest

from src.features import FEATURES, derive_rate
from src.features2 import BSP_FEATURES, build_bsp


def rows():
    up = np.array([120_000.0, 0.0, 3_600_000.0])
    dom, lag, net = np.array([600., 0., 40.]), np.array([12_000., 0., 0.]), np.array([30., 25., 900.])
    df = pd.DataFrame({"dom_mutation_count": dom, "event_loop_lag_ms": lag, "network_request_count": net,
                       "post_request_count": [3., 20., 450.], "unique_domains_contacted": [2., 1., 5.],
                       "idle_ratio": [.2, 0., 1.], "visibility_hidden": [0., 0., 1.], "visibility_changes": [1., 0., 7.]})
    df["dom_per_second"] = derive_rate(dom, up); df["lag_per_second"] = derive_rate(lag, up)
    df["network_per_second"] = derive_rate(net, up)
    return df[FEATURES]


def test_columns_and_no_nan():
    b = build_bsp(rows())
    assert list(b.columns) == BSP_FEATURES and b.notna().all().all() and np.isfinite(b.to_numpy()).all()


def test_rates_are_per_second_and_regime_is_explicit():
    b = build_bsp(rows())
    assert list(b["counts_only"]) == [0.0, 1.0, 0.0]
    assert b["lag_fraction"].iloc[0] == pytest.approx(0.1)                       # 12,000 ms of 120,000 ms
    assert b["log_net_rate"].iloc[0] == pytest.approx(np.log1p(30 / 120.0))       # per SECOND
    assert b.loc[1, ["log_uptime_s", "lag_fraction", "log_dom_rate", "log_net_rate", "log_post_rate"]].eq(0).all()
    assert b["log_net"].iloc[1] == pytest.approx(np.log1p(25.0))                  # counts kept for counts-only rows


def test_counts_only_row_is_not_off_scale():
    """His 'per second' value for a counts-only row is the raw count (25); ours must be O(1)."""
    r = rows(); assert r["network_per_second"].iloc[1] == 25.0
    assert build_bsp(r)["log_net_rate"].iloc[1] == 0.0


def test_zero_uptime_guard_all_zero_row():
    z = pd.DataFrame([dict.fromkeys(FEATURES, 0.0)])
    assert np.isfinite(build_bsp(z).to_numpy()).all()
