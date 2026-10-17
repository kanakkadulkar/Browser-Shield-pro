
### Reading A: at his threshold rule (max F1 s.t. val recall >= 0.97)

| Condition | Model | Precision | Recall | F1 | FPR |
|---|---|---|---|---|---|
| 1. His protocol (his data + generator, random split, no dedupe) | His recipe, as coded (11 features) | 0.993 [0.984, 1.000] | 0.990 [0.980, 0.998] | 0.991 [0.984, 0.998] | 0.001 [0.000, 0.002] |
| 1. His protocol (his data + generator, random split, no dedupe) | His recipe, as described (18 features) | 0.997 [0.992, 1.000] | 0.983 [0.968, 0.993] | 0.990 [0.982, 0.996] | 0.000 [0.000, 0.001] |
| 1. His protocol (his data + generator, random split, no dedupe) | Logistic regression | 0.836 [0.804, 0.864] | 0.965 [0.946, 0.980] | 0.896 [0.876, 0.912] | 0.017 [0.014, 0.022] |
| 1. His protocol (his data + generator, random split, no dedupe) | Best single feature | 0.283 [0.271, 0.296] | 0.963 [0.946, 0.978] | 0.429 [0.416, 0.444] | 0.262 [0.251, 0.273] |
| 2. Honest protocol, his generator | His recipe, as coded (11 features) | 0.992 [0.989, 0.996] | 0.951 [0.946, 0.957] | 0.971 [0.968, 0.975] | 0.001 [0.000, 0.001] |
| 2. Honest protocol, his generator | His recipe, as described (18 features) | 0.995 [0.992, 0.997] | 0.951 [0.946, 0.956] | 0.972 [0.969, 0.975] | 0.000 [0.000, 0.001] |
| 2. Honest protocol, his generator | Logistic regression | 0.472 [0.463, 0.481] | 0.963 [0.959, 0.967] | 0.595 [0.588, 0.603] | 0.177 [0.173, 0.182] |
| 2. Honest protocol, his generator | Best single feature | 0.125 [0.124, 0.127] | 0.984 [0.981, 0.986] | 0.217 [0.215, 0.219] | 0.776 [0.773, 0.780] |
| 3. Honest protocol, rebuilt generator | His recipe, as coded (11 features) | 0.282 [0.277, 0.288] | 0.925 [0.918, 0.932] | 0.422 [0.416, 0.428] | 0.258 [0.253, 0.264] |
| 3. Honest protocol, rebuilt generator | His recipe, as described (18 features) | 0.334 [0.326, 0.342] | 0.918 [0.912, 0.925] | 0.463 [0.455, 0.470] | 0.295 [0.290, 0.300] |
| 3. Honest protocol, rebuilt generator | Logistic regression | 0.131 [0.129, 0.132] | 0.952 [0.946, 0.958] | 0.228 [0.226, 0.230] | 0.628 [0.622, 0.633] |
| 3. Honest protocol, rebuilt generator | Best single feature | 0.152 [0.151, 0.154] | 0.992 [0.990, 0.994] | 0.264 [0.262, 0.266] | 0.504 [0.498, 0.510] |
| 4a. Train his generator -> test rebuilt | His recipe, as coded (11 features) | 0.942 [0.918, 0.969] | 0.070 [0.065, 0.077] | 0.127 [0.117, 0.138] | 0.001 [0.000, 0.001] |
| 4a. Train his generator -> test rebuilt | His recipe, as described (18 features) | 0.959 [0.933, 0.983] | 0.082 [0.075, 0.089] | 0.147 [0.136, 0.158] | 0.000 [0.000, 0.001] |
| 4a. Train his generator -> test rebuilt | Logistic regression | 0.303 [0.291, 0.316] | 0.461 [0.451, 0.474] | 0.313 [0.304, 0.323] | 0.177 [0.173, 0.182] |
| 4a. Train his generator -> test rebuilt | Best single feature | 0.086 [0.084, 0.088] | 0.786 [0.780, 0.793] | 0.151 [0.148, 0.154] | 0.776 [0.773, 0.780] |
| 4b. Train rebuilt -> test his generator | His recipe, as coded (11 features) | 0.289 [0.283, 0.295] | 0.950 [0.945, 0.955] | 0.433 [0.427, 0.439] | 0.258 [0.253, 0.264] |
| 4b. Train rebuilt -> test his generator | His recipe, as described (18 features) | 0.343 [0.336, 0.351] | 0.949 [0.944, 0.954] | 0.478 [0.471, 0.485] | 0.295 [0.290, 0.300] |
| 4b. Train rebuilt -> test his generator | Logistic regression | 0.103 [0.101, 0.105] | 0.750 [0.740, 0.761] | 0.180 [0.177, 0.183] | 0.628 [0.622, 0.633] |
| 4b. Train rebuilt -> test his generator | Best single feature | 0.149 [0.148, 0.151] | 0.969 [0.965, 0.973] | 0.259 [0.256, 0.261] | 0.504 [0.498, 0.510] |

### Reading A: threshold-free and fixed operating points

| Condition | Model | ROC-AUC | PR-AUC (prev 8.35%) | Recall @ FPR<=1% (realised FPR) | FPR @ recall~95% (realised recall) |
|---|---|---|---|---|---|
| 1. His protocol (his data + generator, random split, no dedupe) | His recipe, as coded (11 features) | 1.000 [0.999, 1.000] | 0.999 [0.996, 1.000] | 0.998 [0.993, 1.000] (0.014) | 0.000 [0.000, 0.000] (0.911) |
| 1. His protocol (his data + generator, random split, no dedupe) | His recipe, as described (18 features) | 1.000 [1.000, 1.000] | 1.000 [0.999, 1.000] | 1.000 [1.000, 1.000] (0.014) | 0.000 [0.000, 0.000] (0.931) |
| 1. His protocol (his data + generator, random split, no dedupe) | Logistic regression | 0.994 [0.990, 0.997] | 0.974 [0.962, 0.984] | 0.946 [0.923, 0.968] (0.012) | 0.008 [0.006, 0.011] (0.936) |
| 1. His protocol (his data + generator, random split, no dedupe) | Best single feature | 0.976 [0.966, 0.984] | 0.941 [0.921, 0.958] | 0.911 [0.884, 0.936] (0.011) | 0.165 [0.154, 0.175] (0.938) |
| 2. Honest protocol, his generator | His recipe, as coded (11 features) | 0.999 [0.999, 1.000] | 0.997 [0.996, 0.998] | 0.998 [0.997, 0.999] (0.063) | 0.000 [0.000, 0.000] (0.927) |
| 2. Honest protocol, his generator | His recipe, as described (18 features) | 0.998 [0.998, 0.999] | 0.995 [0.994, 0.996] | 0.996 [0.994, 0.997] (0.049) | 0.000 [0.000, 0.000] (0.923) |
| 2. Honest protocol, his generator | Logistic regression | 0.992 [0.991, 0.993] | 0.959 [0.956, 0.962] | 0.962 [0.957, 0.967] (0.046) | 0.036 [0.034, 0.038] (0.936) |
| 2. Honest protocol, his generator | Best single feature | 0.938 [0.933, 0.942] | 0.800 [0.789, 0.814] | 0.832 [0.824, 0.841] (0.196) | 0.385 [0.381, 0.388] (0.932) |
| 3. Honest protocol, rebuilt generator | His recipe, as coded (11 features) | 0.949 [0.946, 0.952] | 0.778 [0.766, 0.790] | 0.684 [0.674, 0.695] (0.016) | 0.091 [0.087, 0.095] (0.856) |
| 3. Honest protocol, rebuilt generator | His recipe, as described (18 features) | 0.957 [0.954, 0.961] | 0.825 [0.815, 0.835] | 0.720 [0.710, 0.731] (0.016) | 0.127 [0.123, 0.131] (0.856) |
| 3. Honest protocol, rebuilt generator | Logistic regression | 0.875 [0.870, 0.880] | 0.496 [0.483, 0.512] | 0.440 [0.429, 0.453] (0.031) | 0.385 [0.379, 0.391] (0.912) |
| 3. Honest protocol, rebuilt generator | Best single feature | 0.825 [0.820, 0.830] | 0.390 [0.377, 0.403] | 0.335 [0.324, 0.348] (0.041) | 0.455 [0.449, 0.461] (0.971) |
| 4a. Train his generator -> test rebuilt | His recipe, as coded (11 features) | 0.715 [0.707, 0.723] | 0.418 [0.406, 0.432] | 0.430 [0.418, 0.443] (0.063) | 0.000 [0.000, 0.000] (0.039) |
| 4a. Train his generator -> test rebuilt | His recipe, as described (18 features) | 0.695 [0.686, 0.703] | 0.419 [0.406, 0.431] | 0.407 [0.395, 0.417] (0.049) | 0.000 [0.000, 0.000] (0.053) |
| 4a. Train his generator -> test rebuilt | Logistic regression | 0.708 [0.702, 0.716] | 0.399 [0.387, 0.412] | 0.394 [0.382, 0.406] (0.046) | 0.036 [0.034, 0.038] (0.343) |
| 4a. Train his generator -> test rebuilt | Best single feature | 0.558 [0.551, 0.566] | 0.148 [0.141, 0.156] | 0.237 [0.225, 0.248] (0.196) | 0.385 [0.381, 0.388] (0.409) |
| 4b. Train rebuilt -> test his generator | His recipe, as coded (11 features) | 0.969 [0.967, 0.972] | 0.865 [0.856, 0.875] | 0.804 [0.795, 0.813] (0.016) | 0.091 [0.087, 0.095] (0.911) |
| 4b. Train rebuilt -> test his generator | His recipe, as described (18 features) | 0.962 [0.959, 0.966] | 0.900 [0.893, 0.906] | 0.832 [0.823, 0.840] (0.016) | 0.127 [0.123, 0.131] (0.915) |
| 4b. Train rebuilt -> test his generator | Logistic regression | 0.678 [0.669, 0.687] | 0.324 [0.311, 0.339] | 0.349 [0.337, 0.361] (0.031) | 0.385 [0.379, 0.391] (0.656) |
| 4b. Train rebuilt -> test his generator | Best single feature | 0.899 [0.896, 0.903] | 0.553 [0.542, 0.565] | 0.452 [0.440, 0.463] (0.041) | 0.455 [0.449, 0.461] (0.968) |

### Reading B: at his threshold rule (max F1 s.t. val recall >= 0.97)

| Condition | Model | Precision | Recall | F1 | FPR |
|---|---|---|---|---|---|
| 1. His protocol (his data + generator, random split, no dedupe) | His recipe, as coded (11 features) | 0.949 [0.912, 0.988] | 0.966 [0.931, 1.000] | 0.956 [0.926, 0.982] | 0.005 [0.001, 0.011] |
| 1. His protocol (his data + generator, random split, no dedupe) | His recipe, as described (18 features) | 0.969 [0.935, 1.000] | 0.966 [0.931, 1.000] | 0.966 [0.937, 0.989] | 0.003 [0.000, 0.007] |
| 1. His protocol (his data + generator, random split, no dedupe) | Logistic regression | 0.631 [0.588, 0.680] | 0.966 [0.931, 1.000] | 0.719 [0.681, 0.753] | 0.101 [0.084, 0.120] |
| 1. His protocol (his data + generator, random split, no dedupe) | Best single feature | 0.213 [0.197, 0.231] | 0.966 [0.920, 1.000] | 0.348 [0.325, 0.372] | 0.338 [0.307, 0.369] |
| 2. Honest protocol, his generator | His recipe, as coded (11 features) | 0.533 [0.514, 0.555] | 0.924 [0.910, 0.938] | 0.596 [0.582, 0.612] | 0.262 [0.253, 0.270] |
| 2. Honest protocol, his generator | His recipe, as described (18 features) | 0.551 [0.535, 0.568] | 0.902 [0.885, 0.916] | 0.619 [0.605, 0.635] | 0.119 [0.109, 0.127] |
| 2. Honest protocol, his generator | Logistic regression | 0.457 [0.438, 0.475] | 0.920 [0.905, 0.933] | 0.544 [0.530, 0.558] | 0.184 [0.174, 0.196] |
| 2. Honest protocol, his generator | Best single feature | 0.093 [0.091, 0.094] | 0.934 [0.920, 0.946] | 0.168 [0.165, 0.171] | 0.842 [0.833, 0.851] |
| 3. Honest protocol, rebuilt generator | His recipe, as coded (11 features) | 0.151 [0.146, 0.156] | 0.867 [0.850, 0.886] | 0.256 [0.248, 0.264] | 0.457 [0.444, 0.470] |
| 3. Honest protocol, rebuilt generator | His recipe, as described (18 features) | 0.134 [0.130, 0.138] | 0.839 [0.818, 0.859] | 0.231 [0.224, 0.238] | 0.495 [0.482, 0.510] |
| 3. Honest protocol, rebuilt generator | Logistic regression | 0.152 [0.146, 0.158] | 0.791 [0.769, 0.813] | 0.254 [0.246, 0.263] | 0.408 [0.396, 0.422] |
| 3. Honest protocol, rebuilt generator | Best single feature | 0.155 [0.151, 0.159] | 0.955 [0.945, 0.968] | 0.267 [0.261, 0.273] | 0.475 [0.463, 0.489] |
| 4a. Train his generator -> test rebuilt | His recipe, as coded (11 features) | 0.355 [0.306, 0.415] | 0.423 [0.401, 0.444] | 0.240 [0.215, 0.262] | 0.262 [0.253, 0.270] |
| 4a. Train his generator -> test rebuilt | His recipe, as described (18 features) | 0.354 [0.284, 0.439] | 0.338 [0.316, 0.361] | 0.225 [0.205, 0.245] | 0.119 [0.109, 0.127] |
| 4a. Train his generator -> test rebuilt | Logistic regression | 0.240 [0.199, 0.292] | 0.320 [0.296, 0.345] | 0.186 [0.169, 0.203] | 0.184 [0.174, 0.196] |
| 4a. Train his generator -> test rebuilt | Best single feature | 0.082 [0.080, 0.084] | 0.833 [0.813, 0.852] | 0.150 [0.146, 0.153] | 0.842 [0.833, 0.851] |
| 4b. Train rebuilt -> test his generator | His recipe, as coded (11 features) | 0.159 [0.155, 0.165] | 0.918 [0.902, 0.933] | 0.271 [0.264, 0.278] | 0.457 [0.444, 0.470] |
| 4b. Train rebuilt -> test his generator | His recipe, as described (18 features) | 0.137 [0.133, 0.141] | 0.851 [0.835, 0.870] | 0.235 [0.229, 0.242] | 0.495 [0.482, 0.510] |
| 4b. Train rebuilt -> test his generator | Logistic regression | 0.120 [0.115, 0.126] | 0.616 [0.592, 0.641] | 0.200 [0.191, 0.210] | 0.408 [0.396, 0.422] |
| 4b. Train rebuilt -> test his generator | Best single feature | 0.128 [0.124, 0.133] | 0.765 [0.741, 0.789] | 0.220 [0.212, 0.227] | 0.475 [0.463, 0.489] |

### Reading B: threshold-free and fixed operating points

| Condition | Model | ROC-AUC | PR-AUC (prev 8.35%) | Recall @ FPR<=1% (realised FPR) | FPR @ recall~95% (realised recall) |
|---|---|---|---|---|---|
| 1. His protocol (his data + generator, random split, no dedupe) | His recipe, as coded (11 features) | 0.999 [0.997, 1.000] | 0.992 [0.981, 1.000] | 0.977 [0.943, 1.000] (0.020) | 0.000 [0.000, 0.000] (0.920) |
| 1. His protocol (his data + generator, random split, no dedupe) | His recipe, as described (18 features) | 0.999 [0.995, 1.000] | 0.993 [0.978, 1.000] | 0.989 [0.965, 1.000] (0.014) | 0.000 [0.000, 0.000] (0.874) |
| 1. His protocol (his data + generator, random split, no dedupe) | Logistic regression | 0.995 [0.988, 1.000] | 0.979 [0.956, 0.998] | 0.954 [0.908, 1.000] (0.011) | 0.005 [0.001, 0.011] (0.943) |
| 1. His protocol (his data + generator, random split, no dedupe) | Best single feature | 0.986 [0.969, 0.999] | 0.962 [0.924, 0.993] | 0.943 [0.885, 0.989] (0.017) | 0.052 [0.038, 0.064] (0.920) |
| 2. Honest protocol, his generator | His recipe, as coded (11 features) | 0.976 [0.970, 0.981] | 0.932 [0.920, 0.943] | 0.928 [0.915, 0.942] (0.098) | 0.100 [0.092, 0.107] (0.907) |
| 2. Honest protocol, his generator | His recipe, as described (18 features) | 0.978 [0.973, 0.983] | 0.929 [0.919, 0.940] | 0.941 [0.928, 0.954] (0.137) | 0.062 [0.055, 0.069] (0.879) |
| 2. Honest protocol, his generator | Logistic regression | 0.981 [0.977, 0.984] | 0.907 [0.895, 0.920] | 0.923 [0.909, 0.938] (0.107) | 0.074 [0.066, 0.081] (0.895) |
| 2. Honest protocol, his generator | Best single feature | 0.711 [0.696, 0.726] | 0.211 [0.197, 0.226] | 0.411 [0.390, 0.431] (0.214) | 0.680 [0.666, 0.692] (0.888) |
| 3. Honest protocol, rebuilt generator | His recipe, as coded (11 features) | 0.853 [0.840, 0.866] | 0.618 [0.590, 0.649] | 0.582 [0.558, 0.608] (0.048) | 0.302 [0.291, 0.314] (0.754) |
| 3. Honest protocol, rebuilt generator | His recipe, as described (18 features) | 0.847 [0.834, 0.860] | 0.633 [0.608, 0.661] | 0.646 [0.622, 0.674] (0.125) | 0.285 [0.272, 0.297] (0.751) |
| 3. Honest protocol, rebuilt generator | Logistic regression | 0.773 [0.758, 0.786] | 0.285 [0.266, 0.311] | 0.387 [0.360, 0.414] (0.085) | 0.222 [0.210, 0.233] (0.685) |
| 3. Honest protocol, rebuilt generator | Best single feature | 0.793 [0.780, 0.805] | 0.316 [0.293, 0.342] | 0.262 [0.238, 0.284] (0.056) | 0.405 [0.393, 0.419] (0.904) |
| 4a. Train his generator -> test rebuilt | His recipe, as coded (11 features) | 0.754 [0.738, 0.769] | 0.346 [0.320, 0.379] | 0.399 [0.376, 0.423] (0.098) | 0.100 [0.092, 0.107] (0.322) |
| 4a. Train his generator -> test rebuilt | His recipe, as described (18 features) | 0.696 [0.680, 0.714] | 0.306 [0.282, 0.333] | 0.436 [0.412, 0.459] (0.137) | 0.062 [0.055, 0.069] (0.272) |
| 4a. Train his generator -> test rebuilt | Logistic regression | 0.616 [0.596, 0.633] | 0.206 [0.188, 0.229] | 0.272 [0.247, 0.296] (0.107) | 0.074 [0.066, 0.081] (0.232) |
| 4a. Train his generator -> test rebuilt | Best single feature | 0.499 [0.480, 0.518] | 0.096 [0.089, 0.104] | 0.190 [0.168, 0.212] (0.214) | 0.680 [0.666, 0.692] (0.698) |
| 4b. Train rebuilt -> test his generator | His recipe, as coded (11 features) | 0.920 [0.910, 0.929] | 0.778 [0.754, 0.801] | 0.749 [0.723, 0.774] (0.048) | 0.302 [0.291, 0.314] (0.862) |
| 4b. Train rebuilt -> test his generator | His recipe, as described (18 features) | 0.859 [0.846, 0.872] | 0.676 [0.651, 0.701] | 0.732 [0.712, 0.754] (0.125) | 0.285 [0.272, 0.297] (0.786) |
| 4b. Train rebuilt -> test his generator | Logistic regression | 0.637 [0.622, 0.654] | 0.126 [0.120, 0.136] | 0.168 [0.149, 0.185] (0.085) | 0.222 [0.210, 0.233] (0.419) |
| 4b. Train rebuilt -> test his generator | Best single feature | 0.711 [0.694, 0.727] | 0.284 [0.261, 0.315] | 0.299 [0.276, 0.326] (0.056) | 0.405 [0.393, 0.419] (0.737) |

### Reading A: per validation group (mean over seeds)

| Cond | Model | Group | Eval normals | Eval attacks | F1 | Recall | FPR | PR-AUC | Recall@1%FPR (realised FPR) |
|---|---|---|---|---|---|---|---|---|---|
| C2 | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.954 | 0.953 | 0.004 | 0.995 | 1.000 (0.140) |
| C2 | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.987 | 0.974 | 0.000 | 1.000 | 0.996 (0.000) |
| C2 | His recipe, as coded (11 features) | unknow | 6617 | 1654 | 0.974 | 0.950 | 0.000 | 0.998 | 0.998 (0.049) |
| C2 | Logistic regression | 0f14de | 1395 | 349 | 0.376 | 0.955 | 0.397 | 0.897 | 0.911 (0.090) |
| C2 | Logistic regression | 2c0470 | 310 | 78 | 0.482 | 0.974 | 0.189 | 0.949 | 0.799 (0.000) |
| C2 | Logistic regression | unknow | 6617 | 1654 | 0.711 | 0.964 | 0.130 | 0.975 | 0.980 (0.039) |
| C2 | Best single feature | 0f14de | 1395 | 349 | 0.233 | 0.989 | 0.757 | 0.684 | 0.841 (0.138) |
| C2 | Best single feature | 2c0470 | 310 | 78 | 0.154 | 1.000 | 1.000 | 0.863 | 0.299 (0.000) |
| C2 | Best single feature | unknow | 6617 | 1654 | 0.221 | 0.982 | 0.769 | 0.813 | 0.856 (0.218) |
| C3 | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.612 | 0.839 | 0.088 | 0.799 | 0.547 (0.005) |
| C3 | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.293 | 1.000 | 0.600 | 0.812 | 0.598 (0.017) |
| C3 | His recipe, as coded (11 features) | unknow | 6617 | 1654 | 0.424 | 0.940 | 0.278 | 0.826 | 0.717 (0.018) |
| C3 | Logistic regression | 0f14de | 1395 | 349 | 0.251 | 0.927 | 0.500 | 0.388 | 0.199 (0.019) |
| C3 | Logistic regression | 2c0470 | 310 | 78 | 0.156 | 0.996 | 0.982 | 0.501 | 0.137 (0.004) |
| C3 | Logistic regression | unknow | 6617 | 1654 | 0.233 | 0.955 | 0.638 | 0.520 | 0.506 (0.035) |
| C3 | Best single feature | 0f14de | 1395 | 349 | 0.224 | 0.993 | 0.627 | 0.346 | 0.295 (0.048) |
| C3 | Best single feature | 2c0470 | 310 | 78 | 0.497 | 0.970 | 0.176 | 0.579 | 0.145 (0.003) |
| C3 | Best single feature | unknow | 6617 | 1654 | 0.268 | 0.993 | 0.493 | 0.407 | 0.352 (0.042) |
| C4a | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.300 | 0.201 | 0.004 | 0.448 | 0.488 (0.140) |
| C4a | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.058 | 0.030 | 0.000 | 0.451 | 0.038 (0.000) |
| C4a | His recipe, as coded (11 features) | unknow | 6617 | 1654 | 0.084 | 0.045 | 0.000 | 0.455 | 0.437 (0.049) |
| C4a | Logistic regression | 0f14de | 1395 | 349 | 0.249 | 0.649 | 0.397 | 0.258 | 0.441 (0.090) |
| C4a | Logistic regression | 2c0470 | 310 | 78 | 0.457 | 0.910 | 0.189 | 0.702 | 0.030 (0.000) |
| C4a | Logistic regression | unknow | 6617 | 1654 | 0.343 | 0.401 | 0.130 | 0.426 | 0.402 (0.039) |
| C4a | Best single feature | 0f14de | 1395 | 349 | 0.191 | 0.869 | 0.757 | 0.240 | 0.299 (0.138) |
| C4a | Best single feature | 2c0470 | 310 | 78 | 0.154 | 1.000 | 1.000 | 0.312 | 0.171 (0.000) |
| C4a | Best single feature | unknow | 6617 | 1654 | 0.142 | 0.759 | 0.769 | 0.125 | 0.227 (0.218) |
| C4b | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.623 | 0.861 | 0.088 | 0.848 | 0.633 (0.005) |
| C4b | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.288 | 0.987 | 0.600 | 0.812 | 0.624 (0.017) |
| C4b | His recipe, as coded (11 features) | unknow | 6617 | 1654 | 0.437 | 0.967 | 0.278 | 0.886 | 0.848 (0.018) |
| C4b | Logistic regression | 0f14de | 1395 | 349 | 0.240 | 0.882 | 0.500 | 0.564 | 0.451 (0.019) |
| C4b | Logistic regression | 2c0470 | 310 | 78 | 0.143 | 0.906 | 0.982 | 0.656 | 0.359 (0.004) |
| C4b | Logistic regression | unknow | 6617 | 1654 | 0.173 | 0.715 | 0.638 | 0.267 | 0.327 (0.035) |
| C4b | Best single feature | 0f14de | 1395 | 349 | 0.210 | 0.926 | 0.627 | 0.507 | 0.434 (0.048) |
| C4b | Best single feature | 2c0470 | 310 | 78 | 0.475 | 0.915 | 0.176 | 0.734 | 0.325 (0.003) |
| C4b | Best single feature | unknow | 6617 | 1654 | 0.265 | 0.980 | 0.493 | 0.565 | 0.462 (0.042) |

### Reading B: per validation group (mean over seeds)

| Cond | Model | Group | Eval normals | Eval attacks | F1 | Recall | FPR | PR-AUC | Recall@1%FPR (realised FPR) |
|---|---|---|---|---|---|---|---|---|---|
| C2 | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.565 | 0.919 | 0.320 | 0.917 | 0.914 (0.120) |
| C2 | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.974 | 0.949 | 0.000 | 1.000 | 0.991 (0.001) |
| C2 | Logistic regression | 0f14de | 1395 | 349 | 0.631 | 0.905 | 0.111 | 0.895 | 0.919 (0.130) |
| C2 | Logistic regression | 2c0470 | 310 | 78 | 0.446 | 0.983 | 0.512 | 0.970 | 0.944 (0.002) |
| C2 | Best single feature | 0f14de | 1395 | 349 | 0.169 | 0.925 | 0.836 | 0.130 | 0.460 (0.261) |
| C2 | Best single feature | 2c0470 | 310 | 78 | 0.174 | 0.974 | 0.870 | 0.785 | 0.188 (0.000) |
| C3 | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.271 | 0.840 | 0.450 | 0.576 | 0.544 (0.057) |
| C3 | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.341 | 0.991 | 0.490 | 0.888 | 0.752 (0.005) |
| C3 | Logistic regression | 0f14de | 1395 | 349 | 0.271 | 0.755 | 0.389 | 0.278 | 0.413 (0.103) |
| C3 | Logistic regression | 2c0470 | 310 | 78 | 0.320 | 0.953 | 0.497 | 0.661 | 0.274 (0.003) |
| C3 | Best single feature | 0f14de | 1395 | 349 | 0.243 | 0.951 | 0.537 | 0.320 | 0.293 (0.068) |
| C3 | Best single feature | 2c0470 | 310 | 78 | 0.476 | 0.974 | 0.195 | 0.579 | 0.120 (0.003) |
| C4a | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.262 | 0.514 | 0.320 | 0.371 | 0.425 (0.120) |
| C4a | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.025 | 0.013 | 0.000 | 0.634 | 0.282 (0.001) |
| C4a | Logistic regression | 0f14de | 1395 | 349 | 0.145 | 0.223 | 0.111 | 0.137 | 0.223 (0.130) |
| C4a | Logistic regression | 2c0470 | 310 | 78 | 0.335 | 0.752 | 0.512 | 0.728 | 0.491 (0.002) |
| C4a | Best single feature | 0f14de | 1395 | 349 | 0.146 | 0.809 | 0.836 | 0.077 | 0.228 (0.261) |
| C4a | Best single feature | 2c0470 | 310 | 78 | 0.167 | 0.940 | 0.870 | 0.293 | 0.017 (0.000) |
| C4b | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.294 | 0.900 | 0.450 | 0.750 | 0.724 (0.057) |
| C4b | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.344 | 1.000 | 0.490 | 0.935 | 0.863 (0.005) |
| C4b | Logistic regression | 0f14de | 1395 | 349 | 0.203 | 0.580 | 0.389 | 0.118 | 0.142 (0.103) |
| C4b | Logistic regression | 2c0470 | 310 | 78 | 0.254 | 0.778 | 0.497 | 0.536 | 0.286 (0.003) |
| C4b | Best single feature | 0f14de | 1395 | 349 | 0.189 | 0.716 | 0.537 | 0.253 | 0.301 (0.068) |
| C4b | Best single feature | 2c0470 | 310 | 78 | 0.480 | 0.983 | 0.195 | 0.791 | 0.291 (0.003) |

### Best single feature chosen

- reading A, trained on H: dom_per_second x4, lag_per_second x3, event_loop_lag_ms x2
- reading A, trained on R: post_request_count x9
- reading B, trained on H: dom_per_second x3, lag_per_second x3
- reading B, trained on R: post_request_count x5, network_request_count x1

### Reading A: effect-size sweep, where each model stops working (recall@1%FPR >= 0.5)

| Model (train source) | Family | Weakest s working | d_lag there | pool req/min there | Recall at strongest s | Recall at weakest s (realised FPR) |
|---|---|---|---|---|---|---|
| His recipe, as coded (11 features) (H) | main_thread | 0.50 | 0.110 | 1.095 | 0.657 | 0.069 (0.063) |
| His recipe, as coded (11 features) (R) | main_thread | 0.00 | 0.020 | 0.200 | 0.941 | 0.011 (0.016) |
| Logistic regression (R) | main_thread | 0.75 | 0.256 | 2.564 | 1.000 | 0.014 (0.031) |
| Best single feature (R) | main_thread | 1.00 | 0.600 | 6.000 | 0.947 | 0.023 (0.041) |
| His recipe, as coded (11 features) (H) | network_only | never | never | never | 0.000 | 0.000 (0.063) |
| His recipe, as coded (11 features) (R) | network_only | never | never | never | 0.215 | 0.145 (0.016) |
| Logistic regression (R) | network_only | 1.50 | 0.000 | 126.491 | 0.934 | 0.119 (0.031) |
| Best single feature (R) | network_only | 1.50 | 0.000 | 126.491 | 0.569 | 0.025 (0.041) |
| His recipe, as coded (11 features) (H) | throttled | 0.75 | 0.064 | 1.282 | 0.650 | 0.069 (0.063) |
| His recipe, as coded (11 features) (R) | throttled | 0.25 | 0.012 | 0.234 | 0.960 | 0.010 (0.016) |
| Logistic regression (R) | throttled | 1.50 | 0.822 | 16.432 | 0.999 | 0.014 (0.031) |
| Best single feature (R) | throttled | 1.50 | 0.822 | 16.432 | 0.877 | 0.023 (0.041) |
| His recipe, as coded (11 features) (H) | worker_pool | never | never | never | 0.194 | 0.069 (0.063) |
| His recipe, as coded (11 features) (R) | worker_pool | 0.50 | 0.000 | 3.162 | 0.735 | 0.008 (0.016) |
| Logistic regression (R) | worker_pool | 0.75 | 0.000 | 7.953 | 0.976 | 0.014 (0.031) |
| Best single feature (R) | worker_pool | 0.75 | 0.000 | 7.953 | 0.994 | 0.023 (0.041) |

### Reading B: effect-size sweep, where each model stops working (recall@1%FPR >= 0.5)

| Model (train source) | Family | Weakest s working | d_lag there | pool req/min there | Recall at strongest s | Recall at weakest s (realised FPR) |
|---|---|---|---|---|---|---|
| His recipe, as coded (11 features) (H) | main_thread | 0.50 | 0.110 | 1.095 | 0.938 | 0.060 (0.098) |
| His recipe, as coded (11 features) (R) | main_thread | 0.00 | 0.020 | 0.200 | 1.000 | 0.031 (0.048) |
| Logistic regression (R) | main_thread | 0.50 | 0.110 | 1.095 | 0.988 | 0.049 (0.085) |
| Best single feature (R) | main_thread | 1.00 | 0.600 | 6.000 | 0.921 | 0.024 (0.056) |
| His recipe, as coded (11 features) (H) | network_only | never | never | never | 0.132 | 0.014 (0.098) |
| His recipe, as coded (11 features) (R) | network_only | never | never | never | 0.212 | 0.067 (0.048) |
| Logistic regression (R) | network_only | never | never | never | 0.229 | 0.009 (0.085) |
| Best single feature (R) | network_only | never | never | never | 0.301 | 0.037 (0.056) |
| His recipe, as coded (11 features) (H) | throttled | 0.75 | 0.064 | 1.282 | 0.934 | 0.058 (0.098) |
| His recipe, as coded (11 features) (R) | throttled | 0.25 | 0.012 | 0.234 | 0.998 | 0.028 (0.048) |
| Logistic regression (R) | throttled | 1.00 | 0.150 | 3.000 | 0.987 | 0.049 (0.085) |
| Best single feature (R) | throttled | 1.50 | 0.822 | 16.432 | 0.818 | 0.024 (0.056) |
| His recipe, as coded (11 features) (H) | worker_pool | never | never | never | 0.377 | 0.058 (0.098) |
| His recipe, as coded (11 features) (R) | worker_pool | 0.50 | 0.000 | 3.162 | 0.728 | 0.027 (0.048) |
| Logistic regression (R) | worker_pool | 0.75 | 0.000 | 7.953 | 0.958 | 0.049 (0.085) |
| Best single feature (R) | worker_pool | 0.75 | 0.000 | 7.953 | 0.988 | 0.024 (0.056) |

### His tiered generator under the Stage B adversarial check (dev only)

| Reading | All-feature AUC | Non-signal-only AUC | Best single feature | Rates share one uptime | Rows above real max (>=1 feature) |
|---|---|---|---|---|---|
| A | 1.000 | 0.998 | visibility_hidden 0.998 | 0.0016 (real 1.0) | 0.938 |
| B | 0.987 | 0.997 | visibility_hidden 0.995 | 0.0026 (real 1.0) | 0.9211 |