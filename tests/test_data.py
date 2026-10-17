"""Tests on the real de-identified files. Skipped if data/raw is absent."""
import re

import pandas as pd
import pytest

from src.data import ROOT, UNKNOWN, load_config, load_friend_synthetic, load_normals
from src.features import FEATURES
from src.splits import assert_no_leak, build_protocol

RAW = ROOT / "data" / "raw"
pytestmark = pytest.mark.skipif(not (RAW / "MANIFEST.json").exists(), reason="de-identified data not present")


def test_no_identifiers_in_deidentified_files():
    forbidden = {"user_id", "domain", "timestamp", "cpu_cores", "memory_available"}
    uuid = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}")
    for f in RAW.glob("*.csv"):
        df = pd.read_csv(f)
        assert not forbidden & set(df.columns), f.name
        text = f.read_text()
        assert not uuid.search(text), f.name
        assert not re.search(r"[A-Za-z0-9-]+\.(com|in|org|net|io)\b", text), f.name


@pytest.mark.parametrize("reading", ["A", "B"])
def test_normals_deduped_with_groups(reading):
    df, st = load_normals(reading)
    assert not df.duplicated(subset=FEATURES).any()
    assert df["group"].notna().all() and st["rows_after"] <= st["rows_before"]


def test_unknown_group_is_one_group():
    df, _ = load_normals("A")
    assert (df["group"] == UNKNOWN).sum() > 0 and df["group"].nunique() >= 4


def test_protocol_no_leak_and_same_test_groups_across_readings():
    a, _ = load_normals("A"); b, _ = load_normals("B")
    p = build_protocol(a, b)
    for r in ("A", "B"):
        dev, test = p["readings"][r]["dev"], p["readings"][r]["test"]
        assert_no_leak(dev, test)
        assert UNKNOWN not in set(test["group"])
    # reading B's test rows are a subset of reading A's test rows
    ta = set(map(tuple, p["readings"]["A"]["test"][FEATURES].round(6).to_numpy()))
    tb = set(map(tuple, p["readings"]["B"]["test"][FEATURES].round(6).to_numpy()))
    assert tb <= ta


def test_friend_synthetic_shape():
    s = load_friend_synthetic()
    assert list(s.columns) == FEATURES and len(s) == 1000 and not s.duplicated().any()


def test_locked_test_set_unchanged():
    import json
    lock = json.loads((ROOT / "configs" / "split.lock.json").read_text())
    a, _ = load_normals("A"); b, _ = load_normals("B")
    p = build_protocol(a, b)
    for r in ("A", "B"):
        assert p["readings"][r]["test_fingerprint"] == lock["test_fingerprint"]
        assert len(p["readings"][r]["test"]) == lock["test_rows"]
        assert len(p["readings"][r]["dev"]) == lock["dev_rows"][r]
