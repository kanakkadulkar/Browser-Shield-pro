"""Fails if the frozen final pipeline config changes after it was locked (see src/stage_e_freeze.py)."""
import hashlib
import json

import pytest
import yaml

from src.data import ROOT

FINAL = ROOT / "configs" / "stage_e_final.yaml"
LOCK = ROOT / "configs" / "stage_e_final.lock"
pytestmark = pytest.mark.skipif(not LOCK.exists(), reason="final config not frozen yet")


def test_final_config_matches_lock():
    lock = json.loads(LOCK.read_text())
    assert hashlib.sha256(FINAL.read_bytes()).hexdigest() == lock["sha256"], \
        "configs/stage_e_final.yaml changed after the freeze"


def test_lock_ties_to_the_locked_test_set():
    lock = json.loads(LOCK.read_text())
    split = json.loads((ROOT / "configs" / "split.lock.json").read_text())
    assert lock["test_fingerprint"] == split["test_fingerprint"]


def test_final_config_is_complete_and_inherits_frozen_rules():
    cfg = yaml.safe_load(FINAL.read_text())
    for k in ("pipeline", "generator", "features", "training", "final_evaluation_plan", "evidence"):
        assert k in cfg
    p = cfg["pipeline"]
    assert p["final_model"] in ("m1", "m2", "ens") and p["calibration"]["method"] in ("platt", "isotonic")
    assert p["regime_handling"]["variant"] in ("V0", "Va", "Vb", "Vab")
    assert cfg["generator"]["version"] == 2 and cfg["generator"]["heldout_family"] == "throttled"
    # the pre-registered rules and the Stage D config it depends on must be unchanged since the freeze
    ev = cfg["evidence"]
    assert hashlib.sha256((ROOT / "configs" / "stage_e.yaml").read_bytes()).hexdigest() == ev["stage_e_rules_sha256"]
    assert hashlib.sha256((ROOT / "configs" / "stage_d.yaml").read_bytes()).hexdigest() == ev["stage_d_config_sha256"]
    assert cfg["final_evaluation_plan"]["single_evaluation"] is True
