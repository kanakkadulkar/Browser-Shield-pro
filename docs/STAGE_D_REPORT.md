# Stage D report: generator v2, my features, M1 / M2 / M4

**All attack data is "simulated miner signal, assumed effect sizes".** No real mining traffic. "His recipe" = *reproduction of the described method* (11 raw features, as coded).

Rules kept: `configs/stage_d.yaml` written and frozen **before** any Stage D result; dev folds only, the locked test set was never loaded (code asserts it; fingerprint `aef6cae8bd4179c5` unchanged); v1 generator untouched (v1 config byte-identical; its default output hash is a test); no other generator parameter changed. Seeds 42/43/44; 200-replicate bootstrap. Tables: `reports/stage_d/tables.md`, `v1_vs_v2_stage_c.md`; figures `reports/stage_d/sweep_recall_{A,B}.png`. Tests: **49 pass**.

## 1. Generator v2 (the fix, and what it changed)
- **Bug:** counts-only rows have no uptime, yet cumulative request counts scale with uptime. v1 borrowed one from the other rows *of the batch*; the `network_only` batch contains only counts-only rows, so it fell back to a constant 60 s.
- **Fix, defined from the bug:** v2 draws a **per-row uptime from the group's observed uptimes**. `configs/synth_v2.yaml` differs from v1 by **one added line** (`version: 2`); tests prove all other families are **bit-identical** to v1 under the same seed.
- **Stage C re-run under v2** (frozen Stage C config, same code, Reading A, his recipe as coded):

| | v1 | v2 |
|---|---|---|
| Condition 3, PR-AUC | 0.778 [0.766, 0.790] | 0.811 [0.801, 0.822] |
| Condition 3, recall @ val-1% FPR | 0.684 | 0.769 |
| Condition 3, F1 at his rule | 0.422 | 0.406 |
| `network_only` sweep: onset (first s with recall >= 0.5) | **never** (0.215 at strongest) | **s = 0.25** (0.811 at strongest) |
| Counts-only normals FPR (validation 1% threshold) | 12.4% | 11.8% |
| Condition 4a (his gen -> rebuilt): recall at his rule / ROC | 0.070 / 0.715 | 0.070 / 0.722 |

  Conclusions of Stage C **stand**: his generator-trained model still misses rebuilt attacks (4a unchanged), and the counts-only false-alarm problem is **not** caused by the bug (11.8% vs 12.4%). Evaluating v2-trained models on v1's `network_only` attacks gives onset only at s = 1.5, confirming v1's family was far weaker than labelled. Reading B: same direction (`reports/stage_d/v1_vs_v2_stage_c.md`).

## 2. My feature set `bsp_v1` (`src/features2.py`)
Counts-only indicator; recovered log-uptime; lag fraction; **correct per-second rates** (0 when uptime unknown, so no divide-by-zero and no count-valued "rates"); log-scaled counters; post share; idle and visibility. 15 features, **all of them reach the model** (his 7 engineered ones never did). 4 tests.

## 3. Setup (Stage C protocol, plus)
Dedupe, leave-one-group-out dev folds, inner validation, thresholds from validation only. **Held-out family: `throttled`** never generated for training, validation, tuning or early stopping for any model (his recipe included; asserted in code). Training sources: H (his generator), R1 (v1), R2 (v2, primary); evaluation sets: EH, ER1, ER2 (seen families), **EHO (held-out family only)**. **M1:** XGBoost, Optuna 20 trials per (fold, source, seed), one imbalance mechanism chosen by the tuning objective. **M2:** feature-token transformer (2 layers, 4 heads, d=32), cosine LR with warmup, early stopping, M1's mechanism. **M4:** Isolation Forest (his raw features and mine) and autoencoder, trained on **normals only**.

## 4. Headline (Reading A, v2 attacks, seen families, trained on R2) [95% bootstrap CI]

**Ranking quality** (oracle thresholds: the held-out group's own normal-score quantile):

| Model | ROC-AUC | PR-AUC (8.35%) | Recall @ 1% FPR | Recall @ 0.1% FPR | ECE |
|---|---|---|---|---|---|
| His recipe | 0.954 | 0.813 [0.802, 0.824] | 0.675 [0.646, 0.701] | 0.409 [0.377, 0.450] | 0.235 |
| Logistic regression, raw | 0.918 | 0.638 | 0.364 | 0.138 | 0.205 |
| XGBoost on his 11 raw features (ablation) | 0.947 | 0.806 [0.796, 0.816] | 0.664 | **0.537** [0.468, 0.558] | 0.253 |
| Logistic regression, my features | 0.963 | 0.795 [0.786, 0.805] | 0.592 | 0.393 | 0.117 |
| **M1 XGBoost, my features** | **0.971** | **0.849** [0.839, 0.858] | 0.693 [0.680, 0.712] | 0.444 [0.395, 0.488] | 0.157 |
| **M2 attention net, my features** | 0.962 | 0.785 [0.774, 0.798] | 0.581 [0.552, 0.613] | 0.276 | **0.108** |

**Threshold transfer** (thresholds fixed on validation of the training side; target FPR 1%):

| Model | Realised FPR | Recall | Per-group FPR range | **FPR on counts-only normals** | FPR his rule |
|---|---|---|---|---|---|
| His recipe | **5.5%** [5.2, 5.7] | 0.823 | 0.5% to 6.5% | **14.8%** [12.1, 17.9] | 25.4% |
| XGBoost, his raw features | 4.9% | 0.818 | 0.8% to 5.7% | 9.8% [7.6, 12.5] | 16.4% |
| Logistic regression, my features | 3.2% | 0.720 | 0.9% to 4.1% | **22.2%** [19.0, 25.5] | 22.3% |
| **M1, my features** | **1.8%** [1.7, 1.9] | 0.759 | 1.0% to 2.1% | **9.5%** [7.2, 11.9] | 15.1% |
| **M2, my features** | **2.0%** [1.8, 2.2] | 0.714 | 0.0% to 2.2% | **8.7%** [6.8, 10.7] | 12.7% |

Reading B: M1 PR-AUC 0.672 [0.650, 0.701] vs his recipe 0.610 [0.580, 0.644]; M2 0.548; realised FPR 2.2% (M1) and 1.5% (M2) vs 5.2% (his); counts-only FPR 6.1% (M1), 10.3% (M2), 8.3% (his), 19.2% (XGBoost on raw features). Intervals on B are wide (104 counts-only normals; 2 folds).

### What this does and does not show
- **Ranking: modest gain, only for M1.** M1 beats his recipe on PR-AUC (+0.036, non-overlapping CIs) and ROC-AUC (0.971 vs 0.954). Recall at fixed 1% and 0.1% FPR is **not distinguishable** from his recipe (overlapping CIs), and XGBoost on his *raw* features is just as good at 0.1% FPR (0.537). **M2 does not beat M1**, and is below his recipe on PR-AUC (0.785 vs 0.813). Caveat: M1 was tuned (20 Optuna trials), M2 was not.
- **Features matter most for simple models:** logistic regression PR-AUC 0.638 -> 0.795 with my features. For XGBoost the gain is +0.043 PR-AUC.
- **The clearest gain is threshold transfer:** at a 1% target, the realised FPR on held-out groups is 1.8% (M1) / 2.0% (M2) vs 5.5% (his), with much narrower per-group spread. It costs recall at that threshold (0.76 vs 0.82); oracle recall at 1% FPR is similar, so this is better *calibration across groups*, not better detection.
- **HEADLINE, counts-only false alarms: reduced, not fixed.** 14.8% [12.1, 17.9] (his recipe) -> 9.5% [7.2, 11.9] (M1) and 8.7% [6.8, 10.7] (M2), vs 1.6% to 1.8% on other normals. **My features alone do not explain it:** XGBoost on his raw features already gets 9.8%, and logistic regression on my features is *worse* (22.2%). The improvement comes mostly from the model family (his 1000x off-scale rates feed an MLP), and a ~9% false-alarm rate on those rows is still about 5x the rate elsewhere. *Hypothesis, untested:* counts-only normals with large counts resemble `network_only` attacks, and there are few of them (2.7% of deduped normals; 218 in A).
- **Calibration is poor everywhere** (ECE 0.11 to 0.25): class weighting and focal loss distort probabilities. Calibration is left to the ensemble stage.
- **His threshold rule is the problem, not only the models:** at "max F1 s.t. val recall >= 0.97" every model false-alarms on 13% to 25% of normals.
- **Imbalance mechanism chosen by tuning (Reading A, R2):** class weight 7 of 9 fits, focal 2 of 9. Class weight is the default winner.

## 5. Cross-generator transfer (ROC-AUC / PR-AUC, Reading A)

| Model | H->EH (his own) | R2->ER2 | R2->held-out | **H->ER2** | R2->EH | **R1->ER2 (v1->v2)** | R2->ER1 (v2->v1) |
|---|---|---|---|---|---|---|---|
| His recipe | 0.999 / 0.997 | 0.954 / 0.813 | 0.926 / 0.722 | **0.708 / 0.416** | 0.972 / 0.827 | 0.943 / 0.760 | 0.932 / 0.750 |
| XGBoost, raw features | 0.989 / 0.969 | 0.947 / 0.806 | 0.929 / 0.781 | 0.703 / 0.306 | 0.956 / 0.752 | 0.948 / 0.791 | 0.924 / 0.742 |
| M1, my features | 0.938 / 0.802 | 0.971 / 0.849 | 0.950 / 0.776 | **0.692 / 0.294** | 0.959 / 0.665 | 0.941 / 0.748 | 0.948 / 0.782 |
| M2, my features | 0.998 / 0.993 | 0.962 / 0.785 | 0.931 / 0.708 | **0.595 / 0.230** | 0.950 / 0.682 | 0.968 / 0.780 | 0.937 / 0.725 |
| Logistic reg., my features | 0.996 / 0.989 | 0.963 / 0.795 | 0.948 / 0.691 | 0.719 / 0.353 | 0.963 / 0.843 | 0.962 / 0.734 | 0.934 / 0.723 |

- **Training on his generator transfers poorly for every model** (ROC 0.60 to 0.76 on rebuilt attacks), including M1 and M2. Training on his generator and testing on his own is near-perfect for most models: that is the artefact shortcut, and it does not depend on the architecture or features.
- **v1 -> v2 and v2 -> v1:** modest changes (his recipe 0.954 -> 0.943 ROC); M1 loses more when trained on v1 and tested on v2 (PR-AUC 0.849 -> 0.748). The v1 data is the less informative training source because of the buggy family.
- One oddity I did not resolve: M1 on my features trained on his generator scores only 0.938 on his own attacks while logistic regression and M2 get ~0.997. Trees tuned on a small validation set of artefact-laden data may have picked a poor configuration. I did not investigate further.

## 6. Held-out family (`throttled`, never used for training or tuning)
All models degrade by a similar amount: PR-AUC his 0.813 -> 0.722, M1 0.849 -> 0.776, M2 0.785 -> 0.708, XGBoost-raw 0.806 -> 0.781; oracle recall at 1% FPR 0.675 -> 0.564 (his), 0.693 -> 0.572 (M1). **No model adapts better than another.** *Caveat:* `throttled` is a weaker-parameter mixture of mechanisms the models have seen (lag + pool traffic), not a new mechanism, and it is weak by construction, so part of the drop is difficulty, not novelty. It is a mild test of generalisation. Reading B shows a larger drop (his recipe ROC 0.860 -> 0.793; M2 0.886 -> 0.784).

## 7. M4 one-class: evidence about inflation, not detection
Trained on normals only, never shown an attack (Reading A; ROC / PR-AUC / recall @ 1% FPR):

| Model | His generator | Rebuilt v2 | Held-out family |
|---|---|---|---|
| Isolation Forest, his raw features (his baseline) | 0.981 / 0.905 / 0.799 | 0.889 / 0.531 / 0.289 | 0.826 / 0.339 / 0.133 |
| Isolation Forest, my features | 0.973 / 0.848 / 0.687 | 0.866 / 0.327 / 0.079 | 0.811 / 0.224 / 0.028 |
| Autoencoder, my features | 0.976 / 0.878 / 0.766 | 0.734 / 0.360 / 0.230 | 0.788 / 0.389 / 0.245 |

A detector that has never seen an attack scores PR-AUC 0.85 to 0.91 on **his** generator and 0.33 to 0.53 on the rebuilt one. His attack set is mostly "outlier-looking", which supports the inflation conclusion: his reported numbers measure how easy his synthetic attacks are to spot. Reading B: IF 0.835 / 0.567 on his generator vs 0.732 / 0.225 on rebuilt. Deep SVDD was not run (optional).

## 8. Effect-size sweep (simulated miner signal, assumed effect sizes) with v2
Figure: `reports/stage_d/sweep_recall_A.png`. Threshold: validation 1% FPR; "onset" = first s with recall >= 0.5 (Reading A):

| Family | His recipe | M1 (mine) | M2 (mine) | Log. reg. (raw) | Autoencoder (normals only) | His recipe trained on **his** generator |
|---|---|---|---|---|---|---|
| main_thread | 0.00 | 0.00 | 0.25 | 0.75 | 0.75 | 0.50 |
| worker_pool | 0.25 | 0.25 | 0.25 | 0.75 | 1.50 | **never** |
| network_only (v2) | 0.25 | 0.25 | 0.25 | 0.50 | 1.50 | **never** |
| throttled (held-out) | 0.25 | 0.25 | 0.50 | 1.00 | 1.00 | 0.75 |

- **My models are not more sensitive to weak signals than his recipe.** The curves nearly overlap; the difference is the false-alarm floor at the same nominal threshold (realised FPR 1.8% to 2.0% vs 5.5%).
- **Below about s = -0.5 every model is at chance**; with v2, `network_only` behaves like the other families.
- The one-class autoencoder needs about 3x to 6x stronger signals and only works at all because the attacks sit in the tails.
- `network_only` has a nonzero floor (recall 0.08 to 0.23 at s = -2) because counts-only rows are themselves false-alarmed, not because anything is detected.

## 9. Per-group spread (not only bootstrap)
Reading A, PR-AUC across the 3 held-out groups (R2->ER2): his recipe 0.809 / 0.938 / 0.833 (spread 0.129); M1 0.814 / 0.978 / 0.861 (0.164); M2 0.802 / 0.979 / 0.796 (0.183). **One group is easy and two are hard for every model**, so differences between models of ~0.04 PR-AUC are smaller than the difference between groups. Full per-group tables: `reports/stage_d/tables.md`.

## 10. Deviations and limits (all recorded)
1. **Tuning is not full cross-validation:** the Optuna objective is the mean PR-AUC on two validation splits (group-held-out validation + a random 20% of the training side). **Early stopping and thresholds share the group-held-out validation set** with tuning (mild reuse).
2. **"Imbalance chosen by CV"** = chosen by that objective. **M2 reuses M1's choice** for the same fold, source and seed, it is not chosen independently.
3. **M2 was not tuned** (fixed settings) while M1 got 20 trials: the comparison favours M1.
4. **XGBoost, not LightGBM.** **Deep SVDD not run.** **His recipe with 18 features not re-run** in Stage D (it was in the Stage C v2 re-run).
5. **Models using my features trained on H attacks with raw normals**; his clip/noise on normals (which breaks uptime recovery) is kept only for his raw-feature models.
6. **Held-out family = `throttled`**, a weak variant of seen mechanisms (section 6). Tier hold-out not done.
7. **Bootstrap CIs exclude between-group variation** (3 groups in A, 2 in B). Counts-only normals: 218 (A), 104 (B).
8. **ECE** is computed on the model scores with prevalence weights; models are uncalibrated by design here.
9. **Oracle recall at 0.1% FPR** has coarse resolution on small folds (310 normals): it equals "above all normals" there.
10. The Stage C v2 re-run used the **frozen Stage C config unchanged** (only a generator-version switch and an output folder were added, default off).
11. Nothing here says anything about real miners. The ensemble, calibration, ONNX export, extension and demo were **not started**. The locked test set remains untouched.

## Files
`configs/stage_d.yaml`, `configs/synth_v2.yaml` · `src/features2.py`, `src/models2.py`, `src/metrics_d.py`, `src/stage_d.py`, `src/stage_d_report.py`, `src/v1_v2_compare.py` · `src/synth.py` (v2 flag, `exclude_families`) · `tests/test_features2.py`, `test_models2.py`, `test_metrics_d.py`, additions to `test_synth.py` · `reports/stage_d/` (`tables.md`, `main_results.json`, `sweep_*`, `v1_vs_v2_stage_c.md`, `raw/`), `reports/stage_c_v2/`
