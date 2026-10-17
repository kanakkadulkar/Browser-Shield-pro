# Stage E tables (dev folds only; simulated miner signal, assumed effect sizes)

**Reproducibility:** Stage E evaluation sets are identical to Stage D's; M1 scores differ from Stage D's stored M1/R2 scores by at most 0.00e+00.

## 1. Calibration (fit on validation only). ECE on Reading A, R2->ER2 (seed mean)

| Member | raw | Platt | isotonic |
|---|---|---|---|
| M1 | 0.157 | 0.014 | 0.017 |
| M2 | 0.081 | 0.018 | 0.024 |

Rule (lowest mean member ECE, tie -> Platt) selects: **platt** (mean ECE Platt 0.0159, isotonic 0.0208).

## 2. Fair M2: same tuning budget as M1 (20 Optuna trials, same objective and validation scheme), own imbalance choice


### Reading A, seen families (R2->ER2)

| Model | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE (raw) | Realised FPR @ val-1% | Recall @ val-1% | FPR counts-only normals |
|---|---|---|---|---|---|---|---|---|
| His recipe (Stage D) | 0.954 [0.951, 0.957] | 0.813 [0.802, 0.824] | 0.675 [0.646, 0.701] | 0.409 [0.377, 0.450] | 0.235 [0.234, 0.237] | 0.055 [0.052, 0.057] | 0.823 [0.813, 0.831] | 0.148 [0.121, 0.179] |
| M1 XGBoost (tuned) | 0.971 [0.969, 0.973] | 0.849 [0.839, 0.858] | 0.693 [0.680, 0.712] | 0.444 [0.395, 0.488] | 0.157 [0.155, 0.159] | 0.018 [0.017, 0.019] | 0.759 [0.746, 0.769] | 0.095 [0.072, 0.119] |
| M2 untuned (Stage D, M1's imbalance choice) | 0.962 [0.959, 0.964] | 0.785 [0.774, 0.798] | 0.581 [0.552, 0.613] | 0.276 [0.235, 0.341] | 0.108 [0.106, 0.111] | 0.020 [0.018, 0.022] | 0.714 [0.703, 0.725] | 0.087 [0.068, 0.107] |
| M2 TUNED (own imbalance choice) | 0.969 [0.966, 0.971] | 0.838 [0.827, 0.846] | 0.663 [0.646, 0.679] | 0.424 [0.346, 0.486] | 0.081 [0.080, 0.083] | 0.025 [0.024, 0.027] | 0.770 [0.759, 0.779] | 0.116 [0.094, 0.143] |

### Reading A, HELD-OUT family

| Model | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE (raw) | Realised FPR @ val-1% | Recall @ val-1% | FPR counts-only normals |
|---|---|---|---|---|---|---|---|---|
| His recipe (Stage D) | 0.926 [0.922, 0.930] | 0.722 [0.708, 0.738] | 0.564 [0.516, 0.602] | 0.263 [0.227, 0.294] | 0.230 [0.228, 0.232] | 0.055 [0.052, 0.057] | 0.754 [0.744, 0.765] | 0.148 [0.121, 0.179] |
| M1 XGBoost (tuned) | 0.950 [0.948, 0.953] | 0.776 [0.765, 0.786] | 0.572 [0.555, 0.593] | 0.384 [0.351, 0.416] | 0.151 [0.149, 0.152] | 0.018 [0.017, 0.019] | 0.644 [0.633, 0.657] | 0.095 [0.072, 0.119] |
| M2 untuned (Stage D, M1's imbalance choice) | 0.931 [0.928, 0.935] | 0.708 [0.695, 0.720] | 0.485 [0.458, 0.505] | 0.234 [0.202, 0.285] | 0.102 [0.100, 0.105] | 0.020 [0.018, 0.022] | 0.602 [0.589, 0.615] | 0.087 [0.068, 0.107] |
| M2 TUNED (own imbalance choice) | 0.921 [0.918, 0.925] | 0.717 [0.705, 0.728] | 0.514 [0.499, 0.533] | 0.341 [0.282, 0.385] | 0.071 [0.069, 0.072] | 0.025 [0.024, 0.027] | 0.611 [0.599, 0.623] | 0.116 [0.094, 0.143] |

Reading A tuning: M1 best objective mean 0.906 (imbalance: class_weight 7, focal 2); M2 best objective mean 0.885 (class_weight 0, focal 9); M2 final epochs median 35.

### Reading B, seen families (R2->ER2)

| Model | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE (raw) | Realised FPR @ val-1% | Recall @ val-1% | FPR counts-only normals |
|---|---|---|---|---|---|---|---|---|
| His recipe (Stage D) | 0.860 [0.848, 0.872] | 0.610 [0.580, 0.644] | 0.462 [0.426, 0.504] | 0.264 [0.199, 0.336] | 0.238 [0.236, 0.243] | 0.052 [0.046, 0.058] | 0.477 [0.450, 0.503] | 0.083 [0.054, 0.115] |
| M1 XGBoost (tuned) | 0.925 [0.919, 0.933] | 0.672 [0.650, 0.701] | 0.418 [0.386, 0.466] | 0.286 [0.272, 0.335] | 0.214 [0.211, 0.218] | 0.022 [0.018, 0.025] | 0.499 [0.473, 0.525] | 0.061 [0.035, 0.094] |
| M2 untuned (Stage D, M1's imbalance choice) | 0.886 [0.875, 0.896] | 0.548 [0.520, 0.578] | 0.379 [0.340, 0.415] | 0.212 [0.185, 0.271] | 0.149 [0.144, 0.155] | 0.015 [0.013, 0.019] | 0.397 [0.377, 0.420] | 0.103 [0.071, 0.133] |
| M2 TUNED (own imbalance choice) | 0.899 [0.891, 0.907] | 0.512 [0.487, 0.541] | 0.353 [0.313, 0.392] | 0.203 [0.183, 0.256] | 0.130 [0.125, 0.134] | 0.008 [0.006, 0.011] | 0.336 [0.314, 0.358] | 0.016 [0.003, 0.029] |

### Reading B, HELD-OUT family

| Model | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE (raw) | Realised FPR @ val-1% | Recall @ val-1% | FPR counts-only normals |
|---|---|---|---|---|---|---|---|---|
| His recipe (Stage D) | 0.793 [0.776, 0.809] | 0.481 [0.452, 0.522] | 0.341 [0.309, 0.394] | 0.158 [0.127, 0.239] | 0.231 [0.228, 0.235] | 0.052 [0.046, 0.058] | 0.368 [0.344, 0.391] | 0.083 [0.054, 0.115] |
| M1 XGBoost (tuned) | 0.881 [0.870, 0.891] | 0.588 [0.564, 0.620] | 0.358 [0.333, 0.400] | 0.261 [0.243, 0.299] | 0.207 [0.204, 0.212] | 0.022 [0.018, 0.025] | 0.415 [0.391, 0.441] | 0.061 [0.035, 0.094] |
| M2 untuned (Stage D, M1's imbalance choice) | 0.784 [0.771, 0.798] | 0.391 [0.366, 0.420] | 0.246 [0.219, 0.269] | 0.158 [0.130, 0.187] | 0.143 [0.137, 0.150] | 0.015 [0.013, 0.019] | 0.247 [0.229, 0.265] | 0.103 [0.071, 0.133] |
| M2 TUNED (own imbalance choice) | 0.822 [0.810, 0.834] | 0.401 [0.379, 0.425] | 0.276 [0.246, 0.301] | 0.142 [0.123, 0.198] | 0.120 [0.116, 0.125] | 0.008 [0.006, 0.011] | 0.264 [0.244, 0.284] | 0.016 [0.003, 0.029] |

Reading B tuning: M1 best objective mean 0.805 (imbalance: class_weight 5, focal 1); M2 best objective mean 0.835 (class_weight 2, focal 4); M2 final epochs median 35.

## 3. Counts-only regime handling (calibration: platt; thresholds fixed on validation, 1% FPR target)

Separate counts-only model available (enough training counts-only rows) in fold-seed fits: {'A': (9, 9), 'B': (4, 6)}. Where it is unavailable, Vb/Vab fall back to V0/Va for that fold.


### Reading A (R2 -> ER2, seen families) [95% CI]

| Base | Variant | FPR counts-only normals | FPR other normals | Overall FPR | Recall (all attacks) | Recall (counts-only attacks) |
|---|---|---|---|---|---|---|
| m1 | V0 | 0.093 [0.073, 0.110] | 0.016 [0.014, 0.017] | 0.018 [0.016, 0.020] | 0.758 [0.748, 0.769] | 0.725 [0.696, 0.748] |
| m1 | Va | 0.044 [0.029, 0.060] | 0.028 [0.026, 0.030] | 0.029 [0.026, 0.031] | 0.798 [0.788, 0.808] | 0.709 [0.674, 0.736] |
| m1 | Vb | 0.119 [0.099, 0.145] | 0.012 [0.011, 0.013] | 0.015 [0.013, 0.016] | 0.728 [0.718, 0.740] | 0.679 [0.647, 0.705] |
| m1 | Vab | 0.043 [0.026, 0.060] | 0.028 [0.026, 0.030] | 0.029 [0.026, 0.031] | 0.783 [0.772, 0.793] | 0.607 [0.575, 0.636] |
| m2 | V0 | 0.116 [0.096, 0.139] | 0.023 [0.021, 0.025] | 0.025 [0.023, 0.027] | 0.770 [0.760, 0.779] | 0.749 [0.721, 0.775] |
| m2 | Va | 0.054 [0.035, 0.067] | 0.030 [0.028, 0.032] | 0.030 [0.028, 0.032] | 0.795 [0.785, 0.803] | 0.693 [0.662, 0.721] |
| m2 | Vb | 0.162 [0.135, 0.193] | 0.019 [0.017, 0.020] | 0.022 [0.021, 0.024] | 0.745 [0.736, 0.754] | 0.736 [0.706, 0.760] |
| m2 | Vab | 0.043 [0.026, 0.060] | 0.030 [0.028, 0.032] | 0.030 [0.028, 0.032] | 0.782 [0.771, 0.792] | 0.607 [0.575, 0.636] |
| ens | V0 | 0.112 [0.092, 0.136] | 0.019 [0.017, 0.021] | 0.021 [0.019, 0.023] | 0.775 [0.766, 0.784] | 0.728 [0.700, 0.753] |
| ens | Va | 0.050 [0.035, 0.066] | 0.030 [0.027, 0.032] | 0.030 [0.028, 0.032] | 0.815 [0.805, 0.824] | 0.700 [0.667, 0.728] |
| ens | Vb | 0.144 [0.121, 0.173] | 0.014 [0.012, 0.015] | 0.017 [0.016, 0.019] | 0.742 [0.730, 0.751] | 0.703 [0.670, 0.731] |
| ens | Vab | 0.043 [0.026, 0.060] | 0.030 [0.027, 0.032] | 0.030 [0.028, 0.032] | 0.801 [0.790, 0.810] | 0.607 [0.575, 0.636] |

### Reading B (R2 -> ER2, seen families) [95% CI]

| Base | Variant | FPR counts-only normals | FPR other normals | Overall FPR | Recall (all attacks) | Recall (counts-only attacks) |
|---|---|---|---|---|---|---|
| m1 | V0 | 0.061 [0.038, 0.087] | 0.019 [0.016, 0.023] | 0.022 [0.018, 0.025] | 0.495 [0.470, 0.524] | 0.455 [0.390, 0.523] |
| m1 | Va | 0.061 [0.038, 0.090] | 0.058 [0.052, 0.064] | 0.058 [0.052, 0.065] | 0.545 [0.518, 0.571] | 0.465 [0.399, 0.528] |
| m1 | Vb | 0.064 [0.038, 0.099] | 0.019 [0.016, 0.023] | 0.022 [0.018, 0.026] | 0.502 [0.475, 0.528] | 0.551 [0.479, 0.609] |
| m1 | Vab | 0.051 [0.032, 0.080] | 0.058 [0.052, 0.064] | 0.057 [0.052, 0.064] | 0.553 [0.526, 0.578] | 0.529 [0.465, 0.593] |
| m2 | V0 | 0.010 [0.000, 0.022] | 0.007 [0.005, 0.010] | 0.007 [0.005, 0.010] | 0.320 [0.302, 0.340] | 0.202 [0.153, 0.248] |
| m2 | Va | 0.010 [0.000, 0.019] | 0.018 [0.014, 0.021] | 0.017 [0.013, 0.020] | 0.379 [0.359, 0.398] | 0.233 [0.189, 0.272] |
| m2 | Vb | 0.022 [0.006, 0.045] | 0.005 [0.003, 0.007] | 0.006 [0.004, 0.008] | 0.287 [0.270, 0.304] | 0.293 [0.244, 0.333] |
| m2 | Vab | 0.019 [0.006, 0.035] | 0.018 [0.014, 0.021] | 0.018 [0.014, 0.021] | 0.385 [0.366, 0.404] | 0.277 [0.227, 0.322] |
| ens | V0 | 0.026 [0.010, 0.045] | 0.010 [0.008, 0.013] | 0.011 [0.009, 0.014] | 0.458 [0.436, 0.482] | 0.426 [0.369, 0.484] |
| ens | Va | 0.029 [0.013, 0.048] | 0.037 [0.033, 0.042] | 0.037 [0.033, 0.041] | 0.507 [0.485, 0.529] | 0.430 [0.369, 0.491] |
| ens | Vb | 0.029 [0.013, 0.051] | 0.009 [0.006, 0.011] | 0.010 [0.008, 0.013] | 0.453 [0.427, 0.479] | 0.451 [0.402, 0.510] |
| ens | Vab | 0.022 [0.006, 0.042] | 0.037 [0.033, 0.042] | 0.037 [0.032, 0.041] | 0.506 [0.484, 0.527] | 0.423 [0.361, 0.474] |

### Group counts (counts-only normals per held-out group) and per-group counts-only FPR (seed mean), Reading A and B

| Reading | Group | counts-only normals | other normals | m1/V0 | m1/Vab | m2/V0 | m2/Vab | ens/V0 | ens/Vab |
|---|---|---|---|---|---|---|---|---|---|
| A | group 1 | 82 | 1313 | 0.224 | 0.065 | 0.252 | 0.065 | 0.260 | 0.065 |
| A | group 2 | 22 | 288 | 0.076 | 0.000 | 0.030 | 0.000 | 0.076 | 0.000 |
| A | group 3 | 114 | 6503 | 0.003 | 0.035 | 0.035 | 0.035 | 0.012 | 0.035 |
| B | group 1 | 82 | 1313 | 0.053 | 0.053 | 0.012 | 0.012 | 0.012 | 0.016 |
| B | group 2 | 22 | 288 | 0.091 | 0.045 | 0.000 | 0.045 | 0.076 | 0.045 |

**Selection rule applied (Reading A):** m1: **V0** (no eligible variant beats V0 by the required margin); m2: **V0** (no eligible variant beats V0 by the required margin); ens: **V0** (no eligible variant beats V0 by the required margin)

## 4. Stacked ensemble vs its members (calibrated, platt)


### Reading A, seen families

| Score | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE |
|---|---|---|---|---|---|
| M1 calibrated | 0.970 [0.968, 0.973] | 0.854 [0.846, 0.862] | 0.693 [0.680, 0.712] | 0.446 [0.398, 0.490] | 0.014 [0.013, 0.016] |
| M2 (tuned) calibrated | 0.970 [0.968, 0.972] | 0.842 [0.832, 0.851] | 0.663 [0.646, 0.679] | 0.424 [0.346, 0.486] | 0.018 [0.017, 0.019] |
| Stacked ensemble | 0.974 [0.972, 0.976] | 0.866 [0.858, 0.873] | 0.709 [0.694, 0.724] | 0.523 [0.472, 0.551] | 0.015 [0.014, 0.017] |

### Reading A, held-out family

| Score | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE |
|---|---|---|---|---|---|
| M1 calibrated | 0.950 [0.947, 0.953] | 0.785 [0.775, 0.794] | 0.572 [0.555, 0.593] | 0.387 [0.353, 0.416] | 0.020 [0.019, 0.022] |
| M2 (tuned) calibrated | 0.925 [0.921, 0.929] | 0.723 [0.711, 0.733] | 0.514 [0.499, 0.533] | 0.341 [0.283, 0.385] | 0.031 [0.030, 0.033] |
| Stacked ensemble | 0.948 [0.946, 0.951] | 0.775 [0.765, 0.784] | 0.560 [0.540, 0.578] | 0.415 [0.384, 0.434] | 0.026 [0.024, 0.028] |

### Reading B, seen families

| Score | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE |
|---|---|---|---|---|---|
| M1 calibrated | 0.926 [0.919, 0.933] | 0.665 [0.644, 0.695] | 0.418 [0.386, 0.467] | 0.286 [0.272, 0.335] | 0.028 [0.027, 0.033] |
| M2 (tuned) calibrated | 0.866 [0.857, 0.875] | 0.502 [0.480, 0.530] | 0.353 [0.313, 0.392] | 0.205 [0.185, 0.258] | 0.056 [0.053, 0.060] |
| Stacked ensemble | 0.791 [0.778, 0.805] | 0.586 [0.564, 0.617] | 0.443 [0.400, 0.486] | 0.276 [0.260, 0.333] | 0.038 [0.036, 0.042] |

### Reading B, held-out family

| Score | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE |
|---|---|---|---|---|---|
| M1 calibrated | 0.888 [0.878, 0.899] | 0.584 [0.561, 0.618] | 0.358 [0.333, 0.400] | 0.261 [0.243, 0.299] | 0.035 [0.033, 0.039] |
| M2 (tuned) calibrated | 0.800 [0.789, 0.813] | 0.420 [0.398, 0.444] | 0.276 [0.246, 0.301] | 0.141 [0.123, 0.199] | 0.068 [0.064, 0.072] |
| Stacked ensemble | 0.747 [0.733, 0.761] | 0.515 [0.493, 0.543] | 0.357 [0.323, 0.386] | 0.240 [0.226, 0.287] | 0.045 [0.043, 0.049] |

### Per-group PR-AUC (seed mean, R2->ER2) and the paired comparison

| Reading | Score | group 1 | group 2 | group 3 | spread (max-min) |
|---|---|---|---|---|---|
| A | m1 | 0.814 | 0.978 | 0.861 0.164 |
| A | m2 | 0.811 | 0.969 | 0.843 0.158 |
| A | ens | 0.825 | 0.981 | 0.872 0.157 |
| B | m1 | 0.594 | 0.940 |  0.346 |
| B | m2 | 0.479 | 0.919 |  0.440 |
| B | ens | 0.532 | 0.936 |  0.404 |

**Reading A:** ensemble PR-AUC 0.866 vs best member (M1) 0.854: improvement +0.012; that member's per-group spread is 0.164; paired per-group differences [0.011, 0.003, 0.012]. **Beats its best member by more than the per-group spread: NO.**

**Reading B:** ensemble PR-AUC 0.586 vs best member (M1) 0.665: improvement -0.079; that member's per-group spread is 0.346; paired per-group differences [-0.063, -0.005]. **Beats its best member by more than the per-group spread: NO.**

**Final base by rule:** M1 with regime variant V0.

## 5. Threshold policy for the final pipeline (M1, V0, platt)

Candidate levels (validation-quantile FPR for 'dangerous'), pooled over held-out dev groups, R2->ER2:

| Reading | Level | Pooled realised FPR | Worst-group FPR | Per-group FPR | Recall |
|---|---|---|---|---|---|
| A | 0.01 | 0.018 | 0.021 | 0.021, 0.010, 0.017 | 0.758 |
| A | 0.005 | 0.011 | 0.015 | 0.015, 0.000, 0.011 | 0.707 |
| A | 0.0025 | 0.010 | 0.014 | 0.014, 0.000, 0.009 | 0.685 |
| B | 0.01 | 0.022 | 0.024 | 0.024, 0.011 | 0.495 |
| B | 0.005 | 0.013 | 0.016 | 0.016, 0.003 | 0.425 |
| B | 0.0025 | 0.011 | 0.013 | 0.013, 0.002 | 0.405 |

Rule (largest level with pooled FPR <= 0.01 and worst group <= 0.02 on Reading A) selects **0.0025**.

### Per held-out group at the chosen policy (seed mean): verdicts = unsure | dangerous | suspicious | safe

| Reading | Set | Group | FPR dangerous (all normals) | FPR dangerous (decided only) | Recall dangerous | Recall danger+suspicious | Unsure: normals | Unsure: attacks | FPR counts-only normals |
|---|---|---|---|---|---|---|---|---|---|
| A | ER2 | group 1 | 0.014 | 0.014 | 0.630 | 0.887 | 0.000 | 0.000 | 0.130 |
| A | ER2 | group 2 | 0.000 | 0.000 | 0.791 | 0.979 | 0.000 | 0.000 | 0.000 |
| A | ER2 | group 3 | 0.009 | 0.009 | 0.686 | 0.944 | 0.004 | 0.009 | 0.000 |
| A | EHO | group 1 | 0.014 | 0.014 | 0.586 | 0.837 | 0.000 | 0.000 | 0.130 |
| A | EHO | group 2 | 0.000 | 0.000 | 0.735 | 0.880 | 0.000 | 0.000 | 0.000 |
| A | EHO | group 3 | 0.009 | 0.009 | 0.554 | 0.902 | 0.004 | 0.002 | 0.000 |
| B | ER2 | group 1 | 0.011 | 0.017 | 0.219 | 0.440 | 0.341 | 0.338 | 0.020 |
| B | ER2 | group 2 | 0.002 | 0.002 | 0.662 | 0.919 | 0.000 | 0.004 | 0.000 |
| B | EHO | group 1 | 0.011 | 0.017 | 0.177 | 0.363 | 0.341 | 0.370 | 0.020 |
| B | EHO | group 2 | 0.002 | 0.002 | 0.462 | 0.714 | 0.000 | 0.000 | 0.000 |

## 6. Effect-size sweep of the final pipeline (simulated miner signal, assumed effect sizes; recall counts unsure as a miss)

| Reading | Family | His recipe onset s | Final onset s | His recall s=0 | Final recall s=0 | His recall s=1 | Final recall s=1 | Final unsure at s=1.5 |
|---|---|---|---|---|---|---|---|---|
| A | main_thread | 0.00 | 0.25 | 0.629 | 0.455 | 0.987 | 0.940 | 0.333 |
| A | worker_pool | 0.25 | 0.50 | 0.326 | 0.155 | 0.856 | 0.790 | 0.210 |
| A | network_only | 0.25 | 0.50 | 0.404 | 0.219 | 0.973 | 0.924 | 0.205 |
| A | throttled | 0.25 | 0.50 | 0.215 | 0.069 | 0.947 | 0.924 | 0.333 |
| B | main_thread | 0.25 | 0.50 | 0.163 | 0.111 | 0.949 | 0.425 | 1.000 |
| B | worker_pool | 0.50 | 0.50 | 0.089 | 0.078 | 0.753 | 0.575 | 0.734 |
| B | network_only | 0.50 | 0.75 | 0.097 | 0.058 | 0.861 | 0.671 | 0.721 |
| B | throttled | 0.50 | 0.75 | 0.039 | 0.016 | 0.854 | 0.644 | 1.000 |