
## READING A


### C3  R2->ER2 (v2 -> v2, seen families): ranking quality (oracle thresholds on the held-out group)

| Model | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE |
|---|---|---|---|---|---|
| His recipe (11 raw features) | 0.954 [0.951, 0.957] | 0.813 [0.802, 0.824] | 0.675 [0.646, 0.701] | 0.409 [0.377, 0.450] | 0.235 [0.234, 0.237] |
| Logistic regression (raw 11) | 0.918 [0.913, 0.922] | 0.638 [0.621, 0.654] | 0.364 [0.345, 0.380] | 0.138 [0.063, 0.152] | 0.205 [0.203, 0.208] |
| Best single feature (raw 11) | 0.883 [0.879, 0.887] | 0.535 [0.522, 0.546] | 0.295 [0.275, 0.313] | 0.200 [0.185, 0.216] | n/a |
| M1 XGBoost on his 11 raw features (ablation) | 0.947 [0.944, 0.951] | 0.806 [0.796, 0.816] | 0.664 [0.648, 0.688] | 0.537 [0.468, 0.558] | 0.253 [0.250, 0.255] |
| Logistic regression (my features) | 0.963 [0.961, 0.965] | 0.795 [0.786, 0.805] | 0.592 [0.567, 0.603] | 0.393 [0.372, 0.421] | 0.117 [0.115, 0.120] |
| M1 XGBoost, my features | 0.971 [0.969, 0.973] | 0.849 [0.839, 0.858] | 0.693 [0.680, 0.712] | 0.444 [0.395, 0.488] | 0.157 [0.155, 0.159] |
| M2 feature-token attention net, my features | 0.962 [0.959, 0.964] | 0.785 [0.774, 0.798] | 0.581 [0.552, 0.613] | 0.276 [0.235, 0.341] | 0.108 [0.106, 0.111] |

### C3  R2->ER2 (v2 -> v2, seen families): threshold transfer (thresholds fixed on validation of the training side)

| Model | FPR @ val-1% thr | Recall @ val-1% thr | FPR @ his rule | Recall @ his rule | F1 @ his rule | FPR on counts-only normals (val-1%) | (his rule) | per-group FPR @ val-1% [min..max] |
|---|---|---|---|---|---|---|---|---|
| His recipe (11 raw features) | 0.055 [0.052, 0.057] | 0.823 [0.813, 0.831] | 0.254 [0.249, 0.259] | 0.925 [0.918, 0.931] | 0.443 [0.436, 0.449] | 0.148 [0.121, 0.179] | 0.495 [0.463, 0.528] | 0.005 .. 0.065 |
| Logistic regression (raw 11) | 0.029 [0.027, 0.031] | 0.596 [0.584, 0.609] | 0.514 [0.509, 0.518] | 0.947 [0.942, 0.952] | 0.302 [0.297, 0.306] | 0.075 [0.056, 0.098] | 0.813 [0.789, 0.838] | 0.005 .. 0.031 |
| Best single feature (raw 11) | 0.041 [0.039, 0.044] | 0.481 [0.468, 0.493] | 0.398 [0.392, 0.403] | 0.956 [0.951, 0.961] | 0.306 [0.303, 0.310] | 0.023 [0.014, 0.036] | 0.683 [0.649, 0.719] | 0.003 .. 0.048 |
| M1 XGBoost on his 11 raw features (ablation) | 0.049 [0.046, 0.051] | 0.818 [0.808, 0.827] | 0.164 [0.160, 0.169] | 0.917 [0.911, 0.924] | 0.518 [0.510, 0.525] | 0.098 [0.076, 0.125] | 0.398 [0.362, 0.435] | 0.008 .. 0.057 |
| Logistic regression (my features) | 0.032 [0.030, 0.034] | 0.720 [0.709, 0.730] | 0.223 [0.218, 0.228] | 0.961 [0.956, 0.966] | 0.439 [0.434, 0.445] | 0.222 [0.190, 0.255] | 0.538 [0.504, 0.582] | 0.009 .. 0.041 |
| M1 XGBoost, my features | 0.018 [0.017, 0.019] | 0.759 [0.746, 0.769] | 0.151 [0.147, 0.155] | 0.926 [0.919, 0.932] | 0.531 [0.524, 0.539] | 0.095 [0.072, 0.119] | 0.422 [0.385, 0.457] | 0.010 .. 0.021 |
| M2 feature-token attention net, my features | 0.020 [0.018, 0.022] | 0.714 [0.703, 0.725] | 0.127 [0.124, 0.131] | 0.917 [0.910, 0.923] | 0.571 [0.564, 0.579] | 0.087 [0.068, 0.107] | 0.462 [0.428, 0.495] | 0.000 .. 0.022 |

### CHO R2->EHO (v2 -> HELD-OUT family): ranking quality (oracle thresholds on the held-out group)

| Model | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE |
|---|---|---|---|---|---|
| His recipe (11 raw features) | 0.926 [0.922, 0.930] | 0.722 [0.708, 0.738] | 0.564 [0.516, 0.602] | 0.263 [0.227, 0.294] | 0.230 [0.228, 0.232] |
| Logistic regression (raw 11) | 0.830 [0.824, 0.836] | 0.392 [0.376, 0.408] | 0.150 [0.135, 0.160] | 0.021 [0.005, 0.030] | 0.191 [0.188, 0.193] |
| Best single feature (raw 11) | 0.785 [0.779, 0.791] | 0.256 [0.245, 0.265] | 0.082 [0.072, 0.095] | 0.031 [0.025, 0.039] | n/a |
| M1 XGBoost on his 11 raw features (ablation) | 0.929 [0.925, 0.933] | 0.781 [0.770, 0.792] | 0.618 [0.606, 0.637] | 0.535 [0.445, 0.552] | 0.250 [0.248, 0.252] |
| Logistic regression (my features) | 0.948 [0.946, 0.951] | 0.691 [0.676, 0.704] | 0.442 [0.418, 0.455] | 0.235 [0.210, 0.262] | 0.112 [0.109, 0.115] |
| M1 XGBoost, my features | 0.950 [0.948, 0.953] | 0.776 [0.765, 0.786] | 0.572 [0.555, 0.593] | 0.384 [0.351, 0.416] | 0.151 [0.149, 0.152] |
| M2 feature-token attention net, my features | 0.931 [0.928, 0.935] | 0.708 [0.695, 0.720] | 0.485 [0.458, 0.505] | 0.234 [0.202, 0.285] | 0.102 [0.100, 0.105] |

### CHO R2->EHO (v2 -> HELD-OUT family): threshold transfer (thresholds fixed on validation of the training side)

| Model | FPR @ val-1% thr | Recall @ val-1% thr | FPR @ his rule | Recall @ his rule | F1 @ his rule | FPR on counts-only normals (val-1%) | (his rule) | per-group FPR @ val-1% [min..max] |
|---|---|---|---|---|---|---|---|---|
| His recipe (11 raw features) | 0.055 [0.052, 0.057] | 0.754 [0.744, 0.765] | 0.254 [0.249, 0.259] | 0.881 [0.872, 0.889] | 0.424 [0.417, 0.430] | 0.148 [0.121, 0.179] | 0.495 [0.463, 0.528] | 0.005 .. 0.065 |
| Logistic regression (raw 11) | 0.029 [0.027, 0.031] | 0.350 [0.338, 0.361] | 0.514 [0.509, 0.518] | 0.854 [0.848, 0.863] | 0.270 [0.265, 0.275] | 0.075 [0.056, 0.098] | 0.813 [0.789, 0.838] | 0.005 .. 0.031 |
| Best single feature (raw 11) | 0.041 [0.039, 0.044] | 0.217 [0.206, 0.227] | 0.398 [0.392, 0.403] | 0.873 [0.865, 0.881] | 0.281 [0.277, 0.285] | 0.023 [0.014, 0.036] | 0.683 [0.649, 0.719] | 0.003 .. 0.048 |
| M1 XGBoost on his 11 raw features (ablation) | 0.049 [0.046, 0.051] | 0.805 [0.795, 0.815] | 0.164 [0.160, 0.169] | 0.890 [0.882, 0.898] | 0.508 [0.500, 0.515] | 0.098 [0.076, 0.125] | 0.398 [0.362, 0.435] | 0.008 .. 0.057 |
| Logistic regression (my features) | 0.032 [0.030, 0.034] | 0.603 [0.593, 0.614] | 0.223 [0.218, 0.228] | 0.937 [0.932, 0.943] | 0.429 [0.424, 0.436] | 0.222 [0.190, 0.255] | 0.538 [0.504, 0.582] | 0.009 .. 0.041 |
| M1 XGBoost, my features | 0.018 [0.017, 0.019] | 0.644 [0.633, 0.657] | 0.151 [0.147, 0.155] | 0.878 [0.871, 0.886] | 0.510 [0.503, 0.517] | 0.095 [0.072, 0.119] | 0.422 [0.385, 0.457] | 0.010 .. 0.021 |
| M2 feature-token attention net, my features | 0.020 [0.018, 0.022] | 0.602 [0.589, 0.615] | 0.127 [0.124, 0.131] | 0.846 [0.838, 0.855] | 0.540 [0.531, 0.548] | 0.087 [0.068, 0.107] | 0.462 [0.428, 0.495] | 0.000 .. 0.022 |

### Cross-generator transfer: ROC-AUC / PR-AUC (prevalence 8.35%), [95% CI on ROC]

| Model | C2  H->EH | C3  R2->ER2 | CHO R2->EHO | C4a H->ER2 | C4b R2->EH | C5a R1->ER2 | C5b R2->ER1 |
|---|---|---|---|---|---|---|---|
| His recipe (11 raw features) | 0.999 / 0.997 | 0.954 / 0.813 | 0.926 / 0.722 | 0.708 / 0.416 | 0.972 / 0.827 | 0.943 / 0.760 | 0.932 / 0.750 |
| Logistic regression (raw 11) | 0.992 / 0.959 | 0.918 / 0.638 | 0.830 / 0.392 | 0.760 / 0.464 | 0.511 / 0.219 | 0.916 / 0.619 | 0.887 / 0.566 |
| Best single feature (raw 11) | 0.938 / 0.800 | 0.883 / 0.535 | 0.785 / 0.256 | 0.523 / 0.148 | 0.899 / 0.551 | 0.884 / 0.534 | 0.846 / 0.451 |
| M1 XGBoost on his 11 raw features (ablation) | 0.989 / 0.969 | 0.947 / 0.806 | 0.929 / 0.781 | 0.703 / 0.306 | 0.956 / 0.752 | 0.948 / 0.791 | 0.924 / 0.742 |
| Logistic regression (my features) | 0.996 / 0.989 | 0.963 / 0.795 | 0.948 / 0.691 | 0.719 / 0.353 | 0.963 / 0.843 | 0.962 / 0.734 | 0.934 / 0.723 |
| M1 XGBoost, my features | 0.938 / 0.802 | 0.971 / 0.849 | 0.950 / 0.776 | 0.692 / 0.294 | 0.959 / 0.665 | 0.941 / 0.748 | 0.948 / 0.782 |
| M2 feature-token attention net, my features | 0.998 / 0.993 | 0.962 / 0.785 | 0.931 / 0.708 | 0.595 / 0.230 | 0.950 / 0.682 | 0.968 / 0.780 | 0.937 / 0.725 |

### M4 one-class (trained on normals only, never sees attacks): evidence about inflation, NOT detection

| Model | his generator: ROC / PR / recall@1%FPR | rebuilt v2 (seen families) | held-out family |
|---|---|---|---|
| M4 Isolation Forest (raw 11, his baseline) | 0.981 / 0.905 / 0.799 | 0.889 / 0.531 / 0.289 | 0.826 / 0.339 / 0.133 |
| M4 Isolation Forest (my features) | 0.973 / 0.848 / 0.687 | 0.866 / 0.327 / 0.079 | 0.811 / 0.224 / 0.028 |
| M4 Autoencoder (my features) | 0.976 / 0.878 / 0.766 | 0.734 / 0.360 / 0.230 | 0.788 / 0.389 / 0.245 |

### Per-group spread (seed-mean per validation group), R2->ER2 and held-out family

| Cond | Model | group 1 | group 2 | group 3 | spread (max-min) PR-AUC |
|---|---|---|---|---|---|
| C3 | His recipe (11 raw features) | ROC 0.948 PR 0.809 FPR 0.019 | ROC 0.992 PR 0.938 FPR 0.005 | ROC 0.959 PR 0.833 FPR 0.065 | 0.129 |
| C3 | Logistic regression (raw 11) | ROC 0.891 PR 0.581 FPR 0.025 | ROC 0.944 PR 0.691 FPR 0.005 | ROC 0.923 PR 0.652 FPR 0.031 | 0.111 |
| C3 | Best single feature (raw 11) | ROC 0.844 PR 0.458 FPR 0.048 | ROC 0.963 PR 0.689 FPR 0.003 | ROC 0.898 PR 0.559 FPR 0.042 | 0.231 |
| C3 | M1 XGBoost on his 11 raw features (ablation) | ROC 0.956 PR 0.804 FPR 0.020 | ROC 0.997 PR 0.971 FPR 0.008 | ROC 0.965 PR 0.834 FPR 0.057 | 0.168 |
| C3 | Logistic regression (my features) | ROC 0.939 PR 0.676 FPR 0.041 | ROC 0.991 PR 0.911 FPR 0.009 | ROC 0.967 PR 0.822 FPR 0.031 | 0.235 |
| C3 | M1 XGBoost, my features | ROC 0.959 PR 0.814 FPR 0.021 | ROC 0.997 PR 0.978 FPR 0.010 | ROC 0.975 PR 0.861 FPR 0.018 | 0.164 |
| C3 | M2 feature-token attention net, my features | ROC 0.954 PR 0.802 FPR 0.022 | ROC 0.997 PR 0.979 FPR 0.000 | ROC 0.968 PR 0.796 FPR 0.021 | 0.183 |
| CHO | His recipe (11 raw features) | ROC 0.918 PR 0.721 FPR 0.019 | ROC 0.972 PR 0.860 FPR 0.005 | ROC 0.932 PR 0.742 FPR 0.065 | 0.140 |
| CHO | Logistic regression (raw 11) | ROC 0.766 PR 0.238 FPR 0.025 | ROC 0.859 PR 0.325 FPR 0.005 | ROC 0.849 PR 0.428 FPR 0.031 | 0.190 |
| CHO | Best single feature (raw 11) | ROC 0.742 PR 0.200 FPR 0.048 | ROC 0.922 PR 0.393 FPR 0.003 | ROC 0.814 PR 0.276 FPR 0.042 | 0.193 |
| CHO | M1 XGBoost on his 11 raw features (ablation) | ROC 0.940 PR 0.777 FPR 0.020 | ROC 0.988 PR 0.926 FPR 0.008 | ROC 0.946 PR 0.811 FPR 0.057 | 0.148 |
| CHO | Logistic regression (my features) | ROC 0.916 PR 0.509 FPR 0.041 | ROC 0.973 PR 0.756 FPR 0.009 | ROC 0.954 PR 0.738 FPR 0.031 | 0.247 |
| CHO | M1 XGBoost, my features | ROC 0.942 PR 0.761 FPR 0.021 | ROC 0.989 PR 0.929 FPR 0.010 | ROC 0.956 PR 0.787 FPR 0.018 | 0.168 |
| CHO | M2 feature-token attention net, my features | ROC 0.909 PR 0.693 FPR 0.022 | ROC 0.983 PR 0.923 FPR 0.000 | ROC 0.943 PR 0.717 FPR 0.021 | 0.230 |

## READING B


### C3  R2->ER2 (v2 -> v2, seen families): ranking quality (oracle thresholds on the held-out group)

| Model | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE |
|---|---|---|---|---|---|
| His recipe (11 raw features) | 0.860 [0.848, 0.872] | 0.610 [0.580, 0.644] | 0.462 [0.426, 0.504] | 0.264 [0.199, 0.336] | 0.238 [0.236, 0.243] |
| Logistic regression (raw 11) | 0.783 [0.766, 0.801] | 0.356 [0.332, 0.387] | 0.197 [0.162, 0.256] | 0.101 [0.084, 0.131] | 0.140 [0.133, 0.147] |
| Best single feature (raw 11) | 0.841 [0.831, 0.851] | 0.448 [0.426, 0.477] | 0.263 [0.240, 0.304] | 0.164 [0.145, 0.201] | n/a |
| M1 XGBoost on his 11 raw features (ablation) | 0.918 [0.911, 0.926] | 0.619 [0.595, 0.653] | 0.393 [0.358, 0.462] | 0.207 [0.194, 0.268] | 0.186 [0.183, 0.191] |
| Logistic regression (my features) | 0.910 [0.903, 0.917] | 0.594 [0.567, 0.623] | 0.368 [0.335, 0.404] | 0.230 [0.186, 0.271] | 0.074 [0.070, 0.079] |
| M1 XGBoost, my features | 0.925 [0.919, 0.933] | 0.672 [0.650, 0.701] | 0.418 [0.386, 0.466] | 0.286 [0.272, 0.335] | 0.214 [0.211, 0.218] |
| M2 feature-token attention net, my features | 0.886 [0.875, 0.896] | 0.548 [0.520, 0.578] | 0.379 [0.340, 0.415] | 0.212 [0.185, 0.271] | 0.149 [0.144, 0.155] |

### C3  R2->ER2 (v2 -> v2, seen families): threshold transfer (thresholds fixed on validation of the training side)

| Model | FPR @ val-1% thr | Recall @ val-1% thr | FPR @ his rule | Recall @ his rule | F1 @ his rule | FPR on counts-only normals (val-1%) | (his rule) | per-group FPR @ val-1% [min..max] |
|---|---|---|---|---|---|---|---|---|
| His recipe (11 raw features) | 0.052 [0.046, 0.058] | 0.477 [0.450, 0.503] | 0.515 [0.502, 0.525] | 0.870 [0.852, 0.888] | 0.244 [0.236, 0.251] | 0.083 [0.054, 0.115] | 0.583 [0.524, 0.637] | 0.001 .. 0.064 |
| Logistic regression (raw 11) | 0.059 [0.054, 0.066] | 0.440 [0.412, 0.464] | 0.247 [0.239, 0.259] | 0.705 [0.680, 0.728] | 0.334 [0.319, 0.349] | 0.035 [0.015, 0.054] | 0.635 [0.592, 0.674] | 0.004 .. 0.071 |
| Best single feature (raw 11) | 0.044 [0.038, 0.049] | 0.385 [0.358, 0.415] | 0.378 [0.364, 0.390] | 0.895 [0.880, 0.909] | 0.301 [0.292, 0.311] | 0.048 [0.026, 0.075] | 0.660 [0.614, 0.707] | 0.003 .. 0.053 |
| M1 XGBoost on his 11 raw features (ablation) | 0.029 [0.025, 0.033] | 0.532 [0.510, 0.559] | 0.187 [0.179, 0.198] | 0.813 [0.795, 0.832] | 0.434 [0.417, 0.448] | 0.192 [0.158, 0.237] | 0.522 [0.471, 0.577] | 0.003 .. 0.035 |
| Logistic regression (my features) | 0.024 [0.020, 0.028] | 0.416 [0.393, 0.441] | 0.115 [0.109, 0.123] | 0.653 [0.629, 0.673] | 0.451 [0.433, 0.469] | 0.154 [0.123, 0.190] | 0.513 [0.465, 0.562] | 0.005 .. 0.028 |
| M1 XGBoost, my features | 0.022 [0.018, 0.025] | 0.499 [0.473, 0.525] | 0.177 [0.167, 0.186] | 0.811 [0.792, 0.831] | 0.453 [0.438, 0.472] | 0.061 [0.035, 0.094] | 0.587 [0.536, 0.637] | 0.011 .. 0.024 |
| M2 feature-token attention net, my features | 0.015 [0.013, 0.019] | 0.397 [0.377, 0.420] | 0.102 [0.095, 0.110] | 0.638 [0.617, 0.663] | 0.481 [0.458, 0.502] | 0.103 [0.071, 0.133] | 0.474 [0.418, 0.530] | 0.012 .. 0.016 |

### CHO R2->EHO (v2 -> HELD-OUT family): ranking quality (oracle thresholds on the held-out group)

| Model | ROC-AUC | PR-AUC (8.35%) | Recall @ FPR 1% (oracle) | Recall @ FPR 0.1% (oracle) | ECE |
|---|---|---|---|---|---|
| His recipe (11 raw features) | 0.793 [0.776, 0.809] | 0.481 [0.452, 0.522] | 0.341 [0.309, 0.394] | 0.158 [0.127, 0.239] | 0.231 [0.228, 0.235] |
| Logistic regression (raw 11) | 0.664 [0.649, 0.679] | 0.190 [0.176, 0.211] | 0.085 [0.069, 0.116] | 0.030 [0.019, 0.053] | 0.149 [0.142, 0.157] |
| Best single feature (raw 11) | 0.728 [0.715, 0.742] | 0.192 [0.178, 0.215] | 0.066 [0.054, 0.087] | 0.013 [0.009, 0.030] | n/a |
| M1 XGBoost on his 11 raw features (ablation) | 0.862 [0.849, 0.873] | 0.527 [0.497, 0.561] | 0.318 [0.286, 0.372] | 0.156 [0.141, 0.225] | 0.179 [0.176, 0.184] |
| Logistic regression (my features) | 0.850 [0.840, 0.860] | 0.363 [0.340, 0.390] | 0.165 [0.141, 0.188] | 0.095 [0.079, 0.117] | 0.079 [0.075, 0.084] |
| M1 XGBoost, my features | 0.881 [0.870, 0.891] | 0.588 [0.564, 0.620] | 0.358 [0.333, 0.400] | 0.261 [0.243, 0.299] | 0.207 [0.204, 0.212] |
| M2 feature-token attention net, my features | 0.784 [0.771, 0.798] | 0.391 [0.366, 0.420] | 0.246 [0.219, 0.269] | 0.158 [0.130, 0.187] | 0.143 [0.137, 0.150] |

### CHO R2->EHO (v2 -> HELD-OUT family): threshold transfer (thresholds fixed on validation of the training side)

| Model | FPR @ val-1% thr | Recall @ val-1% thr | FPR @ his rule | Recall @ his rule | F1 @ his rule | FPR on counts-only normals (val-1%) | (his rule) | per-group FPR @ val-1% [min..max] |
|---|---|---|---|---|---|---|---|---|
| His recipe (11 raw features) | 0.052 [0.046, 0.058] | 0.368 [0.344, 0.391] | 0.515 [0.502, 0.525] | 0.788 [0.769, 0.810] | 0.219 [0.212, 0.228] | 0.083 [0.054, 0.115] | 0.583 [0.524, 0.637] | 0.001 .. 0.064 |
| Logistic regression (raw 11) | 0.059 [0.054, 0.066] | 0.232 [0.211, 0.251] | 0.247 [0.239, 0.259] | 0.518 [0.496, 0.543] | 0.249 [0.236, 0.261] | 0.035 [0.015, 0.054] | 0.635 [0.592, 0.674] | 0.004 .. 0.071 |
| Best single feature (raw 11) | 0.044 [0.038, 0.049] | 0.165 [0.147, 0.182] | 0.378 [0.364, 0.390] | 0.757 [0.739, 0.776] | 0.258 [0.251, 0.267] | 0.048 [0.026, 0.075] | 0.660 [0.614, 0.707] | 0.003 .. 0.053 |
| M1 XGBoost on his 11 raw features (ablation) | 0.029 [0.025, 0.033] | 0.439 [0.413, 0.465] | 0.187 [0.179, 0.198] | 0.756 [0.733, 0.781] | 0.408 [0.393, 0.425] | 0.192 [0.158, 0.237] | 0.522 [0.471, 0.577] | 0.003 .. 0.035 |
| Logistic regression (my features) | 0.024 [0.020, 0.028] | 0.194 [0.175, 0.212] | 0.115 [0.109, 0.123] | 0.468 [0.446, 0.493] | 0.339 [0.322, 0.357] | 0.154 [0.123, 0.190] | 0.513 [0.465, 0.562] | 0.005 .. 0.028 |
| M1 XGBoost, my features | 0.022 [0.018, 0.025] | 0.415 [0.391, 0.441] | 0.177 [0.167, 0.186] | 0.740 [0.722, 0.763] | 0.423 [0.407, 0.440] | 0.061 [0.035, 0.094] | 0.587 [0.536, 0.637] | 0.011 .. 0.024 |
| M2 feature-token attention net, my features | 0.015 [0.013, 0.019] | 0.247 [0.229, 0.265] | 0.102 [0.095, 0.110] | 0.463 [0.444, 0.486] | 0.371 [0.352, 0.392] | 0.103 [0.071, 0.133] | 0.474 [0.418, 0.530] | 0.012 .. 0.016 |

### Cross-generator transfer: ROC-AUC / PR-AUC (prevalence 8.35%), [95% CI on ROC]

| Model | C2  H->EH | C3  R2->ER2 | CHO R2->EHO | C4a H->ER2 | C4b R2->EH | C5a R1->ER2 | C5b R2->ER1 |
|---|---|---|---|---|---|---|---|
| His recipe (11 raw features) | 0.976 / 0.932 | 0.860 / 0.610 | 0.793 / 0.481 | 0.772 / 0.346 | 0.884 / 0.663 | 0.837 / 0.566 | 0.833 / 0.549 |
| Logistic regression (raw 11) | 0.981 / 0.907 | 0.783 / 0.356 | 0.664 / 0.190 | 0.607 / 0.205 | 0.714 / 0.189 | 0.743 / 0.313 | 0.773 / 0.322 |
| Best single feature (raw 11) | 0.711 / 0.211 | 0.841 / 0.448 | 0.728 / 0.192 | 0.478 / 0.095 | 0.716 / 0.274 | 0.838 / 0.402 | 0.811 / 0.372 |
| M1 XGBoost on his 11 raw features (ablation) | 0.964 / 0.926 | 0.918 / 0.619 | 0.862 / 0.527 | 0.661 / 0.292 | 0.891 / 0.623 | 0.899 / 0.563 | 0.896 / 0.570 |
| Logistic regression (my features) | 0.979 / 0.920 | 0.910 / 0.594 | 0.850 / 0.363 | 0.669 / 0.221 | 0.921 / 0.674 | 0.902 / 0.516 | 0.901 / 0.533 |
| M1 XGBoost, my features | 0.964 / 0.896 | 0.925 / 0.672 | 0.881 / 0.588 | 0.617 / 0.255 | 0.828 / 0.488 | 0.895 / 0.549 | 0.907 / 0.619 |
| M2 feature-token attention net, my features | 0.979 / 0.884 | 0.886 / 0.548 | 0.784 / 0.391 | 0.618 / 0.219 | 0.763 / 0.378 | 0.884 / 0.496 | 0.877 / 0.511 |

### M4 one-class (trained on normals only, never sees attacks): evidence about inflation, NOT detection

| Model | his generator: ROC / PR / recall@1%FPR | rebuilt v2 (seen families) | held-out family |
|---|---|---|---|
| M4 Isolation Forest (raw 11, his baseline) | 0.835 / 0.567 / 0.472 | 0.732 / 0.225 / 0.114 | 0.685 / 0.186 / 0.063 |
| M4 Isolation Forest (my features) | 0.787 / 0.236 / 0.147 | 0.739 / 0.163 / 0.047 | 0.700 / 0.140 / 0.019 |
| M4 Autoencoder (my features) | 0.873 / 0.497 / 0.301 | 0.657 / 0.147 / 0.067 | 0.638 / 0.119 / 0.043 |

### Per-group spread (seed-mean per validation group), R2->ER2 and held-out family

| Cond | Model | group 1 | group 2 | spread (max-min) PR-AUC |
|---|---|---|---|---|
| C3 | His recipe (11 raw features) | ROC 0.827 PR 0.546 FPR 0.064 | ROC 0.976 PR 0.928 FPR 0.001 | 0.382 |
| C3 | Logistic regression (raw 11) | ROC 0.771 PR 0.332 FPR 0.071 | ROC 0.960 PR 0.775 FPR 0.004 | 0.443 |
| C3 | Best single feature (raw 11) | ROC 0.844 PR 0.460 FPR 0.053 | ROC 0.963 PR 0.689 FPR 0.003 | 0.229 |
| C3 | M1 XGBoost on his 11 raw features (ablation) | ROC 0.901 PR 0.557 FPR 0.035 | ROC 0.992 PR 0.939 FPR 0.003 | 0.382 |
| C3 | Logistic regression (my features) | ROC 0.898 PR 0.529 FPR 0.028 | ROC 0.991 PR 0.928 FPR 0.005 | 0.398 |
| C3 | M1 XGBoost, my features | ROC 0.903 PR 0.594 FPR 0.024 | ROC 0.994 PR 0.940 FPR 0.011 | 0.346 |
| C3 | M2 feature-token attention net, my features | ROC 0.855 PR 0.486 FPR 0.016 | ROC 0.989 PR 0.905 FPR 0.012 | 0.419 |
| CHO | His recipe (11 raw features) | ROC 0.760 PR 0.419 FPR 0.064 | ROC 0.971 PR 0.853 FPR 0.001 | 0.434 |
| CHO | Logistic regression (raw 11) | ROC 0.652 PR 0.180 FPR 0.071 | ROC 0.895 PR 0.506 FPR 0.004 | 0.326 |
| CHO | Best single feature (raw 11) | ROC 0.742 PR 0.200 FPR 0.053 | ROC 0.922 PR 0.393 FPR 0.003 | 0.193 |
| CHO | M1 XGBoost on his 11 raw features (ablation) | ROC 0.852 PR 0.482 FPR 0.035 | ROC 0.979 PR 0.842 FPR 0.003 | 0.360 |
| CHO | Logistic regression (my features) | ROC 0.835 PR 0.304 FPR 0.028 | ROC 0.970 PR 0.775 FPR 0.005 | 0.471 |
| CHO | M1 XGBoost, my features | ROC 0.868 PR 0.534 FPR 0.024 | ROC 0.980 PR 0.843 FPR 0.011 | 0.310 |
| CHO | M2 feature-token attention net, my features | ROC 0.727 PR 0.352 FPR 0.016 | ROC 0.959 PR 0.720 FPR 0.012 | 0.368 |

## HEADLINE: false-alarm rate on counts-only normals (uptime unknown), thresholds fixed on validation (1% FPR)

| Reading | Model (trained on rebuilt v2, held-out family excluded) | FPR counts-only normals | FPR other normals | overall FPR |
|---|---|---|---|---|
| A | His recipe (11 raw features) | 0.148 [0.121, 0.179] | 0.052 [0.050, 0.055] | 0.055 [0.052, 0.057] |
| A | Logistic regression (raw 11) | 0.075 [0.056, 0.098] | 0.028 [0.026, 0.030] | 0.029 [0.027, 0.031] |
| A | M1 XGBoost on his 11 raw features (ablation) | 0.098 [0.076, 0.125] | 0.047 [0.045, 0.050] | 0.049 [0.046, 0.051] |
| A | Logistic regression (my features) | 0.222 [0.190, 0.255] | 0.027 [0.025, 0.029] | 0.032 [0.030, 0.034] |
| A | M1 XGBoost, my features | 0.095 [0.072, 0.119] | 0.016 [0.015, 0.017] | 0.018 [0.017, 0.019] |
| A | M2 feature-token attention net, my features | 0.087 [0.068, 0.107] | 0.018 [0.017, 0.020] | 0.020 [0.018, 0.022] |
| B | His recipe (11 raw features) | 0.083 [0.054, 0.115] | 0.050 [0.044, 0.056] | 0.052 [0.046, 0.058] |
| B | Logistic regression (raw 11) | 0.035 [0.015, 0.054] | 0.061 [0.055, 0.068] | 0.059 [0.054, 0.066] |
| B | M1 XGBoost on his 11 raw features (ablation) | 0.192 [0.158, 0.237] | 0.019 [0.015, 0.023] | 0.029 [0.025, 0.033] |
| B | Logistic regression (my features) | 0.154 [0.123, 0.190] | 0.015 [0.012, 0.018] | 0.024 [0.020, 0.028] |
| B | M1 XGBoost, my features | 0.061 [0.035, 0.094] | 0.019 [0.015, 0.023] | 0.022 [0.018, 0.025] |
| B | M2 feature-token attention net, my features | 0.103 [0.071, 0.133] | 0.010 [0.007, 0.013] | 0.015 [0.013, 0.019] |

Counts-only normals per reading (summed over folds, one seed): {'A': 218, 'B': 104}. Small, so intervals are wide.

## Training details

M1 (my features): imbalance mechanism chosen by the tuning objective (count of fold-seed fits)

| Reading | Source | class_weight | focal |
|---|---|---|---|
| A | H | 7 | 2 |
| A | R1 | 5 | 4 |
| A | R2 | 7 | 2 |
| B | H | 5 | 1 |
| B | R1 | 5 | 1 |
| B | R2 | 5 | 1 |

M2 epochs run: median 37, min 19, max 80 (max allowed 80).