
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
| 3. Honest protocol, rebuilt generator | His recipe, as coded (11 features) | 0.275 [0.270, 0.282] | 0.922 [0.916, 0.929] | 0.406 [0.400, 0.413] | 0.348 [0.343, 0.353] |
| 3. Honest protocol, rebuilt generator | His recipe, as described (18 features) | 0.336 [0.329, 0.344] | 0.917 [0.910, 0.924] | 0.471 [0.464, 0.478] | 0.223 [0.218, 0.228] |
| 3. Honest protocol, rebuilt generator | Logistic regression | 0.145 [0.143, 0.147] | 0.947 [0.941, 0.952] | 0.248 [0.245, 0.251] | 0.578 [0.573, 0.584] |
| 3. Honest protocol, rebuilt generator | Best single feature | 0.153 [0.151, 0.154] | 0.994 [0.992, 0.996] | 0.264 [0.262, 0.267] | 0.504 [0.498, 0.510] |
| 4a. Train his generator -> test rebuilt | His recipe, as coded (11 features) | 0.942 [0.918, 0.969] | 0.070 [0.065, 0.077] | 0.127 [0.117, 0.138] | 0.001 [0.000, 0.001] |
| 4a. Train his generator -> test rebuilt | His recipe, as described (18 features) | 0.959 [0.933, 0.983] | 0.082 [0.075, 0.089] | 0.147 [0.136, 0.158] | 0.000 [0.000, 0.001] |
| 4a. Train his generator -> test rebuilt | Logistic regression | 0.310 [0.298, 0.324] | 0.482 [0.472, 0.495] | 0.324 [0.314, 0.333] | 0.177 [0.173, 0.182] |
| 4a. Train his generator -> test rebuilt | Best single feature | 0.086 [0.084, 0.088] | 0.786 [0.780, 0.793] | 0.151 [0.148, 0.154] | 0.776 [0.773, 0.780] |
| 4b. Train rebuilt -> test his generator | His recipe, as coded (11 features) | 0.281 [0.275, 0.288] | 0.948 [0.942, 0.953] | 0.416 [0.410, 0.423] | 0.348 [0.343, 0.353] |
| 4b. Train rebuilt -> test his generator | His recipe, as described (18 features) | 0.345 [0.338, 0.352] | 0.951 [0.946, 0.956] | 0.486 [0.480, 0.493] | 0.223 [0.218, 0.228] |
| 4b. Train rebuilt -> test his generator | Logistic regression | 0.126 [0.124, 0.128] | 0.818 [0.809, 0.828] | 0.215 [0.212, 0.219] | 0.578 [0.573, 0.584] |
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
| 3. Honest protocol, rebuilt generator | His recipe, as coded (11 features) | 0.947 [0.943, 0.950] | 0.811 [0.801, 0.822] | 0.769 [0.759, 0.779] (0.023) | 0.078 [0.075, 0.081] (0.855) |
| 3. Honest protocol, rebuilt generator | His recipe, as described (18 features) | 0.964 [0.961, 0.967] | 0.850 [0.840, 0.859] | 0.801 [0.793, 0.812] (0.023) | 0.042 [0.040, 0.045] (0.838) |
| 3. Honest protocol, rebuilt generator | Logistic regression | 0.892 [0.886, 0.897] | 0.559 [0.544, 0.575] | 0.535 [0.522, 0.548] (0.036) | 0.327 [0.321, 0.333] (0.894) |
| 3. Honest protocol, rebuilt generator | Best single feature | 0.851 [0.846, 0.856] | 0.449 [0.436, 0.463] | 0.392 [0.380, 0.405] (0.041) | 0.421 [0.415, 0.427] (0.959) |
| 4a. Train his generator -> test rebuilt | His recipe, as coded (11 features) | 0.722 [0.714, 0.730] | 0.423 [0.411, 0.436] | 0.432 [0.420, 0.444] (0.063) | 0.000 [0.000, 0.000] (0.039) |
| 4a. Train his generator -> test rebuilt | His recipe, as described (18 features) | 0.710 [0.702, 0.719] | 0.426 [0.412, 0.438] | 0.410 [0.398, 0.421] (0.049) | 0.000 [0.000, 0.000] (0.053) |
| 4a. Train his generator -> test rebuilt | Logistic regression | 0.747 [0.740, 0.754] | 0.425 [0.413, 0.438] | 0.425 [0.412, 0.435] (0.046) | 0.036 [0.034, 0.038] (0.361) |
| 4a. Train his generator -> test rebuilt | Best single feature | 0.558 [0.551, 0.566] | 0.148 [0.141, 0.156] | 0.237 [0.225, 0.248] (0.196) | 0.385 [0.381, 0.388] (0.409) |
| 4b. Train rebuilt -> test his generator | His recipe, as coded (11 features) | 0.973 [0.971, 0.976] | 0.898 [0.891, 0.906] | 0.864 [0.856, 0.872] (0.023) | 0.078 [0.075, 0.081] (0.910) |
| 4b. Train rebuilt -> test his generator | His recipe, as described (18 features) | 0.968 [0.965, 0.972] | 0.906 [0.900, 0.913] | 0.861 [0.852, 0.869] (0.023) | 0.042 [0.040, 0.045] (0.901) |
| 4b. Train rebuilt -> test his generator | Logistic regression | 0.775 [0.767, 0.783] | 0.433 [0.419, 0.450] | 0.489 [0.476, 0.501] (0.036) | 0.327 [0.321, 0.333] (0.746) |
| 4b. Train rebuilt -> test his generator | Best single feature | 0.900 [0.896, 0.903] | 0.553 [0.541, 0.565] | 0.452 [0.440, 0.463] (0.041) | 0.421 [0.415, 0.427] (0.964) |

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
| 3. Honest protocol, rebuilt generator | His recipe, as coded (11 features) | 0.172 [0.166, 0.179] | 0.844 [0.823, 0.866] | 0.284 [0.275, 0.294] | 0.384 [0.371, 0.398] |
| 3. Honest protocol, rebuilt generator | His recipe, as described (18 features) | 0.262 [0.245, 0.279] | 0.802 [0.781, 0.824] | 0.358 [0.343, 0.372] | 0.311 [0.301, 0.324] |
| 3. Honest protocol, rebuilt generator | Logistic regression | 0.161 [0.156, 0.167] | 0.806 [0.784, 0.829] | 0.267 [0.259, 0.276] | 0.396 [0.383, 0.409] |
| 3. Honest protocol, rebuilt generator | Best single feature | 0.160 [0.155, 0.164] | 0.962 [0.952, 0.973] | 0.274 [0.267, 0.280] | 0.464 [0.452, 0.477] |
| 4a. Train his generator -> test rebuilt | His recipe, as coded (11 features) | 0.362 [0.313, 0.423] | 0.435 [0.413, 0.456] | 0.249 [0.225, 0.272] | 0.262 [0.253, 0.270] |
| 4a. Train his generator -> test rebuilt | His recipe, as described (18 features) | 0.358 [0.288, 0.444] | 0.347 [0.324, 0.370] | 0.230 [0.210, 0.250] | 0.119 [0.109, 0.127] |
| 4a. Train his generator -> test rebuilt | Logistic regression | 0.242 [0.201, 0.293] | 0.326 [0.302, 0.352] | 0.189 [0.172, 0.207] | 0.184 [0.174, 0.196] |
| 4a. Train his generator -> test rebuilt | Best single feature | 0.082 [0.080, 0.084] | 0.833 [0.813, 0.852] | 0.150 [0.146, 0.153] | 0.842 [0.833, 0.851] |
| 4b. Train rebuilt -> test his generator | His recipe, as coded (11 features) | 0.176 [0.170, 0.182] | 0.872 [0.852, 0.888] | 0.291 [0.282, 0.300] | 0.384 [0.371, 0.398] |
| 4b. Train rebuilt -> test his generator | His recipe, as described (18 features) | 0.204 [0.186, 0.221] | 0.663 [0.641, 0.686] | 0.275 [0.256, 0.289] | 0.311 [0.301, 0.324] |
| 4b. Train rebuilt -> test his generator | Logistic regression | 0.153 [0.147, 0.159] | 0.786 [0.767, 0.805] | 0.254 [0.245, 0.262] | 0.396 [0.383, 0.409] |
| 4b. Train rebuilt -> test his generator | Best single feature | 0.128 [0.124, 0.134] | 0.746 [0.723, 0.772] | 0.219 [0.211, 0.228] | 0.464 [0.452, 0.477] |

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
| 3. Honest protocol, rebuilt generator | His recipe, as coded (11 features) | 0.875 [0.862, 0.887] | 0.665 [0.636, 0.696] | 0.662 [0.638, 0.690] (0.035) | 0.208 [0.197, 0.220] (0.730) |
| 3. Honest protocol, rebuilt generator | His recipe, as described (18 features) | 0.881 [0.870, 0.893] | 0.673 [0.647, 0.702] | 0.672 [0.646, 0.697] (0.112) | 0.144 [0.135, 0.153] (0.702) |
| 3. Honest protocol, rebuilt generator | Logistic regression | 0.802 [0.788, 0.816] | 0.359 [0.335, 0.389] | 0.454 [0.429, 0.484] (0.076) | 0.185 [0.174, 0.196] (0.702) |
| 3. Honest protocol, rebuilt generator | Best single feature | 0.816 [0.802, 0.829] | 0.392 [0.368, 0.422] | 0.323 [0.298, 0.350] (0.044) | 0.398 [0.385, 0.412] (0.923) |
| 4a. Train his generator -> test rebuilt | His recipe, as coded (11 features) | 0.770 [0.755, 0.786] | 0.354 [0.328, 0.387] | 0.415 [0.393, 0.440] (0.098) | 0.100 [0.092, 0.107] (0.339) |
| 4a. Train his generator -> test rebuilt | His recipe, as described (18 features) | 0.710 [0.693, 0.727] | 0.311 [0.285, 0.338] | 0.438 [0.414, 0.462] (0.137) | 0.062 [0.055, 0.069] (0.272) |
| 4a. Train his generator -> test rebuilt | Logistic regression | 0.629 [0.610, 0.646] | 0.209 [0.190, 0.232] | 0.274 [0.248, 0.297] (0.107) | 0.074 [0.066, 0.081] (0.234) |
| 4a. Train his generator -> test rebuilt | Best single feature | 0.499 [0.480, 0.518] | 0.096 [0.089, 0.104] | 0.190 [0.168, 0.212] (0.214) | 0.680 [0.666, 0.692] (0.698) |
| 4b. Train rebuilt -> test his generator | His recipe, as coded (11 features) | 0.909 [0.896, 0.919] | 0.765 [0.741, 0.788] | 0.746 [0.721, 0.768] (0.035) | 0.208 [0.197, 0.220] (0.795) |
| 4b. Train rebuilt -> test his generator | His recipe, as described (18 features) | 0.823 [0.808, 0.837] | 0.613 [0.586, 0.640] | 0.581 [0.559, 0.607] (0.112) | 0.144 [0.135, 0.153] (0.589) |
| 4b. Train rebuilt -> test his generator | Logistic regression | 0.790 [0.778, 0.802] | 0.221 [0.208, 0.241] | 0.315 [0.291, 0.338] (0.076) | 0.185 [0.174, 0.196] (0.595) |
| 4b. Train rebuilt -> test his generator | Best single feature | 0.702 [0.686, 0.719] | 0.274 [0.250, 0.307] | 0.279 [0.254, 0.304] (0.044) | 0.398 [0.385, 0.412] (0.714) |

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
| C3 | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.634 | 0.850 | 0.080 | 0.811 | 0.702 (0.019) |
| C3 | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.321 | 0.996 | 0.514 | 0.934 | 0.692 (0.008) |
| C3 | His recipe, as coded (11 features) | unknow | 6617 | 1654 | 0.398 | 0.933 | 0.397 | 0.843 | 0.787 (0.024) |
| C3 | Logistic regression | 0f14de | 1395 | 349 | 0.280 | 0.920 | 0.429 | 0.510 | 0.383 (0.029) |
| C3 | Logistic regression | 2c0470 | 310 | 78 | 0.159 | 0.991 | 0.957 | 0.624 | 0.256 (0.003) |
| C3 | Logistic regression | unknow | 6617 | 1654 | 0.256 | 0.950 | 0.592 | 0.570 | 0.581 (0.039) |
| C3 | Best single feature | 0f14de | 1395 | 349 | 0.224 | 0.993 | 0.627 | 0.404 | 0.355 (0.048) |
| C3 | Best single feature | 2c0470 | 310 | 78 | 0.506 | 0.991 | 0.175 | 0.628 | 0.175 (0.003) |
| C3 | Best single feature | unknow | 6617 | 1654 | 0.269 | 0.995 | 0.493 | 0.466 | 0.410 (0.042) |
| C4a | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.300 | 0.201 | 0.004 | 0.449 | 0.488 (0.140) |
| C4a | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.058 | 0.030 | 0.000 | 0.448 | 0.038 (0.000) |
| C4a | His recipe, as coded (11 features) | unknow | 6617 | 1654 | 0.084 | 0.045 | 0.000 | 0.462 | 0.439 (0.049) |
| C4a | Logistic regression | 0f14de | 1395 | 349 | 0.265 | 0.679 | 0.397 | 0.277 | 0.508 (0.090) |
| C4a | Logistic regression | 2c0470 | 310 | 78 | 0.468 | 0.940 | 0.189 | 0.743 | 0.030 (0.000) |
| C4a | Logistic regression | unknow | 6617 | 1654 | 0.351 | 0.420 | 0.130 | 0.453 | 0.425 (0.039) |
| C4a | Best single feature | 0f14de | 1395 | 349 | 0.191 | 0.869 | 0.757 | 0.240 | 0.299 (0.138) |
| C4a | Best single feature | 2c0470 | 310 | 78 | 0.154 | 1.000 | 1.000 | 0.312 | 0.171 (0.000) |
| C4a | Best single feature | unknow | 6617 | 1654 | 0.142 | 0.759 | 0.769 | 0.125 | 0.227 (0.218) |
| C4b | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.636 | 0.859 | 0.080 | 0.824 | 0.734 (0.019) |
| C4b | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.315 | 0.983 | 0.514 | 0.857 | 0.573 (0.008) |
| C4b | His recipe, as coded (11 features) | unknow | 6617 | 1654 | 0.410 | 0.965 | 0.397 | 0.921 | 0.905 (0.024) |
| C4b | Logistic regression | 0f14de | 1395 | 349 | 0.271 | 0.889 | 0.429 | 0.679 | 0.605 (0.029) |
| C4b | Logistic regression | 2c0470 | 310 | 78 | 0.145 | 0.902 | 0.957 | 0.721 | 0.483 (0.003) |
| C4b | Logistic regression | unknow | 6617 | 1654 | 0.215 | 0.800 | 0.592 | 0.379 | 0.465 (0.039) |
| C4b | Best single feature | 0f14de | 1395 | 349 | 0.210 | 0.926 | 0.627 | 0.507 | 0.434 (0.048) |
| C4b | Best single feature | 2c0470 | 310 | 78 | 0.476 | 0.915 | 0.175 | 0.734 | 0.325 (0.003) |
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
| C3 | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.349 | 0.810 | 0.310 | 0.616 | 0.630 (0.043) |
| C3 | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.246 | 0.996 | 0.718 | 0.906 | 0.803 (0.002) |
| C3 | Logistic regression | 0f14de | 1395 | 349 | 0.308 | 0.769 | 0.357 | 0.352 | 0.488 (0.092) |
| C3 | Logistic regression | 2c0470 | 310 | 78 | 0.277 | 0.974 | 0.569 | 0.715 | 0.303 (0.003) |
| C3 | Best single feature | 0f14de | 1395 | 349 | 0.249 | 0.956 | 0.524 | 0.405 | 0.361 (0.053) |
| C3 | Best single feature | 2c0470 | 310 | 78 | 0.481 | 0.987 | 0.195 | 0.628 | 0.150 (0.003) |
| C4a | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.272 | 0.529 | 0.320 | 0.379 | 0.445 (0.120) |
| C4a | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.025 | 0.013 | 0.000 | 0.637 | 0.282 (0.001) |
| C4a | Logistic regression | 0f14de | 1395 | 349 | 0.145 | 0.224 | 0.111 | 0.139 | 0.223 (0.130) |
| C4a | Logistic regression | 2c0470 | 310 | 78 | 0.340 | 0.782 | 0.512 | 0.741 | 0.500 (0.002) |
| C4a | Best single feature | 0f14de | 1395 | 349 | 0.146 | 0.809 | 0.836 | 0.077 | 0.228 (0.261) |
| C4a | Best single feature | 2c0470 | 310 | 78 | 0.167 | 0.940 | 0.870 | 0.293 | 0.017 (0.000) |
| C4b | His recipe, as coded (11 features) | 0f14de | 1395 | 349 | 0.358 | 0.843 | 0.310 | 0.724 | 0.720 (0.043) |
| C4b | His recipe, as coded (11 features) | 2c0470 | 310 | 78 | 0.247 | 1.000 | 0.718 | 0.950 | 0.863 (0.002) |
| C4b | Logistic regression | 0f14de | 1395 | 349 | 0.279 | 0.773 | 0.357 | 0.200 | 0.309 (0.092) |
| C4b | Logistic regression | 2c0470 | 310 | 78 | 0.234 | 0.846 | 0.569 | 0.625 | 0.342 (0.003) |
| C4b | Best single feature | 0f14de | 1395 | 349 | 0.187 | 0.693 | 0.524 | 0.237 | 0.277 (0.053) |
| C4b | Best single feature | 2c0470 | 310 | 78 | 0.480 | 0.983 | 0.195 | 0.791 | 0.291 (0.003) |

### Best single feature chosen

- reading A, trained on H: dom_per_second x4, lag_per_second x3, event_loop_lag_ms x2
- reading A, trained on R: post_request_count x9
- reading B, trained on H: dom_per_second x3, lag_per_second x3
- reading B, trained on R: post_request_count x6

### Reading A: effect-size sweep, where each model stops working (recall@1%FPR >= 0.5)

| Model (train source) | Family | Weakest s working | d_lag there | pool req/min there | Recall at strongest s | Recall at weakest s (realised FPR) |
|---|---|---|---|---|---|---|
| His recipe, as coded (11 features) (H) | main_thread | 0.50 | 0.110 | 1.095 | 0.657 | 0.069 (0.063) |
| His recipe, as coded (11 features) (R) | main_thread | 0.00 | 0.020 | 0.200 | 0.994 | 0.017 (0.023) |
| Logistic regression (R) | main_thread | 0.75 | 0.256 | 2.564 | 1.000 | 0.023 (0.036) |
| Best single feature (R) | main_thread | 1.00 | 0.600 | 6.000 | 0.947 | 0.023 (0.041) |
| His recipe, as coded (11 features) (H) | network_only | never | never | never | 0.000 | 0.000 (0.063) |
| His recipe, as coded (11 features) (R) | network_only | 0.25 | 0.000 | 1.257 | 0.811 | 0.121 (0.023) |
| Logistic regression (R) | network_only | 0.50 | 0.000 | 3.162 | 0.998 | 0.066 (0.036) |
| Best single feature (R) | network_only | 0.50 | 0.000 | 3.162 | 0.996 | 0.025 (0.041) |
| His recipe, as coded (11 features) (H) | throttled | 0.75 | 0.064 | 1.282 | 0.650 | 0.069 (0.063) |
| His recipe, as coded (11 features) (R) | throttled | 0.25 | 0.012 | 0.234 | 0.995 | 0.016 (0.023) |
| Logistic regression (R) | throttled | 1.00 | 0.150 | 3.000 | 1.000 | 0.023 (0.036) |
| Best single feature (R) | throttled | 1.50 | 0.822 | 16.432 | 0.877 | 0.023 (0.041) |
| His recipe, as coded (11 features) (H) | worker_pool | never | never | never | 0.194 | 0.069 (0.063) |
| His recipe, as coded (11 features) (R) | worker_pool | 0.50 | 0.000 | 3.162 | 0.887 | 0.012 (0.023) |
| Logistic regression (R) | worker_pool | 0.75 | 0.000 | 7.953 | 0.988 | 0.023 (0.036) |
| Best single feature (R) | worker_pool | 0.75 | 0.000 | 7.953 | 0.994 | 0.023 (0.041) |

### Reading B: effect-size sweep, where each model stops working (recall@1%FPR >= 0.5)

| Model (train source) | Family | Weakest s working | d_lag there | pool req/min there | Recall at strongest s | Recall at weakest s (realised FPR) |
|---|---|---|---|---|---|---|
| His recipe, as coded (11 features) (H) | main_thread | 0.50 | 0.110 | 1.095 | 0.938 | 0.060 (0.098) |
| His recipe, as coded (11 features) (R) | main_thread | 0.00 | 0.020 | 0.200 | 1.000 | 0.025 (0.035) |
| Logistic regression (R) | main_thread | 0.50 | 0.110 | 1.095 | 0.989 | 0.049 (0.076) |
| Best single feature (R) | main_thread | 1.00 | 0.600 | 6.000 | 0.925 | 0.021 (0.044) |
| His recipe, as coded (11 features) (H) | network_only | never | never | never | 0.167 | 0.014 (0.098) |
| His recipe, as coded (11 features) (R) | network_only | 0.50 | 0.000 | 3.162 | 0.987 | 0.061 (0.035) |
| Logistic regression (R) | network_only | 0.75 | 0.000 | 7.953 | 0.987 | 0.039 (0.076) |
| Best single feature (R) | network_only | 0.75 | 0.000 | 7.953 | 0.992 | 0.036 (0.044) |
| His recipe, as coded (11 features) (H) | throttled | 0.75 | 0.064 | 1.282 | 0.934 | 0.058 (0.098) |
| His recipe, as coded (11 features) (R) | throttled | 0.25 | 0.012 | 0.234 | 0.998 | 0.022 (0.035) |
| Logistic regression (R) | throttled | 1.00 | 0.150 | 3.000 | 0.987 | 0.049 (0.076) |
| Best single feature (R) | throttled | 1.50 | 0.822 | 16.432 | 0.826 | 0.021 (0.044) |
| His recipe, as coded (11 features) (H) | worker_pool | never | never | never | 0.377 | 0.058 (0.098) |
| His recipe, as coded (11 features) (R) | worker_pool | 0.50 | 0.000 | 3.162 | 0.868 | 0.019 (0.035) |
| Logistic regression (R) | worker_pool | 0.75 | 0.000 | 7.953 | 0.967 | 0.049 (0.076) |
| Best single feature (R) | worker_pool | 0.75 | 0.000 | 7.953 | 0.989 | 0.021 (0.044) |

### His tiered generator under the Stage B adversarial check (dev only)

| Reading | All-feature AUC | Non-signal-only AUC | Best single feature | Rates share one uptime | Rows above real max (>=1 feature) |
|---|---|---|---|---|---|
| A | 1.000 | 0.998 | visibility_hidden 0.998 | 0.0016 (real 1.0) | 0.938 |
| B | 0.987 | 0.997 | visibility_hidden 0.995 | 0.0026 (real 1.0) | 0.9211 |