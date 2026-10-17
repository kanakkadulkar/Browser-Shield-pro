"""Logic tests on tiny synthetic frames (no data files needed)."""
import numpy as np
import pandas as pd
import pytest

from src.data import UNKNOWN, assign_group, dedupe_exact
from src.features import FEATURES, derive_rate, recover_uptime_ms, regime
from src.splits import (assert_no_leak, assign_batches, fingerprint, lock_test_groups,
                        split_dev_test, validation_groups)


def frame(groups, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame(rng.random((len(groups), len(FEATURES))), columns=FEATURES)
    df["group"] = groups
    return df


def test_dedupe_removes_exact_duplicates_only():
    df = frame(["a"] * 4)
    df.iloc[1] = df.iloc[0]
    df.iloc[3, 0] += 1e-3                 # near-duplicate must survive
    out, n = dedupe_exact(df)
    assert n == 1 and len(out) == 3


def test_assign_group_rules():
    g = assign_group(pd.Series(["u1", "u1", "", "u2"]), pd.Series([1, 2, 0, 1]))
    assert list(g) == ["u1", UNKNOWN, UNKNOWN, "u2"]


def test_lock_test_groups_by_rank_deterministic():
    df = frame(["big"] * 5 + ["mid"] * 3 + ["tie_b"] * 2 + ["tie_a"] * 2 + [UNKNOWN] * 50)
    assert lock_test_groups(df, [1, 3]) == ["big", "tie_a"]   # unknown never a test user


def test_split_never_splits_a_group_and_has_no_vector_leak():
    df = frame(["a"] * 5 + ["b"] * 5 + [UNKNOWN] * 5)
    dev, test = split_dev_test(df, ["b"])
    assert set(test["group"]) == {"b"} and "b" not in set(dev["group"])
    assert_no_leak(dev, test)


def test_leak_detection_fires():
    df = frame(["a"] * 3 + ["b"] * 3)
    with pytest.raises(AssertionError):
        assert_no_leak(df[df.group == "a"], df)          # shared group
    t = df[df.group == "b"].copy(); t["group"] = "c"; t.iloc[0, :len(FEATURES)] = df.iloc[0, :len(FEATURES)].to_numpy()
    with pytest.raises(AssertionError):
        assert_no_leak(df[df.group == "a"], t)           # identical vector, different group


def test_validation_groups_excludes_small():
    df = frame(["a"] * 60 + ["b"] * 10 + [UNKNOWN] * 80)
    assert validation_groups(df, 50) == ["a", UNKNOWN]


def test_batches_reproducible_and_balanced():
    b1, t1 = assign_batches(1000, 20, 4, seed=42)
    b2, t2 = assign_batches(1000, 20, 4, seed=42)
    assert (b1 == b2).all() and t1 == t2 and len(t1) == 4
    assert np.bincount(b1).min() == 50


def test_fingerprint_order_independent_and_sensitive():
    df = frame(["a"] * 5)
    assert fingerprint(df) == fingerprint(df.sample(frac=1, random_state=1))
    df2 = df.copy(); df2.iloc[0, 0] += 1
    assert fingerprint(df) != fingerprint(df2)


def test_rate_convention_and_uptime_recovery():
    up = np.array([2000.0, 0.0])
    cnt = np.array([100.0, 40.0])
    rate = derive_rate(cnt, up)
    assert rate[0] == pytest.approx(0.05) and rate[1] == 40.0   # per-ms vs raw count
    df = pd.DataFrame({"dom_mutation_count": [100, 0], "dom_per_second": [rate[0], 0.0],
                       "event_loop_lag_ms": [10, 0], "lag_per_second": [10 / 2000, 0.0],
                       "network_request_count": [5, 40], "network_per_second": [5 / 2000, 40.0],
                       "post_request_count": [1, 3], "idle_ratio": [0.5, 0.0]})
    assert recover_uptime_ms(df).iloc[0] == pytest.approx(2000.0)
    assert np.isnan(recover_uptime_ms(df).iloc[1])
    assert list(regime(df)) == ["U", "U0"]
