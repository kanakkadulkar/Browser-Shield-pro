"""Freeze the final pipeline BEFORE the locked test set is touched.

Reads the choices that the pre-registered rules (configs/stage_e.yaml) produced on dev data, writes
configs/stage_e_final.yaml, and a lock file with its SHA-256. tests/test_stage_e_freeze.py fails if the
final config changes afterwards. The final-evaluation script does not exist yet and is not run here.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date

import yaml

from .data import ROOT


def sha(path) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    E = yaml.safe_load(open(ROOT / "configs" / "stage_e.yaml"))
    D = yaml.safe_load(open(ROOT / "configs" / "stage_d.yaml"))
    res = json.load(open(ROOT / "reports" / "stage_e" / "results.json"))
    ch = res["choices"]
    base, variant = ch["final_base"], ch["final_variant"]
    split_lock = json.load(open(ROOT / "configs" / "split.lock.json"))
    final = {
        "status": "FROZEN. Written after Stage E dev results and BEFORE the locked test set was touched. Do not edit.",
        "frozen_on": str(date.today()),
        "evidence": {"stage_e_rules": "configs/stage_e.yaml", "stage_e_rules_sha256": sha(ROOT / "configs" / "stage_e.yaml"),
                     "stage_d_config_sha256": sha(ROOT / "configs" / "stage_d.yaml"),
                     "dev_results": "reports/stage_e/results.json", "dev_results_sha256": sha(ROOT / "reports" / "stage_e" / "results.json"),
                     "selection": ch},
        "data": {"primary_reading": "A", "also_report": ["B"], "test_fingerprint": split_lock["test_fingerprint"],
                 "test_groups": "the two locked user groups (rank 2 and 4 by size in Reading A); same 928 real normals under both readings",
                 "dedupe_before_split": True},
        "generator": {"version": 2, "config": "configs/synth_v2.yaml", "heldout_family": D["generator"]["heldout_family"],
                      "train_families": D["generator"]["train_families"], "train_attack_ratio": D["honest"]["train_attack_ratio"],
                      "label": "SIMULATED MINER SIGNAL, assumed effect sizes"},
        "features": {"name": "bsp_v1", "module": "src/features2.py"},
        "pipeline": {
            "final_model": base,
            "members": (["m1", "m2"] if base == "ens" else [base]),
            "m1": {"library": "xgboost", "tuning": {"trials": D["m1"]["trials"], "space": D["m1"]["space"], "objective": D["m1"]["objective"]},
                   "early_stopping_rounds": D["m1"]["early_stopping_rounds"]},
            "m2": {"tuning": {"trials": E["m2_tuned"]["trials"], "space": E["m2_tuned"]["space"], "objective": E["m2_tuned"]["objective"]},
                   "final_fit": E["m2_tuned"]["final_fit"]},
            "calibration": {"method": ch["calibration"], "fit_on": "validation only"},
            "ensemble": ({"stacker": E["ensemble"]["stacker"]} if base == "ens" else None),
            "regime_handling": {"variant": variant, "counts_only_model": E["regime"]["counts_only_model"],
                                "regime_threshold_min_val_normals": E["regime"]["regime_threshold_min_val_normals"],
                                "calibrator_min_val_attacks": E["regime"]["calibrator_min_val_attacks"]},
            "threshold_policy": {"danger_validation_fpr": ch["danger_validation_fpr_level"],
                                 "suspicious_validation_fpr": E["threshold_policy"]["suspicious_validation_fpr"],
                                 "thresholds_fit_on": "validation normals of the training side only",
                                 "unsure": E["threshold_policy"]["unsure"]},
        },
        "training": {"seeds": E["seeds"], "train_on": "all DEV groups (no held-out dev group)",
                     "inner_validation": "smallest remaining dev group with >= 50 rows if at least two such groups remain, else a random 20%",
                     "hyperparameters": "re-tuned with the frozen procedure on the final training side, per seed",
                     "his_recipe_comparator": "trained on the same training side and attacks (R2, held-out family excluded), evaluated on the same test sets"},
        "final_evaluation_plan": {
            "run_only_after": "explicit approval from the project owner",
            "test_sets": {"seen_families": "test-group real normals + attacks from generator v2 (3 seen families)",
                          "heldout_family": "test-group real normals + attacks from the held-out family only"},
            "attack_counts": {"at_prevalence_0.0835": {"group_rank2_user": 59, "group_rank4_user": 26},
                              "evaluation_ratio_0.25": {"group_rank2_user": 161, "group_rank4_user": 71},
                              "note": "evaluation sets use ratio 0.25 for stable estimates; precision, F1, FPR and PR-AUC are reweighted to 8.35% prevalence, exactly as in dev"},
            "metrics": ["ROC-AUC", "PR-AUC (prevalence 8.35%)", "recall at oracle FPR 1% and 0.1%", "realised FPR and recall at the frozen policy per test group",
                        "verdict breakdown dangerous/suspicious/unsure/safe", "FPR on counts-only normals and on other normals",
                        "ECE and reliability curve", "per-group results (2 groups) and bootstrap CIs", "his recipe as comparator", "sweep onset"],
            "single_evaluation": True,
        },
    }
    path = ROOT / "configs" / "stage_e_final.yaml"
    path.write_text("# FROZEN final pipeline. See tests/test_stage_e_freeze.py.\n" + yaml.safe_dump(final, sort_keys=False, width=110))
    (ROOT / "configs" / "stage_e_final.lock").write_text(json.dumps(
        {"file": "configs/stage_e_final.yaml", "sha256": sha(path), "test_fingerprint": split_lock["test_fingerprint"],
         "frozen_on": final["frozen_on"]}, indent=1))
    print(json.dumps(ch, indent=1, default=str)); print("lock sha256", sha(path))


if __name__ == "__main__":
    main()
