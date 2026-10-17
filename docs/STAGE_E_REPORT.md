# Stage E report: fair M2, counts-only regime, calibration, ensemble, threshold policy, freeze

**All attack data is "simulated miner signal, assumed effect sizes".** Nothing here is evidence about real miners. Dev folds only: **the locked test set was not loaded** (fingerprint `aef6cae8bd4179c5`). Rules and selections: every selection rule below was written into `configs/stage_e.yaml` (SHA-256 `166421ac...8829d`) **before any Stage E result existed** and was applied mechanically by code. v1/v2 generators unchanged. Seeds 42/43/44, 200-replicate bootstrap, source R2 (generator v2, held-out family `throttled` excluded). Tests: **53 pass**. Full tables: `reports/stage_e/tables.md`.

## Decisions at a glance (all produced by the pre-registered rules)

| Question | Outcome |
|---|---|
| Does M2 beat M1 once tuned equally? | **No.** M2 improved a lot and now beats his recipe on seen families, but M1 is still ahead |
| Counts-only handling | **None chosen (V0).** The best variant halves counts-only false alarms but fails the rule because it raises false alarms elsewhere |
| Calibration | **Platt** (ECE 0.157 -> 0.014 for M1), fit on validation only |
| Ensemble | **Not chosen.** It gains +0.012 PR-AUC, far below the per-group spread (0.164) |
| Final model | **M1 (XGBoost, my features) + Platt + V0** |
| Deployment threshold | **Validation-quantile 0.25%** for "dangerous", 5% for "suspicious", out-of-range -> "unsure" |
| Final pipeline | **Frozen** in `configs/stage_e_final.yaml`, locked by a test |

## 1. Fair M2 (same budget as M1: 20 Optuna trials, same objective and validation scheme, own imbalance choice)
Reading A, R2 -> ER2 (seen families) [95% CI]; Reading A held-out family; Reading B:

| Model | A seen: PR-AUC | A seen: recall @ FPR 1% | A held-out: PR-AUC | B seen: PR-AUC | B held-out: PR-AUC |
|---|---|---|---|---|---|
| His recipe (Stage D) | 0.813 [0.802, 0.824] | 0.675 | 0.722 | 0.610 | 0.481 |
| **M1** (tuned) | **0.849** [0.839, 0.858] | **0.693** | **0.776** | **0.672** | **0.588** |
| M2 untuned (Stage D) | 0.785 [0.774, 0.798] | 0.581 | 0.708 | 0.548 | 0.391 |
| **M2 tuned, own imbalance choice** | 0.838 [0.827, 0.846] | 0.663 | 0.717 | 0.512 | 0.401 |

- **Tuning helped M2 a lot** (A seen 0.785 -> 0.838; ROC 0.962 -> 0.969) and it now **beats his recipe on seen families** (0.838 vs 0.813, CIs just separate).
- **M2 still loses to M1:** 0.838 vs 0.849 on A seen (CIs touch), and clearly on the held-out family (0.717 vs 0.776) and on Reading B (0.512 vs 0.672). On the held-out family it is level with his recipe (0.717 vs 0.722); on B it is below his recipe.
- **Its own imbalance choice differs from M1's:** M2 chose focal loss in **9 of 9** Reading A fits (M1: class weight 7, focal 2). The tuning objective was lower for M2 (0.885 vs 0.906).
- M1 **reproduces Stage D exactly** (score difference 0.0), and the evaluation sets are identical to Stage D's.

## 2. Counts-only regime (uptime unrecoverable)
Variants: **V0** none; **Va** regime-specific validation-FPR threshold; **Vb** separate model for counts-only rows (logistic regression, training-fold counts-only rows only); **Vab** both. Reading A, M1 base (Platt), 1% FPR target, [95% CI]:

| Variant | FPR counts-only normals | FPR other normals | Overall FPR | Recall (all) | Recall (counts-only attacks) |
|---|---|---|---|---|---|
| **V0** (baseline) | **0.093** [0.073, 0.110] | **0.016** [0.014, 0.017] | 0.018 | 0.758 | 0.725 |
| Va | 0.044 [0.029, 0.060] | 0.028 [0.026, 0.030] | 0.029 | 0.798 | 0.709 |
| Vb | 0.119 [0.099, 0.145] | 0.012 [0.011, 0.013] | 0.015 | 0.728 | 0.679 |
| Vab | 0.043 [0.026, 0.060] | 0.028 [0.026, 0.030] | 0.029 | 0.783 | 0.607 |

- **The rule picked V0 for every base (M1, M2, ensemble).** Va and Vab roughly halve counts-only false alarms (9.3% -> 4.4%), but they also raise false alarms on other normals (1.6% -> 2.8%), which violates the rule's "no more than +0.5 pp" condition. **This is a reallocation of a fixed false-alarm budget, not a free gain** (overall FPR rises 1.8% -> 2.9%, recall rises 0.758 -> 0.798).
- **A separate counts-only model (Vb) does not help:** counts-only FPR gets worse (11.9%) and recall lower. Same pattern for M2 and the ensemble (Reading B tells the same story with wide intervals).
- **The pooled 9% hides huge group differences.** Counts-only FPR for M1/V0 by held-out group (Reading A): **22.4%** (82 counts-only normals), **7.6%** (22), **0.3%** (114). Vab (the only variant I tabulated per group) brings these to 6.5%, 0.0%, 3.5%. Other normals: 1,313 / 288 / 6,503. CIs in the table ignore this between-group spread.
- The counts-only model was available in 9 of 9 Reading A fits and 4 of 6 Reading B fits (otherwise Vb/Vab fall back to V0/Va for that fold).
- **Baseline for the headline:** his recipe 14.8% (Stage D) -> M1 9.3% -> best variant 4.4% at the price above; **V0's 9.3% is what the frozen pipeline will show**, not the 4.4%.

## 3. Calibration and ensemble
**Calibration (fit on validation only; Reading A, R2 -> ER2).** ECE raw -> Platt -> isotonic: M1 0.157 -> **0.014** -> 0.017; M2 0.081 -> **0.018** -> 0.024. Rule (lowest mean member ECE, tie -> Platt) selects **Platt**. Reliability curves: `reports/stage_e/reliability_A.png`.
- **ECE flatters the result:** it is dominated by the mass of normals near probability 0. In the mid-to-high range the Platt curve is still **over-confident** (predicted 0.4 to 0.85, observed roughly 0.3 to 0.6). Probabilities are usable for ranking and for the low range, not as reliable "chance of attack" values.
- **Calibration is relative to the generator:** it holds for held-out *groups* of the same simulated attacks at 8.35% prevalence. It says nothing about real prevalence or real miners.

**Stacked ensemble** (logistic stacker on the two calibrated members' logits, fit on validation). Reading A, R2 -> ER2:

| Score | ROC-AUC | PR-AUC | Recall @ FPR 1% | Recall @ FPR 0.1% | ECE |
|---|---|---|---|---|---|
| M1 calibrated | 0.970 | 0.854 [0.846, 0.862] | 0.693 | 0.446 | 0.014 |
| M2 calibrated | 0.970 | 0.842 | 0.663 | 0.424 | 0.018 |
| **Ensemble** | **0.974** | **0.866** [0.858, 0.873] | **0.709** | **0.523** | 0.015 |

- **Does the ensemble beat its best member (M1) by more than the per-group spread? NO.** Improvement **+0.012** PR-AUC; M1's per-group PR-AUC spread is **0.164** (0.814 / 0.978 / 0.861). The paired per-group differences are small but all positive (+0.011, +0.003, +0.012). At 0.1% FPR the ensemble is a bit better (0.523 vs 0.446), with overlapping intervals.
- **Held-out family:** no gain (PR-AUC 0.775 vs M1 0.785). **Reading B: the ensemble is worse** (PR-AUC 0.586 vs 0.665; its stacker is fit on a very small validation set).
- **Final model by the rule: M1**, with V0 and Platt.

## 4. Threshold policy (frozen)
"Dangerous" = calibrated score above the validation-normals quantile at level q; "suspicious" = above the 5% level; "unsure" = no verdict when any `bsp_v1` feature is outside the training range by more than 10%. Candidate levels on Reading A (pooled realised FPR; worst group):

| q | Pooled FPR | Worst group | Recall |
|---|---|---|---|
| 1% | 0.018 | 0.021 | 0.758 |
| 0.5% | 0.011 | 0.015 | 0.707 |
| **0.25%** | **0.010** | **0.014** | **0.685** |

The rule (largest q with pooled FPR <= 1% and worst group <= 2%) selects **q = 0.25%**. **Realised FPR is about 4x the validation level** (the same transfer gap seen in Stage D), which is why such a low level is needed. At that policy, per held-out group (seed mean):

| Reading | Group | Seen: FPR | Seen: recall (dangerous) | Seen: recall (dangerous + suspicious) | Held-out family: recall | Unsure (normals / attacks) | FPR counts-only normals |
|---|---|---|---|---|---|---|---|
| A | 1 | 1.4% | 0.630 | 0.887 | 0.586 | 0% / 0% | **13.0%** |
| A | 2 | 0.0% | 0.791 | 0.979 | 0.735 | 0% / 0% | 0.0% |
| A | 3 | 0.9% | 0.686 | 0.944 | 0.554 | 0.4% / 0.9% | 0.0% |
| B | 1 | 1.1% (1.7% of decided) | 0.219 | 0.440 | 0.177 | **34%** / 34% | 2.0% |
| B | 2 | 0.2% | 0.662 | 0.919 | 0.462 | 0% / 0.4% | 0.0% |

- **Reading A: false alarms on held-out groups stay near or under 1.4%** with recall 0.63 to 0.79 (dangerous) and 0.89 to 0.98 if "suspicious" counts. **Counts-only normals in group 1 are still flagged 13% of the time**, the problem from section 2.
- **The unsure band is data-hungry:** in Reading B group 1 it flags **34%** of rows because the training side there is tiny (256 normals), so the "range" is narrow. In Reading A it flags under 1%. In sweeps it flags 20% to 33% of s = 1.5 attacks (out-of-distribution, as intended).
- **The strict threshold costs sensitivity vs his recipe at its looser threshold:** sweep onset (first s with recall >= 0.5), Reading A: main_thread 0.25 vs his 0.00; worker_pool, network_only, throttled 0.50 vs 0.25 (recall at s = 1: 0.79 to 0.94 vs 0.86 to 0.99). At equal FPR the two are close (oracle recall at 1% FPR 0.693 vs 0.675). Figure: `reports/stage_e/sweep_final_A.png`.

## 5. The oddity (M1 on his generator scored 0.938)
**It is an early-stopping artefact, not a feature or tuning-hyperparameter problem.** On his generator the validation set is so easy that PR-AUC saturates immediately, so early stopping on it halts M1 after **1 to 10 trees (mean 3.3)** instead of the tuned 105 to 441. Refitting the same configuration **without early stopping gives ROC 1.000** (default settings: 1.000), and with early stopping the per-fold ROC is already 0.996 (min 0.980), like the other models. The pooled 0.938 in Stage D comes from concatenating folds whose tiny forests produce coarse scores on different scales, which pooled ROC punishes. Under the primary setting (rebuilt attacks) M1 uses **23 to 221 trees (mean 101)**, so it does not collapse there, and no Stage D conclusion changes. I left the frozen M1 procedure unchanged (`reports/stage_e/oddity_*.csv`). Not tested: whether the same truncation hurts other sources.

## 6. Frozen final pipeline
`configs/stage_e_final.yaml` (SHA-256 `93b21205...c55702`, recorded in `configs/stage_e_final.lock`): bsp_v1 features; generator v2 with `throttled` held out; **M1 (XGBoost, 20 Optuna trials, class-weight or focal chosen by the tuning objective)**; **Platt calibration on validation**; **V0** (no regime handling); policy q = 0.25% / suspicious 5% / unsure delta 10%; seeds 42/43/44; training on all dev groups with the same inner-validation rule; his recipe as comparator on the same training side. Written **after** the Stage E dev results and **before** any test access. `tests/test_stage_e_freeze.py` fails if the file changes (I verified it fails on a one-line tamper and passes after restoring), if the rules file or the Stage D config changes, or if the test fingerprint drifts.

## 7. Planned final evaluation (NOT run; waiting for your "go")
Test set: the two locked user groups, **928 real normals**, same rows under both readings.

| Test group (size rank in Reading A) | Real normals | Attacks at 8.35% prevalence | Attacks at the 0.25 evaluation ratio |
|---|---|---|---|
| rank 2 user | 644 | **59** | 161 |
| rank 4 user | 284 | **26** | 71 |

- **Sets:** seen families (generator v2) and the held-out family `throttled`. The 0.25-ratio sets give stable estimates and are **reweighted to 8.35%** in precision, F1, FPR and PR-AUC, exactly as in dev. At the natural 8.35% there would be only 59 and 26 attacks per group, so intervals would be very wide.
- **Counts-only normals in the test groups: roughly 17 and 7** (estimated from the dev proportion of about 2.6%, **not** read from the test data). Far too few for a stable counts-only FPR; I will report it with its count and a wide interval.
- **Metrics:** ROC-AUC; PR-AUC (8.35%); recall at oracle FPR 1% and 0.1%; **realised FPR and recall at the frozen policy per test group**; verdict breakdown (dangerous / suspicious / unsure / safe); FPR on counts-only vs other normals; ECE and reliability; per-group results (2 groups) plus bootstrap CIs; his recipe as comparator; sweep onset. One evaluation, no re-runs.

## 8. Deviations and limits
1. **Tuning scheme** unchanged from Stage D (two validation splits, not full CV); M2's tuning uses fixed epochs per trial (no early stopping), its final fit uses early stopping on validation; **tuning, early stopping, calibration, stacking and thresholds all share the fold's validation set** (mild reuse; validation sets are small: a few hundred normals in most Reading A folds, tens in some Reading B folds).
2. **Rules are conservative and mechanical.** The regime rule rejected Va on the "other FPR" condition even though Va halves counts-only false alarms; a different rule would choose differently. The ensemble rule's bar (the per-group spread, 0.164) is nearly unreachable by design.
3. **Regime thresholds from 22 to 82 validation counts-only normals** are noisy; counts-only model available in 4 of 6 Reading B fits.
4. **Calibration** is relative to generator v2 at 8.35% prevalence; mid-range probabilities remain over-confident.
5. **Reading B is much noisier** (2 folds, tiny training sides); its ensemble and unsure results are poor.
6. **The held-out family is a weak variant of seen mechanisms.** The final pipeline is trained without it; whether a deployment model should include it is a later decision.
7. **CIs exclude between-group variation** (3 groups in A, 2 in B); per-group numbers are given.
8. His recipe in these tables is thresholded at validation-1% (not its own rule) for comparability.
9. Hypothesis, untested: counts-only normals with large counts resemble `network_only` attacks.
10. Nothing was run on the locked test set; nothing here says anything about real miners. ONNX export, the extension and the demo are not started.

## Files
`configs/stage_e.yaml` (rules, frozen first) · `configs/stage_e_final.yaml` + `.lock` · `src/models3.py`, `src/stage_e.py`, `src/stage_e_analysis.py`, `src/stage_e_freeze.py`, `src/oddity.py` · `tests/test_stage_e_freeze.py`, additions to `tests/test_models2.py` · `reports/stage_e/` (`tables.md`, `results.json`, `reliability_A.png`, `sweep_final_A.png`, `oddity_*.csv`, `raw/`)
