"""Group-aware evaluation splits. Test groups are locked by rule, not by peeking.

Protocol (configs/split.yaml):
  * exact duplicates are removed BEFORE any split (src/data.py)
  * test = whole user groups chosen by size rank; never split a group
  * dev folds = leave-one-group-out over dev groups with >= min_fold_rows
  * the unknown_source group is one indivisible group
"""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from .data import UNKNOWN, load_config, vector_key
from .features import FEATURES


def lock_test_groups(normals_a: pd.DataFrame, ranks: list[int]) -> list[str]:
    """Pick test user groups by rank (1 = largest) in the largest reading (A).

    Ties are broken by group name so the rule is deterministic.
    """
    sizes = normals_a[normals_a["group"] != UNKNOWN]["group"].value_counts()
    order = sorted(sizes.items(), key=lambda kv: (-kv[1], kv[0]))
    return [order[r - 1][0] for r in ranks]


def split_dev_test(df: pd.DataFrame, test_groups: list[str], group_col: str = "group"
                   ) -> tuple[pd.DataFrame, pd.DataFrame]:
    is_test = df[group_col].isin(test_groups)
    return df[~is_test].reset_index(drop=True), df[is_test].reset_index(drop=True)


def validation_groups(dev: pd.DataFrame, min_rows: int, group_col: str = "group") -> list[str]:
    """Dev groups big enough to serve as a validation fold (leave-one-group-out)."""
    sizes = dev[group_col].value_counts()
    return sorted(g for g, n in sizes.items() if n >= min_rows)


def assign_batches(n: int, n_batches: int, n_test: int, seed: int) -> tuple[np.ndarray, set[int]]:
    """Random pseudo-groups for rows with no provenance (friend's synthetic CSV)."""
    rng = np.random.default_rng(seed)
    batch = rng.permutation(n) % n_batches
    test = set(rng.permutation(n_batches)[:n_test].tolist())
    return batch, test


def assert_no_leak(train: pd.DataFrame, test: pd.DataFrame, group_col: str = "group",
                   cols: list[str] = FEATURES) -> None:
    """Fail loudly if a group or an exact feature vector is on both sides."""
    both = set(train[group_col]) & set(test[group_col])
    assert not both, f"groups on both sides: {sorted(both)}"
    shared = set(vector_key(train, cols)) & set(vector_key(test, cols))
    assert not shared, f"{len(shared)} identical feature vectors on both sides"


def fingerprint(df: pd.DataFrame, cols: list[str] = FEATURES) -> str:
    """Order-independent hash of a row set, to detect an accidentally changed test set."""
    keys = sorted(map(repr, vector_key(df, cols)))
    return hashlib.sha256("\n".join(keys).encode()).hexdigest()[:16]


def build_protocol(normals_a: pd.DataFrame, normals_b: pd.DataFrame, cfg: dict | None = None) -> dict:
    """Locked protocol summary for both readings (used by reports and tests)."""
    sc = cfg or load_config("split")
    test_groups = lock_test_groups(normals_a, sc["test_user_ranks"])
    out = {"test_groups": test_groups, "readings": {}}
    for name, df in (("A", normals_a), ("B", normals_b)):
        dev, test = split_dev_test(df, test_groups)
        assert_no_leak(dev, test)
        out["readings"][name] = {
            "dev": dev, "test": test,
            "val_groups": validation_groups(dev, sc["min_fold_rows"]),
            "test_fingerprint": fingerprint(test),
        }
    return out
