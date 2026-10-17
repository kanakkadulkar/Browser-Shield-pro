# Stage C re-run: generator v1 vs v2 (v2 fixes ONLY the counts-only uptime fallback)

Same code path, same frozen `configs/stage_c.yaml`, same seeds. All four attack families, as in Stage C.


## Reading A

| Condition | Model | F1 @ his rule v1 | F1 v2 | PR-AUC v1 | PR-AUC v2 | Recall @ val-1% FPR v1 | v2 | FPR @ his rule v1 | v2 |
|---|---|---|---|---|---|---|---|---|---|
| 3. honest, rebuilt (all 4 families) | His recipe, as coded (11) | 0.422 [0.416, 0.428] | 0.406 [0.400, 0.413] | 0.778 [0.766, 0.790] | 0.811 [0.801, 0.822] | 0.684 [0.674, 0.695] | 0.769 [0.759, 0.779] | 0.258 | 0.348 |
| 3. honest, rebuilt (all 4 families) | His recipe, as described (18) | 0.463 [0.455, 0.470] | 0.471 [0.464, 0.478] | 0.825 [0.815, 0.835] | 0.850 [0.840, 0.859] | 0.720 [0.710, 0.731] | 0.801 [0.793, 0.812] | 0.295 | 0.223 |
| 3. honest, rebuilt (all 4 families) | Logistic regression | 0.228 [0.226, 0.230] | 0.248 [0.245, 0.251] | 0.496 [0.483, 0.512] | 0.559 [0.544, 0.575] | 0.440 [0.429, 0.453] | 0.535 [0.522, 0.548] | 0.628 | 0.578 |
| 3. honest, rebuilt (all 4 families) | Best single feature | 0.264 [0.262, 0.266] | 0.264 [0.262, 0.267] | 0.390 [0.377, 0.403] | 0.449 [0.436, 0.463] | 0.335 [0.324, 0.348] | 0.392 [0.380, 0.405] | 0.504 | 0.504 |
| 4a. his gen -> rebuilt | His recipe, as coded (11) | 0.127 [0.117, 0.138] | 0.127 [0.117, 0.138] | 0.418 [0.406, 0.432] | 0.423 [0.411, 0.436] | 0.430 [0.418, 0.443] | 0.432 [0.420, 0.444] | 0.001 | 0.001 |
| 4a. his gen -> rebuilt | His recipe, as described (18) | 0.147 [0.136, 0.158] | 0.147 [0.136, 0.158] | 0.419 [0.406, 0.431] | 0.426 [0.412, 0.438] | 0.407 [0.395, 0.417] | 0.410 [0.398, 0.421] | 0.000 | 0.000 |
| 4a. his gen -> rebuilt | Logistic regression | 0.313 [0.304, 0.323] | 0.324 [0.314, 0.333] | 0.399 [0.387, 0.412] | 0.425 [0.413, 0.438] | 0.394 [0.382, 0.406] | 0.425 [0.412, 0.435] | 0.177 | 0.177 |
| 4a. his gen -> rebuilt | Best single feature | 0.151 [0.148, 0.154] | 0.151 [0.148, 0.154] | 0.148 [0.141, 0.156] | 0.148 [0.141, 0.156] | 0.237 [0.225, 0.248] | 0.237 [0.225, 0.248] | 0.776 | 0.776 |
| 4b. rebuilt -> his gen | His recipe, as coded (11) | 0.433 [0.427, 0.439] | 0.416 [0.410, 0.423] | 0.865 [0.856, 0.875] | 0.898 [0.891, 0.906] | 0.804 [0.795, 0.813] | 0.864 [0.856, 0.872] | 0.258 | 0.348 |
| 4b. rebuilt -> his gen | His recipe, as described (18) | 0.478 [0.471, 0.485] | 0.486 [0.480, 0.493] | 0.900 [0.893, 0.906] | 0.906 [0.900, 0.913] | 0.832 [0.823, 0.840] | 0.861 [0.852, 0.869] | 0.295 | 0.223 |
| 4b. rebuilt -> his gen | Logistic regression | 0.180 [0.177, 0.183] | 0.215 [0.212, 0.219] | 0.324 [0.311, 0.339] | 0.433 [0.419, 0.450] | 0.349 [0.337, 0.361] | 0.489 [0.476, 0.501] | 0.628 | 0.578 |
| 4b. rebuilt -> his gen | Best single feature | 0.259 [0.256, 0.261] | 0.259 [0.256, 0.261] | 0.553 [0.542, 0.565] | 0.553 [0.541, 0.565] | 0.452 [0.440, 0.463] | 0.452 [0.440, 0.463] | 0.504 | 0.504 |

**network_only sweep onset** (first s with recall >= 0.5 at the validation 1%-FPR threshold; effect-size columns for v1 are WRONG by construction, v2's are right)

| Model (rebuilt-trained) | v1 weakest s | v1 recall at strongest s / at weakest s | v2 weakest s | v2 recall at strongest s / at weakest s |
|---|---|---|---|---|
| His recipe, as coded (11) | never | 0.215 / 0.145 | 0.25 | 0.811 / 0.121 |
| Logistic regression | 1.50 | 0.934 / 0.119 | 0.50 | 0.998 / 0.066 |
| Best single feature | 1.50 | 0.569 / 0.025 | 0.50 | 0.996 / 0.025 |

**FPR on counts-only vs other normals** (his recipe family, rebuilt-trained, validation-1% threshold; pooled over folds and seeds)

| Model | v1: counts-only | v1: other | v2: counts-only | v2: other |
|---|---|---|---|---|
| His recipe, as coded (11) | 0.124 (81/654) | 0.013 | 0.118 (77/654) | 0.020 |
| His recipe, as described (18) | 0.099 (65/654) | 0.014 | 0.125 (82/654) | 0.020 |
| Logistic regression | 0.115 (75/654) | 0.029 | 0.070 (46/654) | 0.035 |
| Best single feature | 0.023 (15/654) | 0.042 | 0.023 (15/654) | 0.042 |

## Reading B

| Condition | Model | F1 @ his rule v1 | F1 v2 | PR-AUC v1 | PR-AUC v2 | Recall @ val-1% FPR v1 | v2 | FPR @ his rule v1 | v2 |
|---|---|---|---|---|---|---|---|---|---|
| 3. honest, rebuilt (all 4 families) | His recipe, as coded (11) | 0.256 [0.248, 0.264] | 0.284 [0.275, 0.294] | 0.618 [0.590, 0.649] | 0.665 [0.636, 0.696] | 0.582 [0.558, 0.608] | 0.662 [0.638, 0.690] | 0.457 | 0.384 |
| 3. honest, rebuilt (all 4 families) | His recipe, as described (18) | 0.231 [0.224, 0.238] | 0.358 [0.343, 0.372] | 0.633 [0.608, 0.661] | 0.673 [0.647, 0.702] | 0.646 [0.622, 0.674] | 0.672 [0.646, 0.697] | 0.495 | 0.311 |
| 3. honest, rebuilt (all 4 families) | Logistic regression | 0.254 [0.246, 0.263] | 0.267 [0.259, 0.276] | 0.285 [0.266, 0.311] | 0.359 [0.335, 0.389] | 0.387 [0.360, 0.414] | 0.454 [0.429, 0.484] | 0.408 | 0.396 |
| 3. honest, rebuilt (all 4 families) | Best single feature | 0.267 [0.261, 0.273] | 0.274 [0.267, 0.280] | 0.316 [0.293, 0.342] | 0.392 [0.368, 0.422] | 0.262 [0.238, 0.284] | 0.323 [0.298, 0.350] | 0.475 | 0.464 |
| 4a. his gen -> rebuilt | His recipe, as coded (11) | 0.240 [0.215, 0.262] | 0.249 [0.225, 0.272] | 0.346 [0.320, 0.379] | 0.354 [0.328, 0.387] | 0.399 [0.376, 0.423] | 0.415 [0.393, 0.440] | 0.262 | 0.262 |
| 4a. his gen -> rebuilt | His recipe, as described (18) | 0.225 [0.205, 0.245] | 0.230 [0.210, 0.250] | 0.306 [0.282, 0.333] | 0.311 [0.285, 0.338] | 0.436 [0.412, 0.459] | 0.438 [0.414, 0.462] | 0.119 | 0.119 |
| 4a. his gen -> rebuilt | Logistic regression | 0.186 [0.169, 0.203] | 0.189 [0.172, 0.207] | 0.206 [0.188, 0.229] | 0.209 [0.190, 0.232] | 0.272 [0.247, 0.296] | 0.274 [0.248, 0.297] | 0.184 | 0.184 |
| 4a. his gen -> rebuilt | Best single feature | 0.150 [0.146, 0.153] | 0.150 [0.146, 0.153] | 0.096 [0.089, 0.104] | 0.096 [0.089, 0.104] | 0.190 [0.168, 0.212] | 0.190 [0.168, 0.212] | 0.842 | 0.842 |
| 4b. rebuilt -> his gen | His recipe, as coded (11) | 0.271 [0.264, 0.278] | 0.291 [0.282, 0.300] | 0.778 [0.754, 0.801] | 0.765 [0.741, 0.788] | 0.749 [0.723, 0.774] | 0.746 [0.721, 0.768] | 0.457 | 0.384 |
| 4b. rebuilt -> his gen | His recipe, as described (18) | 0.235 [0.229, 0.242] | 0.275 [0.256, 0.289] | 0.676 [0.651, 0.701] | 0.613 [0.586, 0.640] | 0.732 [0.712, 0.754] | 0.581 [0.559, 0.607] | 0.495 | 0.311 |
| 4b. rebuilt -> his gen | Logistic regression | 0.200 [0.191, 0.210] | 0.254 [0.245, 0.262] | 0.126 [0.120, 0.136] | 0.221 [0.208, 0.241] | 0.168 [0.149, 0.185] | 0.315 [0.291, 0.338] | 0.408 | 0.396 |
| 4b. rebuilt -> his gen | Best single feature | 0.220 [0.212, 0.227] | 0.219 [0.211, 0.228] | 0.284 [0.261, 0.315] | 0.274 [0.250, 0.307] | 0.299 [0.276, 0.326] | 0.279 [0.254, 0.304] | 0.475 | 0.464 |

**network_only sweep onset** (first s with recall >= 0.5 at the validation 1%-FPR threshold; effect-size columns for v1 are WRONG by construction, v2's are right)

| Model (rebuilt-trained) | v1 weakest s | v1 recall at strongest s / at weakest s | v2 weakest s | v2 recall at strongest s / at weakest s |
|---|---|---|---|---|
| His recipe, as coded (11) | never | 0.212 / 0.067 | 0.50 | 0.987 / 0.061 |
| Logistic regression | never | 0.229 / 0.009 | 0.75 | 0.987 / 0.039 |
| Best single feature | never | 0.301 / 0.037 | 0.75 | 0.992 / 0.036 |

**FPR on counts-only vs other normals** (his recipe family, rebuilt-trained, validation-1% threshold; pooled over folds and seeds)

| Model | v1: counts-only | v1: other | v2: counts-only | v2: other |
|---|---|---|---|---|
| His recipe, as coded (11) | 0.054 (17/312) | 0.047 | 0.077 (24/312) | 0.033 |
| His recipe, as described (18) | 0.087 (27/312) | 0.127 | 0.093 (29/312) | 0.114 |
| Logistic regression | 0.013 (4/312) | 0.090 | 0.051 (16/312) | 0.077 |
| Best single feature | 0.045 (14/312) | 0.057 | 0.048 (15/312) | 0.044 |