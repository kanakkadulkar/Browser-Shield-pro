# FINAL RESULTS: single evaluation on the locked test set

## What this evaluation can and cannot show (read first)
**The test attacks come from the SAME generator as the training attacks** (generator v2, simulated miner signal with assumed effect sizes, held-out family `throttled` never trained on). Both the training attacks and the test attacks are synthetic and built by the same code. **So this evaluation checks transfer to unseen users' REAL NORMAL traffic (false alarms, and how separable generator-style attacks injected into those users' rows are). It does NOT measure detection of real miners.** Nothing here supports any claim about real-world cryptojacking coverage.

## What was run
- **One evaluation, run once** (`reports/final_eval/RUN_COMPLETE` blocks a second run). Pipeline exactly as frozen in `configs/stage_e_final.yaml` (hash verified against `configs/stage_e_final.lock` before running; the lock test still passes afterwards): own features, **M1 (XGBoost, 20 Optuna trials)**, **Platt calibration fit on validation**, no regime handling (V0), policy **dangerous = above the validation 0.25% quantile, suspicious = above the 5% quantile, unsure = out of training range**. Trained on all dev groups, 3 seeds (42/43/44). His recipe is the comparator, trained on the same training side and attacks.
- **I took your addendum ("Addendum to the final-test GO") as the GO.** Before the real run I did a dry run of the same code on a *dev* group standing in as "test" (no locked-test rows were loaded) to catch bugs. Nothing was changed or re-run after seeing results.
- **Test set:** 928 real normals in two user groups (**group 1: 644, group 2: 284**; Reading A and B use the same rows). Attacks were generated from each test group's own real normals at the 0.25 evaluation ratio (**161 and 71 for seed 42**) and are reweighted to the 8.35% prevalence for PR-AUC. At the natural 8.35% there would be only 59 and 26 attacks.
- **How to read the counts:** counts (k/n) are for **seed 42**, the first configured seed, with Wilson 95% intervals that assume independent rows. A second table per group gives the **3-seed mean [min, max]**; seeds change model training and the attack draws (the normals are identical). The ROC/PR/ECE intervals are row bootstraps. All of these ignore variation between groups, which is why groups are reported separately and the test is only two groups.
- **Reading A is primary.** Reading B (tiny training sides) is in the appendix.

## Summary: Reading A, seen families (each group first, then pooled)

| | Group 1 (644 normals, 161 attacks) | Group 2 (284 normals, 71 attacks) | Pooled (928 normals, 232 attacks) |
|---|---|---|---|
| **Counts-only normals (n)** | **128** | **1** | 129 |
| **FPR, "dangerous"** | **20/644 = 3.1% [2.0, 4.7]** (3-seed mean 4.3%, range 3.1% to 6.1%) | 1/284 = 0.4% [0.1, 2.0] | **21/928 = 2.3% [1.5, 3.4]** (3-seed mean 3.1%) |
| FPR on counts-only normals | **19/128 = 14.8% [9.7, 22.0]** (3-seed mean 19.3%) | 1/1 (uninformative) | 20/129 = 15.5% [10.3, 22.7] |
| FPR on other normals | 1/506 = 0.2% | 0/281 = 0.0% | 1/787 = 0.1% |
| **Recall, "dangerous" alone** | 118/161 = 73.3% [66.0, 79.5] | 53/71 = 74.6% [63.4, 83.3] | 171/232 = 73.7% [67.7, 79.0] |
| **Recall, "dangerous" + "suspicious"** | 156/161 = 96.9% [92.9, 98.7] | 69/71 = 97.2% [90.3, 99.2] | 225/232 = 97.0% [93.9, 98.5] |
| Unsure rows (normals + attacks) | 0 + 0 | 1 + 0 | 1 + 0 |
| ROC-AUC / PR-AUC (8.35%) | 0.965 / 0.793 | 0.990 / 0.938 | 0.972 / 0.817 |
| Oracle recall @ FPR 1% | 0.567 | 0.850 | 0.654 |
| ECE | 0.045 | 0.019 | 0.033 |

Held-out family (`throttled`), recall "dangerous" / "dangerous + suspicious": group 1 **113/161 = 70.2% / 141/161 = 87.6%**; group 2 48/71 = 67.6% / 65/71 = 91.5%; pooled 161/232 = 69.4% / 206/232 = 88.8%. FPR is identical to the table above (same normals and policy).

## The result, plainly
1. **The frozen pipeline missed its false-alarm target on group 1.** The dev rule was pooled FPR <= 1% with no group above 2%. On test, group 1 is **3.1%** (3-seed mean 4.3%) and pooled **2.3%** (mean 3.1%), about 3x the dev value (1.0%) and **worse than every dev group** (dev worst: 1.4%).
2. **Almost all of the false alarms are counts-only normals.** 19 of group 1's 20 false alarms are among its 128 counts-only normals (14.8%); on its 506 other normals there is **1** false alarm (0.2%). This is the failure mode found in Stage D and left unhandled by the pre-registered rule (V0).
3. **I badly underestimated this group.** I projected roughly 17 counts-only normals for it from the dev proportion (2.6%). It has **128 (19.9% of the group)**. That is a distribution shift in the unseen user's data that nothing in dev anticipated, and my projection was wrong by about 7x.
4. **Group 2 looks better than dev on every metric** (FPR 0.4%, recall 74.6%, PR-AUC 0.938), but it contains **one** counts-only normal, so it says nothing about the counts-only problem.
5. **Recall is not the problem:** "dangerous" recall (73.7% pooled) and "dangerous + suspicious" (97.0%) are above their dev values (68.0% and 93.5%). That is partly the same generator on different bases, and says nothing about real miners.
6. **Ranking and calibration degrade on group 1** (PR-AUC 0.793 vs dev's lowest group 0.814; ECE 0.045 vs dev 0.014), consistent with the counts-only shift.
7. **Against his recipe** (same data, validation-1% threshold): pooled FPR 51/928 = 5.5% vs ours 2.3%; recall 81.0% vs 73.7%; PR-AUC 0.724 vs 0.817; ROC-AUC 0.955 vs 0.972. So the new pipeline is better on false alarms and ranking, at lower recall. At his own threshold rule his FPR is 121/928 = 13.0% (recall 95.7%).
8. **What I did not do:** I did not try the regime-specific threshold (Va) or any other fix on the test set. In dev, Va halved counts-only false alarms but raised false alarms elsewhere, and the pre-registered rule rejected it. Using the test result to choose a fix would no longer be a clean evaluation; any change should be treated as new development and needs a fresh held-out set.

## Test vs dev (Reading A). ⚠ = worse than the dev pooled 95% CI; ⛔ = worse than every dev group
Dev = the three Stage E held-out dev groups with the same frozen pipeline and policy. The dev CI ignores between-group variation, so ⚠ alone is a weak signal; ⛔ is the stricter flag. Metrics where test is *better* are unflagged.

**Seen families**

| Metric | Dev pooled [95% CI] | Dev per-group range | Test group 1 | Test group 2 | Test pooled |
|---|---|---|---|---|---|
| ROC-AUC | 0.970 [0.968, 0.973] | 0.959 to 0.997 | 0.965 ⚠ | 0.990 | 0.972 |
| PR-AUC (8.35%) | 0.854 [0.846, 0.863] | 0.814 to 0.978 | 0.793 ⛔ | 0.938 | 0.817 ⚠ |
| Oracle recall @ FPR 1% | 0.693 [0.680, 0.714] | 0.620 to 0.919 | 0.567 ⛔ | 0.850 | 0.654 ⚠ |
| Oracle recall @ FPR 0.1% | 0.446 [0.401, 0.489] | 0.424 to 0.876 | 0.398 ⛔ | 0.742 | 0.503 |
| ECE | 0.014 [0.013, 0.016] | 0.014 to 0.024 | 0.045 ⛔ | 0.019 ⚠ | 0.033 ⛔ |
| FPR, "dangerous" | 0.010 [0.008, 0.011] | 0.000 to 0.014 | 0.043 ⛔ | 0.002 | 0.031 ⛔ |
| FPR, counts-only normals | 0.049 [0.033, 0.067] | 0.000 to 0.130 | 0.193 ⛔ | 0.667 ⛔ (1 row) | 0.196 ⛔ |
| FPR, other normals | 0.009 [0.007, 0.010] | 0.000 to 0.009 | 0.006 | 0.000 | 0.004 |
| Recall, "dangerous" | 0.680 [0.668, 0.694] | 0.630 to 0.791 | 0.766 | 0.728 | 0.754 |
| Recall, "dangerous" + "suspicious" | 0.935 [0.929, 0.941] | 0.887 to 0.979 | 0.948 | 0.934 | 0.944 |
| Unsure rate, normals / attacks | 0.003 / 0.007 | 0.000 to 0.004 / 0.009 | 0.000 / 0.000 | 0.004 / 0.000 | 0.001 / 0.000 |

(The test columns here are 3-seed means; the group-2 counts-only figure is the mean over 3 seeds of a single row.) **Held-out family:** the same flags on ROC-AUC (group 1 ⛔ 0.941), PR-AUC (⛔ 0.750), ECE, FPR and counts-only FPR; recall ("dangerous" 0.677, "dangerous + suspicious" 0.880) is at or above dev except "dangerous + suspicious" ⚠ vs the dev CI. Full tables are in the appendix.

## Caveats
- Two test groups. The pooled numbers are dominated by group 1's counts-only rows (128 of 129 counts-only normals).
- Seeds matter: group 1 FPR ranges from 3.1% to 6.1% across the three seeds.
- Reading B (appendix): pooled FPR 37/928 = 4.0%, counts-only 27/129 = 20.9%, recall "dangerous" 73.3% and "dangerous + suspicious" 94.0%; same pattern, noisier. Its dev "unsure" rate (28%) did not recur on test (0.4%).
- All attacks are simulated. Nothing about real miners.

## Files
`src/final_eval.py`, `src/final_report.py` · `reports/final_eval/` (`raw.pkl`, `tables.md`, `RUN_COMPLETE`, `run.log`) · appendix below is `reports/final_eval/tables.md` verbatim.

---

# Appendix: full tables (generated by `src/final_report.py`; per group first, then pooled)

## Reading A: SEEN families


### Test group 1  (seed 42: 644 real normals, 161 simulated attacks, 128 counts-only normals, 0 + 0 unsure rows)

| Policy outcome (seed 42, raw counts, Wilson 95% CI) | value |
|---|---|
| FPR, 'dangerous' (all normals) | 20/644 = 0.031 [0.020, 0.047] |
| FPR, 'dangerous' among decided normals | 20/644 = 0.031 [0.020, 0.047] |
| FPR on counts-only normals | 19/128 = 0.148 [0.097, 0.220] |
| FPR on other normals | 1/506 = 0.002 [0.000, 0.011] |
| Recall, 'dangerous' alone | 118/161 = 0.733 [0.660, 0.795] |
| Recall, 'dangerous' + 'suspicious' | 156/161 = 0.969 [0.929, 0.987] |
| Unsure rows: normals / attacks | 0/644 / 0/161 |

3-seed mean [min, max across seeds] of the same rates (seeds change the attack draws and model training; normals are identical):

| FPR dangerous | FPR counts-only | FPR other | Recall dangerous | Recall d+s | Unsure normals | Unsure attacks |
|---|---|---|---|---|---|---|
| 0.043 [0.031, 0.061] | 0.193 [0.141, 0.289] | 0.006 [0.002, 0.012] | 0.766 [0.733, 0.807] | 0.948 [0.919, 0.969] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

Ranking quality (seed mean, bootstrap 95% CI over rows):

| ROC-AUC | PR-AUC (8.35%) | Oracle recall @ 1% FPR | Oracle recall @ 0.1% FPR | ECE |
|---|---|---|---|---|
| 0.965 [0.957, 0.972] | 0.793 [0.760, 0.829] | 0.567 [0.501, 0.629] | 0.398 [0.321, 0.509] | 0.045 [0.038, 0.054] |

Comparator, his recipe (same training side, same attacks; seed 42): at validation-1% threshold FPR 51/644 = 0.079 [0.061, 0.103], recall 130/161 = 0.807 [0.740, 0.861]; at his own rule FPR 108/644 = 0.168 [0.141, 0.199], recall 152/161 = 0.944 [0.897, 0.970]; ROC-AUC 0.944 [0.933, 0.954], PR-AUC 0.671 [0.635, 0.720].


### Test group 2  (seed 42: 284 real normals, 71 simulated attacks, 1 counts-only normals, 1 + 0 unsure rows)

| Policy outcome (seed 42, raw counts, Wilson 95% CI) | value |
|---|---|
| FPR, 'dangerous' (all normals) | 1/284 = 0.004 [0.001, 0.020] |
| FPR, 'dangerous' among decided normals | 1/283 = 0.004 [0.001, 0.020] |
| FPR on counts-only normals | 1/1 = 1.000 [0.207, 1.000] |
| FPR on other normals | 0/281 = 0.000 [0.000, 0.013] |
| Recall, 'dangerous' alone | 53/71 = 0.746 [0.634, 0.833] |
| Recall, 'dangerous' + 'suspicious' | 69/71 = 0.972 [0.903, 0.992] |
| Unsure rows: normals / attacks | 1/284 / 0/71 |

3-seed mean [min, max across seeds] of the same rates (seeds change the attack draws and model training; normals are identical):

| FPR dangerous | FPR counts-only | FPR other | Recall dangerous | Recall d+s | Unsure normals | Unsure attacks |
|---|---|---|---|---|---|---|
| 0.002 [0.000, 0.004] | 0.667 [0.000, 1.000] | 0.000 [0.000, 0.000] | 0.728 [0.676, 0.761] | 0.934 [0.901, 0.972] | 0.004 [0.004, 0.004] | 0.000 [0.000, 0.000] |

Ranking quality (seed mean, bootstrap 95% CI over rows):

| ROC-AUC | PR-AUC (8.35%) | Oracle recall @ 1% FPR | Oracle recall @ 0.1% FPR | ECE |
|---|---|---|---|---|
| 0.990 [0.986, 0.994] | 0.938 [0.916, 0.963] | 0.850 [0.777, 0.911] | 0.742 [0.690, 0.840] | 0.019 [0.017, 0.026] |

Comparator, his recipe (same training side, same attacks; seed 42): at validation-1% threshold FPR 0/284 = 0.000 [0.000, 0.013], recall 58/71 = 0.817 [0.712, 0.890]; at his own rule FPR 13/284 = 0.046 [0.027, 0.077], recall 70/71 = 0.986 [0.924, 0.998]; ROC-AUC 0.981 [0.969, 0.992], PR-AUC 0.942 [0.921, 0.967].


### POOLED over the test groups  (seed 42: 928 real normals, 232 simulated attacks, 129 counts-only normals, 1 + 0 unsure rows)

| Policy outcome (seed 42, raw counts, Wilson 95% CI) | value |
|---|---|
| FPR, 'dangerous' (all normals) | 21/928 = 0.023 [0.015, 0.034] |
| FPR, 'dangerous' among decided normals | 21/927 = 0.023 [0.015, 0.034] |
| FPR on counts-only normals | 20/129 = 0.155 [0.103, 0.227] |
| FPR on other normals | 1/787 = 0.001 [0.000, 0.007] |
| Recall, 'dangerous' alone | 171/232 = 0.737 [0.677, 0.790] |
| Recall, 'dangerous' + 'suspicious' | 225/232 = 0.970 [0.939, 0.985] |
| Unsure rows: normals / attacks | 1/928 / 0/232 |

3-seed mean [min, max across seeds] of the same rates (seeds change the attack draws and model training; normals are identical):

| FPR dangerous | FPR counts-only | FPR other | Recall dangerous | Recall d+s | Unsure normals | Unsure attacks |
|---|---|---|---|---|---|---|
| 0.031 [0.023, 0.043] | 0.196 [0.140, 0.295] | 0.004 [0.001, 0.008] | 0.754 [0.733, 0.793] | 0.944 [0.922, 0.970] | 0.001 [0.001, 0.001] | 0.000 [0.000, 0.000] |

Ranking quality (seed mean, bootstrap 95% CI over rows):

| ROC-AUC | PR-AUC (8.35%) | Oracle recall @ 1% FPR | Oracle recall @ 0.1% FPR | ECE |
|---|---|---|---|---|
| 0.972 [0.966, 0.977] | 0.817 [0.791, 0.845] | 0.654 [0.606, 0.696] | 0.503 [0.451, 0.601] | 0.033 [0.029, 0.040] |

Comparator, his recipe (same training side, same attacks; seed 42): at validation-1% threshold FPR 51/928 = 0.055 [0.042, 0.072], recall 188/232 = 0.810 [0.755, 0.856]; at his own rule FPR 121/928 = 0.130 [0.110, 0.154], recall 222/232 = 0.957 [0.922, 0.976]; ROC-AUC 0.955 [0.946, 0.963], PR-AUC 0.724 [0.692, 0.760].


### Dev vs test, Reading A, SEEN families

Dev = the Stage E held-out dev groups (n groups = 3), same frozen pipeline, same policy. Flags: ⚠ = test value worse than the dev pooled 95% CI; ⛔ = worse than every dev group (outside the dev per-group range).

| Metric | Dev pooled [95% CI] | Dev per-group range | test group 1 | test group 2 | test pooled |
|---|---|---|---|---|---|
| ROC-AUC | 0.970 [0.968, 0.973] | 0.959 to 0.997 | 0.965 ⚠ | 0.990 | 0.972 |
| PR-AUC (8.35%) | 0.854 [0.846, 0.863] | 0.814 to 0.978 | 0.793 ⛔ | 0.938 | 0.817 ⚠ |
| Oracle recall @ FPR 1% | 0.693 [0.680, 0.714] | 0.620 to 0.919 | 0.567 ⛔ | 0.850 | 0.654 ⚠ |
| Oracle recall @ FPR 0.1% | 0.446 [0.401, 0.489] | 0.424 to 0.876 | 0.398 ⛔ | 0.742 | 0.503 |
| ECE | 0.014 [0.013, 0.016] | 0.014 to 0.024 | 0.045 ⛔ | 0.019 ⚠ | 0.033 ⛔ |
| FPR, 'dangerous' (all normals) | 0.010 [0.008, 0.011] | 0.000 to 0.014 | 0.043 ⛔ | 0.002 | 0.031 ⛔ |
| FPR, counts-only normals | 0.049 [0.033, 0.067] | 0.000 to 0.130 | 0.193 ⛔ | 0.667 ⛔ | 0.196 ⛔ |
| FPR, other normals | 0.009 [0.007, 0.010] | 0.000 to 0.009 | 0.006 | 0.000 | 0.004 |
| Recall, 'dangerous' alone | 0.680 [0.668, 0.694] | 0.630 to 0.791 | 0.766 | 0.728 | 0.754 |
| Recall, 'dangerous' + 'suspicious' | 0.935 [0.929, 0.941] | 0.887 to 0.979 | 0.948 | 0.934 | 0.944 |
| Unsure rate, normals | 0.003 [0.002, 0.004] | 0.000 to 0.004 | 0.000 | 0.004 | 0.001 |
| Unsure rate, attacks | 0.007 [0.005, 0.009] | 0.000 to 0.009 | 0.000 | 0.000 | 0.000 |

## Reading A: HELD-OUT family


### Test group 1  (seed 42: 644 real normals, 161 simulated attacks, 128 counts-only normals, 0 + 0 unsure rows)

| Policy outcome (seed 42, raw counts, Wilson 95% CI) | value |
|---|---|
| FPR, 'dangerous' (all normals) | 20/644 = 0.031 [0.020, 0.047] |
| FPR, 'dangerous' among decided normals | 20/644 = 0.031 [0.020, 0.047] |
| FPR on counts-only normals | 19/128 = 0.148 [0.097, 0.220] |
| FPR on other normals | 1/506 = 0.002 [0.000, 0.011] |
| Recall, 'dangerous' alone | 113/161 = 0.702 [0.627, 0.767] |
| Recall, 'dangerous' + 'suspicious' | 141/161 = 0.876 [0.816, 0.918] |
| Unsure rows: normals / attacks | 0/644 / 0/161 |

3-seed mean [min, max across seeds] of the same rates (seeds change the attack draws and model training; normals are identical):

| FPR dangerous | FPR counts-only | FPR other | Recall dangerous | Recall d+s | Unsure normals | Unsure attacks |
|---|---|---|---|---|---|---|
| 0.043 [0.031, 0.061] | 0.193 [0.141, 0.289] | 0.006 [0.002, 0.012] | 0.677 [0.634, 0.702] | 0.880 [0.876, 0.882] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

Ranking quality (seed mean, bootstrap 95% CI over rows):

| ROC-AUC | PR-AUC (8.35%) | Oracle recall @ 1% FPR | Oracle recall @ 0.1% FPR | ECE |
|---|---|---|---|---|
| 0.941 [0.929, 0.952] | 0.750 [0.713, 0.787] | 0.571 [0.504, 0.640] | 0.437 [0.354, 0.524] | 0.054 [0.048, 0.065] |

Comparator, his recipe (same training side, same attacks; seed 42): at validation-1% threshold FPR 51/644 = 0.079 [0.061, 0.103], recall 121/161 = 0.752 [0.679, 0.812]; at his own rule FPR 108/644 = 0.168 [0.141, 0.199], recall 142/161 = 0.882 [0.823, 0.923]; ROC-AUC 0.904 [0.887, 0.919], PR-AUC 0.532 [0.488, 0.591].


### Test group 2  (seed 42: 284 real normals, 71 simulated attacks, 1 counts-only normals, 1 + 0 unsure rows)

| Policy outcome (seed 42, raw counts, Wilson 95% CI) | value |
|---|---|
| FPR, 'dangerous' (all normals) | 1/284 = 0.004 [0.001, 0.020] |
| FPR, 'dangerous' among decided normals | 1/283 = 0.004 [0.001, 0.020] |
| FPR on counts-only normals | 1/1 = 1.000 [0.207, 1.000] |
| FPR on other normals | 0/281 = 0.000 [0.000, 0.013] |
| Recall, 'dangerous' alone | 48/71 = 0.676 [0.561, 0.773] |
| Recall, 'dangerous' + 'suspicious' | 65/71 = 0.915 [0.828, 0.961] |
| Unsure rows: normals / attacks | 1/284 / 0/71 |

3-seed mean [min, max across seeds] of the same rates (seeds change the attack draws and model training; normals are identical):

| FPR dangerous | FPR counts-only | FPR other | Recall dangerous | Recall d+s | Unsure normals | Unsure attacks |
|---|---|---|---|---|---|---|
| 0.002 [0.000, 0.004] | 0.667 [0.000, 1.000] | 0.000 [0.000, 0.000] | 0.676 [0.620, 0.732] | 0.887 [0.845, 0.915] | 0.004 [0.004, 0.004] | 0.000 [0.000, 0.000] |

Ranking quality (seed mean, bootstrap 95% CI over rows):

| ROC-AUC | PR-AUC (8.35%) | Oracle recall @ 1% FPR | Oracle recall @ 0.1% FPR | ECE |
|---|---|---|---|---|
| 0.964 [0.950, 0.977] | 0.881 [0.845, 0.920] | 0.751 [0.676, 0.833] | 0.681 [0.622, 0.765] | 0.026 [0.022, 0.033] |

Comparator, his recipe (same training side, same attacks; seed 42): at validation-1% threshold FPR 0/284 = 0.000 [0.000, 0.013], recall 52/71 = 0.732 [0.619, 0.821]; at his own rule FPR 13/284 = 0.046 [0.027, 0.077], recall 61/71 = 0.859 [0.760, 0.922]; ROC-AUC 0.948 [0.927, 0.968], PR-AUC 0.887 [0.851, 0.924].


### POOLED over the test groups  (seed 42: 928 real normals, 232 simulated attacks, 129 counts-only normals, 1 + 0 unsure rows)

| Policy outcome (seed 42, raw counts, Wilson 95% CI) | value |
|---|---|
| FPR, 'dangerous' (all normals) | 21/928 = 0.023 [0.015, 0.034] |
| FPR, 'dangerous' among decided normals | 21/927 = 0.023 [0.015, 0.034] |
| FPR on counts-only normals | 20/129 = 0.155 [0.103, 0.227] |
| FPR on other normals | 1/787 = 0.001 [0.000, 0.007] |
| Recall, 'dangerous' alone | 161/232 = 0.694 [0.632, 0.750] |
| Recall, 'dangerous' + 'suspicious' | 206/232 = 0.888 [0.841, 0.922] |
| Unsure rows: normals / attacks | 1/928 / 0/232 |

3-seed mean [min, max across seeds] of the same rates (seeds change the attack draws and model training; normals are identical):

| FPR dangerous | FPR counts-only | FPR other | Recall dangerous | Recall d+s | Unsure normals | Unsure attacks |
|---|---|---|---|---|---|---|
| 0.031 [0.023, 0.043] | 0.196 [0.140, 0.295] | 0.004 [0.001, 0.008] | 0.677 [0.629, 0.707] | 0.882 [0.871, 0.888] | 0.001 [0.001, 0.001] | 0.000 [0.000, 0.000] |

Ranking quality (seed mean, bootstrap 95% CI over rows):

| ROC-AUC | PR-AUC (8.35%) | Oracle recall @ 1% FPR | Oracle recall @ 0.1% FPR | ECE |
|---|---|---|---|---|
| 0.948 [0.940, 0.956] | 0.776 [0.745, 0.807] | 0.626 [0.571, 0.677] | 0.511 [0.453, 0.578] | 0.044 [0.039, 0.051] |

Comparator, his recipe (same training side, same attacks; seed 42): at validation-1% threshold FPR 51/928 = 0.055 [0.042, 0.072], recall 173/232 = 0.746 [0.686, 0.797]; at his own rule FPR 121/928 = 0.130 [0.110, 0.154], recall 203/232 = 0.875 [0.826, 0.912]; ROC-AUC 0.917 [0.903, 0.930], PR-AUC 0.596 [0.558, 0.642].


### Dev vs test, Reading A, HELD-OUT family

Dev = the Stage E held-out dev groups (n groups = 3), same frozen pipeline, same policy. Flags: ⚠ = test value worse than the dev pooled 95% CI; ⛔ = worse than every dev group (outside the dev per-group range).

| Metric | Dev pooled [95% CI] | Dev per-group range | test group 1 | test group 2 | test pooled |
|---|---|---|---|---|---|
| ROC-AUC | 0.950 [0.947, 0.953] | 0.942 to 0.989 | 0.941 ⛔ | 0.964 | 0.948 |
| PR-AUC (8.35%) | 0.785 [0.775, 0.795] | 0.761 to 0.929 | 0.750 ⛔ | 0.881 | 0.776 |
| Oracle recall @ FPR 1% | 0.572 [0.555, 0.594] | 0.562 to 0.795 | 0.571 | 0.751 | 0.626 |
| Oracle recall @ FPR 0.1% | 0.387 [0.354, 0.417] | 0.360 to 0.774 | 0.437 | 0.681 | 0.511 |
| ECE | 0.020 [0.019, 0.022] | 0.018 to 0.032 | 0.054 ⛔ | 0.026 ⚠ | 0.044 ⛔ |
| FPR, 'dangerous' (all normals) | 0.010 [0.008, 0.011] | 0.000 to 0.014 | 0.043 ⛔ | 0.002 | 0.031 ⛔ |
| FPR, counts-only normals | 0.049 [0.033, 0.067] | 0.000 to 0.130 | 0.193 ⛔ | 0.667 ⛔ | 0.196 ⛔ |
| FPR, other normals | 0.009 [0.007, 0.010] | 0.000 to 0.009 | 0.006 | 0.000 | 0.004 |
| Recall, 'dangerous' alone | 0.566 [0.554, 0.578] | 0.554 to 0.735 | 0.677 | 0.676 | 0.677 |
| Recall, 'dangerous' + 'suspicious' | 0.890 [0.883, 0.898] | 0.837 to 0.902 | 0.880 ⚠ | 0.887 | 0.882 ⚠ |
| Unsure rate, normals | 0.003 [0.002, 0.004] | 0.000 to 0.004 | 0.000 | 0.004 | 0.001 |
| Unsure rate, attacks | 0.002 [0.001, 0.003] | 0.000 to 0.002 | 0.000 | 0.000 | 0.000 |

## Reading B: SEEN families


### Test group 1  (seed 42: 644 real normals, 161 simulated attacks, 128 counts-only normals, 3 + 1 unsure rows)

| Policy outcome (seed 42, raw counts, Wilson 95% CI) | value |
|---|---|
| FPR, 'dangerous' (all normals) | 36/644 = 0.056 [0.041, 0.076] |
| FPR, 'dangerous' among decided normals | 36/641 = 0.056 [0.041, 0.077] |
| FPR on counts-only normals | 27/128 = 0.211 [0.149, 0.290] |
| FPR on other normals | 9/506 = 0.018 [0.009, 0.033] |
| Recall, 'dangerous' alone | 114/161 = 0.708 [0.634, 0.773] |
| Recall, 'dangerous' + 'suspicious' | 151/161 = 0.938 [0.889, 0.966] |
| Unsure rows: normals / attacks | 3/644 / 1/161 |

3-seed mean [min, max across seeds] of the same rates (seeds change the attack draws and model training; normals are identical):

| FPR dangerous | FPR counts-only | FPR other | Recall dangerous | Recall d+s | Unsure normals | Unsure attacks |
|---|---|---|---|---|---|---|
| 0.032 [0.008, 0.056] | 0.115 [0.000, 0.211] | 0.011 [0.006, 0.018] | 0.665 [0.596, 0.708] | 0.946 [0.938, 0.957] | 0.005 [0.005, 0.005] | 0.002 [0.000, 0.006] |

Ranking quality (seed mean, bootstrap 95% CI over rows):

| ROC-AUC | PR-AUC (8.35%) | Oracle recall @ 1% FPR | Oracle recall @ 0.1% FPR | ECE |
|---|---|---|---|---|
| 0.959 [0.948, 0.968] | 0.788 [0.758, 0.822] | 0.576 [0.524, 0.619] | 0.476 [0.418, 0.538] | 0.038 [0.032, 0.046] |

Comparator, his recipe (same training side, same attacks; seed 42): at validation-1% threshold FPR 82/644 = 0.127 [0.104, 0.155], recall 125/161 = 0.776 [0.706, 0.834]; at his own rule FPR 106/644 = 0.165 [0.138, 0.195], recall 139/161 = 0.863 [0.802, 0.908]; ROC-AUC 0.928 [0.915, 0.941], PR-AUC 0.618 [0.581, 0.665].


### Test group 2  (seed 42: 284 real normals, 71 simulated attacks, 1 counts-only normals, 1 + 0 unsure rows)

| Policy outcome (seed 42, raw counts, Wilson 95% CI) | value |
|---|---|
| FPR, 'dangerous' (all normals) | 1/284 = 0.004 [0.001, 0.020] |
| FPR, 'dangerous' among decided normals | 1/283 = 0.004 [0.001, 0.020] |
| FPR on counts-only normals | 0/1 = 0.000 [0.000, 0.793] |
| FPR on other normals | 1/281 = 0.004 [0.001, 0.020] |
| Recall, 'dangerous' alone | 56/71 = 0.789 [0.680, 0.868] |
| Recall, 'dangerous' + 'suspicious' | 67/71 = 0.944 [0.864, 0.978] |
| Unsure rows: normals / attacks | 1/284 / 0/71 |

3-seed mean [min, max across seeds] of the same rates (seeds change the attack draws and model training; normals are identical):

| FPR dangerous | FPR counts-only | FPR other | Recall dangerous | Recall d+s | Unsure normals | Unsure attacks |
|---|---|---|---|---|---|---|
| 0.006 [0.004, 0.011] | 0.000 [0.000, 0.000] | 0.006 [0.004, 0.011] | 0.676 [0.563, 0.789] | 0.953 [0.944, 0.958] | 0.004 [0.004, 0.004] | 0.000 [0.000, 0.000] |

Ranking quality (seed mean, bootstrap 95% CI over rows):

| ROC-AUC | PR-AUC (8.35%) | Oracle recall @ 1% FPR | Oracle recall @ 0.1% FPR | ECE |
|---|---|---|---|---|
| 0.979 [0.968, 0.988] | 0.899 [0.866, 0.931] | 0.761 [0.664, 0.885] | 0.634 [0.554, 0.779] | 0.016 [0.014, 0.024] |

Comparator, his recipe (same training side, same attacks; seed 42): at validation-1% threshold FPR 3/284 = 0.011 [0.004, 0.031], recall 62/71 = 0.873 [0.776, 0.932]; at his own rule FPR 16/284 = 0.056 [0.035, 0.090], recall 69/71 = 0.972 [0.903, 0.992]; ROC-AUC 0.970 [0.956, 0.985], PR-AUC 0.917 [0.889, 0.945].


### POOLED over the test groups  (seed 42: 928 real normals, 232 simulated attacks, 129 counts-only normals, 4 + 1 unsure rows)

| Policy outcome (seed 42, raw counts, Wilson 95% CI) | value |
|---|---|
| FPR, 'dangerous' (all normals) | 37/928 = 0.040 [0.029, 0.054] |
| FPR, 'dangerous' among decided normals | 37/924 = 0.040 [0.029, 0.055] |
| FPR on counts-only normals | 27/129 = 0.209 [0.148, 0.287] |
| FPR on other normals | 10/787 = 0.013 [0.007, 0.023] |
| Recall, 'dangerous' alone | 170/232 = 0.733 [0.672, 0.786] |
| Recall, 'dangerous' + 'suspicious' | 218/232 = 0.940 [0.901, 0.964] |
| Unsure rows: normals / attacks | 4/928 / 1/232 |

3-seed mean [min, max across seeds] of the same rates (seeds change the attack draws and model training; normals are identical):

| FPR dangerous | FPR counts-only | FPR other | Recall dangerous | Recall d+s | Unsure normals | Unsure attacks |
|---|---|---|---|---|---|---|
| 0.024 [0.009, 0.040] | 0.114 [0.000, 0.209] | 0.009 [0.005, 0.013] | 0.668 [0.586, 0.733] | 0.948 [0.940, 0.957] | 0.004 [0.004, 0.004] | 0.001 [0.000, 0.004] |

Ranking quality (seed mean, bootstrap 95% CI over rows):

| ROC-AUC | PR-AUC (8.35%) | Oracle recall @ 1% FPR | Oracle recall @ 0.1% FPR | ECE |
|---|---|---|---|---|
| 0.965 [0.958, 0.973] | 0.814 [0.789, 0.843] | 0.632 [0.585, 0.682] | 0.524 [0.481, 0.590] | 0.026 [0.024, 0.034] |

Comparator, his recipe (same training side, same attacks; seed 42): at validation-1% threshold FPR 85/928 = 0.092 [0.075, 0.112], recall 187/232 = 0.806 [0.750, 0.852]; at his own rule FPR 122/928 = 0.131 [0.111, 0.155], recall 208/232 = 0.897 [0.851, 0.929]; ROC-AUC 0.941 [0.931, 0.952], PR-AUC 0.683 [0.649, 0.725].


### Dev vs test, Reading B, SEEN families

Dev = the Stage E held-out dev groups (n groups = 2), same frozen pipeline, same policy. Flags: ⚠ = test value worse than the dev pooled 95% CI; ⛔ = worse than every dev group (outside the dev per-group range).

| Metric | Dev pooled [95% CI] | Dev per-group range | test group 1 | test group 2 | test pooled |
|---|---|---|---|---|---|
| ROC-AUC | 0.926 [0.919, 0.933] | 0.903 to 0.994 | 0.959 | 0.979 | 0.965 |
| PR-AUC (8.35%) | 0.665 [0.643, 0.693] | 0.594 to 0.940 | 0.788 | 0.899 | 0.814 |
| Oracle recall @ FPR 1% | 0.418 [0.387, 0.467] | 0.330 to 0.812 | 0.576 | 0.761 | 0.632 |
| Oracle recall @ FPR 0.1% | 0.286 [0.269, 0.335] | 0.204 to 0.650 | 0.476 | 0.634 | 0.524 |
| ECE | 0.028 [0.027, 0.033] | 0.016 to 0.034 | 0.038 ⛔ | 0.016 | 0.026 |
| FPR, 'dangerous' (all normals) | 0.009 [0.007, 0.012] | 0.002 to 0.011 | 0.032 ⛔ | 0.006 | 0.024 ⛔ |
| FPR, counts-only normals | 0.016 [0.003, 0.030] | 0.000 to 0.020 | 0.115 ⛔ | 0.000 | 0.114 ⛔ |
| FPR, other normals | 0.009 [0.006, 0.011] | 0.002 to 0.010 | 0.011 ⛔ | 0.006 | 0.009 |
| Recall, 'dangerous' alone | 0.300 [0.277, 0.326] | 0.219 to 0.662 | 0.665 | 0.676 | 0.668 |
| Recall, 'dangerous' + 'suspicious' | 0.528 [0.500, 0.556] | 0.440 to 0.919 | 0.946 | 0.953 | 0.948 |
| Unsure rate, normals | 0.279 [0.266, 0.291] | 0.000 to 0.341 | 0.005 | 0.004 | 0.004 |
| Unsure rate, attacks | 0.277 [0.250, 0.299] | 0.004 to 0.338 | 0.002 | 0.000 | 0.001 |

## Reading B: HELD-OUT family


### Test group 1  (seed 42: 644 real normals, 161 simulated attacks, 128 counts-only normals, 3 + 0 unsure rows)

| Policy outcome (seed 42, raw counts, Wilson 95% CI) | value |
|---|---|
| FPR, 'dangerous' (all normals) | 36/644 = 0.056 [0.041, 0.076] |
| FPR, 'dangerous' among decided normals | 36/641 = 0.056 [0.041, 0.077] |
| FPR on counts-only normals | 27/128 = 0.211 [0.149, 0.290] |
| FPR on other normals | 9/506 = 0.018 [0.009, 0.033] |
| Recall, 'dangerous' alone | 112/161 = 0.696 [0.621, 0.761] |
| Recall, 'dangerous' + 'suspicious' | 137/161 = 0.851 [0.788, 0.898] |
| Unsure rows: normals / attacks | 3/644 / 0/161 |

3-seed mean [min, max across seeds] of the same rates (seeds change the attack draws and model training; normals are identical):

| FPR dangerous | FPR counts-only | FPR other | Recall dangerous | Recall d+s | Unsure normals | Unsure attacks |
|---|---|---|---|---|---|---|
| 0.032 [0.008, 0.056] | 0.115 [0.000, 0.211] | 0.011 [0.006, 0.018] | 0.652 [0.553, 0.708] | 0.857 [0.820, 0.901] | 0.005 [0.005, 0.005] | 0.000 [0.000, 0.000] |

Ranking quality (seed mean, bootstrap 95% CI over rows):

| ROC-AUC | PR-AUC (8.35%) | Oracle recall @ 1% FPR | Oracle recall @ 0.1% FPR | ECE |
|---|---|---|---|---|
| 0.925 [0.911, 0.939] | 0.741 [0.710, 0.784] | 0.563 [0.494, 0.608] | 0.476 [0.415, 0.538] | 0.044 [0.039, 0.053] |

Comparator, his recipe (same training side, same attacks; seed 42): at validation-1% threshold FPR 82/644 = 0.127 [0.104, 0.155], recall 122/161 = 0.758 [0.686, 0.817]; at his own rule FPR 106/644 = 0.165 [0.138, 0.195], recall 129/161 = 0.801 [0.733, 0.856]; ROC-AUC 0.882 [0.864, 0.899], PR-AUC 0.445 [0.413, 0.493].


### Test group 2  (seed 42: 284 real normals, 71 simulated attacks, 1 counts-only normals, 1 + 0 unsure rows)

| Policy outcome (seed 42, raw counts, Wilson 95% CI) | value |
|---|---|
| FPR, 'dangerous' (all normals) | 1/284 = 0.004 [0.001, 0.020] |
| FPR, 'dangerous' among decided normals | 1/283 = 0.004 [0.001, 0.020] |
| FPR on counts-only normals | 0/1 = 0.000 [0.000, 0.793] |
| FPR on other normals | 1/281 = 0.004 [0.001, 0.020] |
| Recall, 'dangerous' alone | 47/71 = 0.662 [0.546, 0.761] |
| Recall, 'dangerous' + 'suspicious' | 62/71 = 0.873 [0.776, 0.932] |
| Unsure rows: normals / attacks | 1/284 / 0/71 |

3-seed mean [min, max across seeds] of the same rates (seeds change the attack draws and model training; normals are identical):

| FPR dangerous | FPR counts-only | FPR other | Recall dangerous | Recall d+s | Unsure normals | Unsure attacks |
|---|---|---|---|---|---|---|
| 0.006 [0.004, 0.011] | 0.000 [0.000, 0.000] | 0.006 [0.004, 0.011] | 0.634 [0.606, 0.662] | 0.887 [0.831, 0.958] | 0.004 [0.004, 0.004] | 0.000 [0.000, 0.000] |

Ranking quality (seed mean, bootstrap 95% CI over rows):

| ROC-AUC | PR-AUC (8.35%) | Oracle recall @ 1% FPR | Oracle recall @ 0.1% FPR | ECE |
|---|---|---|---|---|
| 0.941 [0.919, 0.962] | 0.848 [0.805, 0.892] | 0.746 [0.662, 0.831] | 0.592 [0.521, 0.749] | 0.018 [0.015, 0.027] |

Comparator, his recipe (same training side, same attacks; seed 42): at validation-1% threshold FPR 3/284 = 0.011 [0.004, 0.031], recall 53/71 = 0.746 [0.634, 0.833]; at his own rule FPR 16/284 = 0.056 [0.035, 0.090], recall 61/71 = 0.859 [0.760, 0.922]; ROC-AUC 0.940 [0.916, 0.964], PR-AUC 0.870 [0.831, 0.917].


### POOLED over the test groups  (seed 42: 928 real normals, 232 simulated attacks, 129 counts-only normals, 4 + 0 unsure rows)

| Policy outcome (seed 42, raw counts, Wilson 95% CI) | value |
|---|---|
| FPR, 'dangerous' (all normals) | 37/928 = 0.040 [0.029, 0.054] |
| FPR, 'dangerous' among decided normals | 37/924 = 0.040 [0.029, 0.055] |
| FPR on counts-only normals | 27/129 = 0.209 [0.148, 0.287] |
| FPR on other normals | 10/787 = 0.013 [0.007, 0.023] |
| Recall, 'dangerous' alone | 159/232 = 0.685 [0.623, 0.742] |
| Recall, 'dangerous' + 'suspicious' | 199/232 = 0.858 [0.807, 0.897] |
| Unsure rows: normals / attacks | 4/928 / 0/232 |

3-seed mean [min, max across seeds] of the same rates (seeds change the attack draws and model training; normals are identical):

| FPR dangerous | FPR counts-only | FPR other | Recall dangerous | Recall d+s | Unsure normals | Unsure attacks |
|---|---|---|---|---|---|---|
| 0.024 [0.009, 0.040] | 0.114 [0.000, 0.209] | 0.009 [0.005, 0.013] | 0.647 [0.578, 0.685] | 0.866 [0.823, 0.918] | 0.004 [0.004, 0.004] | 0.000 [0.000, 0.000] |

Ranking quality (seed mean, bootstrap 95% CI over rows):

| ROC-AUC | PR-AUC (8.35%) | Oracle recall @ 1% FPR | Oracle recall @ 0.1% FPR | ECE |
|---|---|---|---|---|
| 0.929 [0.918, 0.939] | 0.763 [0.735, 0.795] | 0.619 [0.565, 0.661] | 0.511 [0.468, 0.578] | 0.032 [0.028, 0.040] |

Comparator, his recipe (same training side, same attacks; seed 42): at validation-1% threshold FPR 85/928 = 0.092 [0.075, 0.112], recall 175/232 = 0.754 [0.695, 0.805]; at his own rule FPR 122/928 = 0.131 [0.111, 0.155], recall 190/232 = 0.819 [0.764, 0.863]; ROC-AUC 0.899 [0.886, 0.914], PR-AUC 0.515 [0.480, 0.568].


### Dev vs test, Reading B, HELD-OUT family

Dev = the Stage E held-out dev groups (n groups = 2), same frozen pipeline, same policy. Flags: ⚠ = test value worse than the dev pooled 95% CI; ⛔ = worse than every dev group (outside the dev per-group range).

| Metric | Dev pooled [95% CI] | Dev per-group range | test group 1 | test group 2 | test pooled |
|---|---|---|---|---|---|
| ROC-AUC | 0.888 [0.878, 0.898] | 0.868 to 0.980 | 0.925 | 0.941 | 0.929 |
| PR-AUC (8.35%) | 0.584 [0.560, 0.617] | 0.534 to 0.843 | 0.741 | 0.848 | 0.763 |
| Oracle recall @ FPR 1% | 0.358 [0.331, 0.400] | 0.302 to 0.607 | 0.563 | 0.746 | 0.619 |
| Oracle recall @ FPR 0.1% | 0.261 [0.243, 0.299] | 0.211 to 0.483 | 0.476 | 0.592 | 0.511 |
| ECE | 0.035 [0.032, 0.039] | 0.032 to 0.038 | 0.044 ⛔ | 0.018 | 0.032 |
| FPR, 'dangerous' (all normals) | 0.009 [0.007, 0.012] | 0.002 to 0.011 | 0.032 ⛔ | 0.006 | 0.024 ⛔ |
| FPR, counts-only normals | 0.016 [0.003, 0.030] | 0.000 to 0.020 | 0.115 ⛔ | 0.000 | 0.114 ⛔ |
| FPR, other normals | 0.009 [0.006, 0.011] | 0.002 to 0.010 | 0.011 ⛔ | 0.006 | 0.009 |
| Recall, 'dangerous' alone | 0.229 [0.210, 0.251] | 0.177 to 0.462 | 0.652 | 0.634 | 0.647 |
| Recall, 'dangerous' + 'suspicious' | 0.427 [0.406, 0.452] | 0.363 to 0.714 | 0.857 | 0.887 | 0.866 |
| Unsure rate, normals | 0.279 [0.266, 0.291] | 0.000 to 0.341 | 0.005 | 0.004 | 0.004 |
| Unsure rate, attacks | 0.302 [0.281, 0.324] | 0.000 to 0.370 | 0.000 | 0.000 | 0.000 |