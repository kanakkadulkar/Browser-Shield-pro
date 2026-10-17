import numpy as np
import pandas as pd
import pytest
import yaml

from src.data import ROOT
from src.features import FEATURES, derive_rate, implied_uptimes, regime
from src.synth import generate, generate_for_groups


@pytest.fixture(scope="module")
def cfg():
    return yaml.safe_load(open(ROOT / "configs" / "synth.yaml"))


def make_normals(n=300, seed=0, group="g"):
    rng = np.random.default_rng(seed)
    T = rng.uniform(2e5, 5e6, n)                       # ms
    dom = rng.integers(0, 5000, n).astype(float)
    lag = np.round(rng.uniform(0, 0.05, n) * T)
    net = rng.integers(1, 200, n).astype(float)
    df = pd.DataFrame({
        "idle_ratio": rng.random(n), "event_loop_lag_ms": lag, "dom_mutation_count": dom,
        "network_request_count": net, "post_request_count": np.floor(net * rng.random(n) * .3),
        "unique_domains_contacted": rng.integers(1, 6, n).astype(float),
        "visibility_hidden": rng.integers(0, 2, n).astype(float),
        "visibility_changes": rng.integers(0, 9, n).astype(float)})
    df["dom_per_second"] = derive_rate(dom, T)
    df["lag_per_second"] = derive_rate(lag, T)
    df["network_per_second"] = derive_rate(net, T)
    df["group"] = group
    return df[FEATURES + ["group"]]


def test_attacks_keep_invariants_and_group(cfg):
    base = make_normals(group="g1")
    a = generate(base, 400, cfg, seed=1)
    assert len(a) > 300 and set(a["group"]) == {"g1"} and (a["label"] == 1).all()
    assert (a["post_request_count"] <= a["network_request_count"]).all()
    assert a["idle_ratio"].between(0, 1).all()
    assert set(a["tier"]) <= {"weak", "medium", "strong"}


def test_rates_stay_consistent_with_uptime(cfg):
    a = generate(make_normals(), 300, cfg, seed=2)
    a = a[regime(a) == "U"]
    t = implied_uptimes(a).dropna(thresh=2)
    spread = (t.max(axis=1) / t.min(axis=1) - 1).abs()
    assert (spread < 1e-2).mean() > 0.95     # all three rates share one denominator


def test_deterministic_and_group_inheritance(cfg):
    n = pd.concat([make_normals(200, 0, "g1"), make_normals(200, 5, "g2")], ignore_index=True)
    a1 = generate_for_groups(n, cfg, 0.25, seed=7)
    a2 = generate_for_groups(n, cfg, 0.25, seed=7)
    pd.testing.assert_frame_equal(a1, a2)
    # an attack of group g only ever differs from some g row on the injected channels
    g1 = n[n.group == "g1"]
    keep = ["dom_mutation_count", "idle_ratio", "visibility_hidden", "visibility_changes", "dom_per_second"]
    base_keys = set(map(tuple, g1[keep].round(6).to_numpy()))
    ag = a1[a1.group == "g1"]
    assert all(tuple(r) in base_keys for r in ag[keep].round(6).to_numpy())


def test_no_attack_identical_to_a_normal_vector(cfg):
    base = make_normals()
    a = generate(base, 500, cfg, seed=3)
    keys = set(map(tuple, base[FEATURES].round(6).to_numpy()))
    assert not any(tuple(r) in keys for r in a[FEATURES].round(6).to_numpy())


def test_benign_heavy_is_label_zero(cfg):
    b = generate(make_normals(), 100, cfg, seed=4, kind="benign_heavy")
    assert (b["label"] == 0).all() and (b["family"] == "benign_heavy").all()


def test_sweep_options_do_not_change_default_and_keep_weak_rows(cfg):
    import hashlib
    base = make_normals()
    a = generate(base, 400, cfg, seed=1)
    # fixed reference produced before the sweep options existed
    assert hashlib.md5(a.round(6).to_csv().encode()).hexdigest()[:10] == "5d718c0c6f"
    weak = generate(base, 200, cfg, seed=1, family="worker_pool", strength=-2.0, keep_unchanged=True)
    assert len(weak) == 200 and set(weak["family"]) == {"worker_pool"} and (weak["strength"] == -2.0).all()
    dropped = generate(base, 200, cfg, seed=1, family="worker_pool", strength=-2.0)
    assert len(dropped) < 200


# ---------------------------------------------------------------- generator v2
def _with_u0(n=300, seed=0):
    """Normals that include counts-only rows (regime U0) so network_only has bases."""
    base = make_normals(n, seed)
    u0 = base.sample(60, random_state=1).copy()
    for c in ("dom_mutation_count", "event_loop_lag_ms", "idle_ratio", "dom_per_second", "lag_per_second"):
        u0[c] = 0.0
    u0["network_per_second"] = u0["network_request_count"]       # counts-only convention
    return pd.concat([base, u0], ignore_index=True)


def test_v2_config_differs_from_v1_only_by_version_line():
    v1 = (ROOT / "configs" / "synth.yaml").read_text().splitlines()
    v2 = (ROOT / "configs" / "synth_v2.yaml").read_text().splitlines()
    extra = [l for l in v2 if l not in v1]
    assert len(extra) == 1 and extra[0].startswith("version: 2")
    assert all(l in v2 for l in v1)


def test_v2_changes_only_network_only(cfg):
    base = _with_u0()
    a1 = generate(base, 1500, cfg, seed=5, version=1)
    a2 = generate(base, 1500, cfg, seed=5, version=2)
    keep = lambda d: d[d.family != "network_only"].reset_index(drop=True)
    pd.testing.assert_frame_equal(keep(a1), keep(a2))              # other families bit-identical
    n1, n2 = a1[a1.family == "network_only"], a2[a2.family == "network_only"]
    assert len(n1) > 50 and len(n2) > 50
    # the base counts dominate the median on toy data; the injected traffic shows in the tail
    assert n2["network_request_count"].median() > 1.3 * n1["network_request_count"].median()
    assert n2["network_request_count"].quantile(.9) > 3 * n1["network_request_count"].quantile(.9)


def test_v1_default_is_unchanged_by_v2_code(cfg):
    import hashlib
    a = generate(make_normals(), 400, cfg, seed=1)
    assert hashlib.md5(a.round(6).to_csv().encode()).hexdigest()[:10] == "5d718c0c6f"


def test_v2_uses_per_row_uptime_not_constant(cfg):
    base = _with_u0()
    a2 = generate(base, 3000, cfg, seed=7, family="network_only", strength=1.0, version=2)
    added_spread = a2["network_request_count"].std() / max(a2["network_request_count"].mean(), 1)
    a1 = generate(base, 3000, cfg, seed=7, family="network_only", strength=1.0, version=1)
    assert a2["network_request_count"].quantile(.9) > 5 * a1["network_request_count"].quantile(.9)
    assert added_spread > 0.5


def test_exclude_families(cfg):
    a = generate(_with_u0(), 800, cfg, seed=2, exclude_families=("throttled",))
    assert "throttled" not in set(a["family"]) and len(set(a["family"])) == 3
