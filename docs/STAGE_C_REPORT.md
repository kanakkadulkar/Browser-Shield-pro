# Stage C report: his method under his protocol vs an honest protocol

**Everything labelled "his recipe" is a *reproduction of the described method*, not his checkpoint** (his pickles can't be loaded, his anomaly generator was never saved as a script). **All attack data here is "simulated miner signal, assumed effect sizes".** No real mining traffic was used.

Rules kept: config frozen before any result (`configs/stage_c.yaml`); **dev folds only, the locked test set was never loaded** (the code asserts it); the rebuilt generator was **not changed after seeing results** (one flaw found afterwards is disclosed in section 6). Seeds 42/43/44; 400-replicate bootstrap CIs. Full tables: `reports/stage_c/tables.md`. Code: `src/hisrecipe.py`, `src/stage_c.py`, `src/stage_c_report.py`. Tests: 29 pass.

## 1. What I found in his recipe before running it
1. **The "18 features" never reached his model.** In cell 28 the scaler and the train/val/test arrays are built from the 11-column frame *before* `engineer_features()` runs. Both saved Keras models (`models/`, `models1/`) have an input shape of **11**, and both scalers have `n_features_in_ = 11`, while the saved config lists 18 names. The deployed bundle is internally inconsistent. I therefore ran **both**: *as coded* (11) and *as described* (18).
2. **His headline evaluation does not use `synthetic_anomalies.csv`.** Section 2 regenerates the anomalies from percentile ranges ("his generator"), which is what produced F1 0.9967. So "his synthetic attacks" in this stage = that generator (what Stage B tested was the CSV rows).
3. **Pre-split leakage kept on purpose in condition 1:** clip cap (p99), noise and the scaler are fitted on *all* rows before the split, although his comment says "split first, then add noise".
4. **Code vs docs:** focal-loss FN weight is 3.0 in code (5.0 in the markdown). I used 3.0.
5. **His generator is trivially separable by artefacts** (Stage B check applied to it, dev only):

| | All-feature AUC | Non-signal channels only | Best single feature | Rates share one uptime (real = 100%) | Rows above real max |
|---|---|---|---|---|---|
| Reading A | 1.000 | 0.998 | `visibility_hidden` 0.998 | 0.16% | 93.8% |
| Reading B | 0.987 | 0.997 | `visibility_hidden` 0.995 | 0.26% | 92.1% |

His generator draws binary `visibility_hidden` from `p90 x 1.5 .. p99 x 3`, producing non-binary values. A single impossible column separates the classes.

## 2. Setup
- **Honest protocol:** dedupe first, leave-one-group-out dev folds (A: 3 folds, B: 2), scalers/caps/generator parameters fitted on the training side only, early stopping and **all thresholds from an inner validation set** (smallest remaining group >= 50 rows, else random 20%), his threshold rule (max F1 s.t. val recall >= 0.97) plus fixed operating points.
- **Evaluation sets:** attacks at 0.25 per normal, **reweighted to his prevalence (8.35%)** in precision, F1, FPR and PR-AUC.
- **Condition 1** is his setup applied to the *dev portion* of his data (9,888 normal rows, no dedupe, his generator, random 70/15/15). I deliberately did **not** run it on all his rows, which would train on locked-test rows.
- **Cross-generator transfer (4a, 4b):** the same fitted models (H = trained on his generator, R = trained on rebuilt) are scored on both evaluation sets.
- **Trivial baselines:** logistic regression (balanced) and the best single feature, same code path.
- **CI limits:** bootstrap resamples rows and averages seeds. It does **not** capture between-group variation, which is large (section 5).

## 3. Headline table: Reading A (primary), mean over 3 seeds, [95% bootstrap CI]

| Condition | Model | F1 at his rule | FPR at his rule | ROC-AUC | PR-AUC (8.35%) | Recall @ val-FPR<=1% (realised FPR) |
|---|---|---|---|---|---|---|
| **1. His protocol** | His recipe, 11 feat. | 0.991 [0.984, 0.998] | 0.001 | 1.000 | 0.999 | 0.998 (0.014) |
| | His recipe, 18 feat. | 0.990 [0.982, 0.996] | 0.000 | 1.000 | 1.000 | 1.000 (0.014) |
| | Logistic regression | 0.896 [0.876, 0.912] | 0.017 | 0.994 | 0.974 | 0.946 (0.012) |
| | Best single feature | 0.429 [0.416, 0.444] | 0.262 | 0.976 | 0.941 | 0.911 (0.011) |
| **2. Honest, his generator** | His recipe, 11 feat. | 0.971 [0.968, 0.975] | 0.001 | 0.999 | 0.997 | 0.998 (0.063) |
| | His recipe, 18 feat. | 0.972 [0.969, 0.975] | 0.000 | 0.998 | 0.995 | 0.996 (0.049) |
| | Logistic regression | 0.595 [0.588, 0.603] | 0.177 | 0.992 | 0.959 | 0.962 (0.046) |
| | Best single feature | 0.217 [0.215, 0.219] | 0.776 | 0.938 | 0.800 | 0.832 (0.196) |
| **3. Honest, rebuilt generator** | His recipe, 11 feat. | **0.422** [0.416, 0.428] | **0.258** | **0.949** | **0.778** [0.766, 0.790] | **0.684** (0.016) |
| | His recipe, 18 feat. | 0.463 [0.455, 0.470] | 0.295 | 0.957 | 0.825 | 0.720 (0.016) |
| | Logistic regression | 0.228 [0.226, 0.230] | 0.628 | 0.875 | 0.496 | 0.440 (0.031) |
| | Best single feature (`post_request_count`) | 0.264 [0.262, 0.266] | 0.504 | 0.825 | 0.390 | 0.335 (0.041) |
| **4a. Train his gen. -> test rebuilt** | His recipe, 11 feat. | 0.127 [0.117, 0.138] (recall **0.070**) | 0.001 | **0.715** | 0.418 | 0.430 (0.063) |
| | His recipe, 18 feat. | 0.147 (recall 0.082) | 0.000 | 0.695 | 0.419 | 0.407 (0.049) |
| | Logistic regression | 0.313 | 0.177 | 0.708 | 0.399 | 0.394 (0.046) |
| **4b. Train rebuilt -> test his gen.** | His recipe, 11 feat. | 0.433 | 0.258 | 0.969 | 0.865 | 0.804 (0.016) |
| | His recipe, 18 feat. | 0.478 | 0.295 | 0.962 | 0.900 | 0.832 (0.016) |
| | Logistic regression | 0.180 | 0.628 | 0.678 | 0.324 | 0.349 (0.031) |

For reference, his *reported* test F1 is 0.9967 and ROC-AUC 0.9999 (quoted from his report, not measured by me). My reproduction of his setup gets F1 0.991 [0.984, 0.998] on dev data, so his number is **inside my CI**.

## 4. How much do his numbers drop?
- **Condition 1 -> 2 (honest split, same generator): small.** F1 0.991 -> 0.971, PR-AUC 0.999 -> 0.997, recall@1%FPR 0.998 -> 0.998. **Group splits and dedupe alone barely hurt him**, because his attacks carry artefacts (section 1) that survive any split. The one visible cost: the validation-derived 1% FPR threshold realises 6.3% FPR on held-out groups.
- **Condition 2 -> 3 (same honest split, artefact-free attacks): large.** F1 0.971 -> 0.422, PR-AUC 0.997 -> 0.778, recall@1%FPR 0.998 -> 0.684 [0.674, 0.695], FPR at his threshold rule 0.001 -> **0.258**. ROC-AUC stays 0.949.
- **Condition 4a is the clearest evidence he learned artefacts:** trained on his generator, tested on rebuilt attacks, recall at his threshold is **7.0%** (ROC-AUC 0.715), and at the same threshold FPR stays 0.1%. The model is not flagging them at all.
- **Condition 4b:** the model trained on rebuilt attacks catches his generator's attacks well (ROC-AUC 0.969), so those are the "easier" ones. Transfer is asymmetric.
- **Caution on the size of the drop in 3:** it depends on **my assumed effect sizes** (including a weak tier, section 5). It shows his pipeline does not hold up against artefact-free attacks of mixed strength. It does **not** say how he would do on real miners.
- Against trivial baselines: his recipe beats logistic regression and a single feature in condition 3 (PR-AUC 0.778 vs 0.496 vs 0.390), so the neural + boosting model is not useless. Under his own generator (conditions 1, 2) the gaps shrink to near zero on AUC. A single feature already reaches 0.976 in condition 1.

## 5. Reading B and per-group spread
- **Reading B (2 folds; training sides of 310 to 1,400 normals) is much noisier and lower:** condition 2 F1 0.596, condition 3 F1 0.256, ROC-AUC 0.853, PR-AUC 0.618 [0.590, 0.649]. Same direction as A (his protocol F1 0.956; 4a ROC-AUC 0.754; 4b 0.920). B is a sensitivity check, not a second confirmation.
- **Between-group spread is large and the CIs above ignore it.** Reading A, his recipe (11), condition 3: F1 0.293 to 0.612, PR-AUC 0.799 to 0.826, FPR at his threshold 0.088 to 0.600, across the three groups. Condition 2 realised FPR at the validation-derived 1% threshold: 0.000, 0.049, **0.140**. Thresholds chosen on one group do not transfer.
- **Training length:** 58% of NN fits ran all 150 epochs, 42% stopped early (as in his notebook, which ran to 150).

## 6. Effect-size sweep: *simulated miner signal, assumed effect sizes*
Strength s scales each family's injected effect geometrically. The standard generator covers s in [0, 1] (shaded); **s < 0 is "low-and-slow"** (extrapolated below the weakest standard effect), s > 1 is stronger than anything trained on. Models are those from conditions 2 and 3, scored on fresh attacks from the held-out group. Operating point: threshold from validation normals at 1% FPR. Figures: `reports/stage_c/sweep_recall_A.png`, `sweep_prauc_A.png` (and `_B`). Full tables: `sweep_A.csv`, `sweep_onset_A.csv`.

**Where each stops working (Reading A; first s on the grid with recall >= 0.5 at the 1%-FPR threshold; realised FPR 1.6% to 6.3%):**

| Family (assumed effect at that s) | His recipe, trained on rebuilt | His recipe, trained on his generator | Logistic regression | Best single feature |
|---|---|---|---|---|
| main_thread (lag fraction added, extra req/min) | s=0 (0.02, 0.2) | s=0.5 (0.11, 1.1) | s=0.75 (0.26, 2.6) | s=1.0 (0.60, 6.0) |
| throttled | s=0.25 (0.012, 0.23) | s=0.75 (0.064, 1.3) | s=1.5 (0.82, 16) | s=1.5 |
| worker_pool (no lag; extra req/min) | s=0.5 (3.2) | **never** (recall 0.19 at s=1.5) | s=0.75 (8.0) | s=0.75 (8.0) |
| network_only | see caveat | **never** (recall 0.00) | s=1.5 | s=1.5 |

- **Detection collapses to chance between s = 0 and s = -1.** main_thread, his recipe (rebuilt-trained): recall 0.980 at s=1.0, 0.628 at s=0, 0.131 at s=-0.5 (lag +0.004, 0.04 req/min), 0.031 at s=-1.0, 0.011 at s=-2 (FPR is about 0.016). **A miner weaker than about a tenth of the weakest standard effect (below +0.002 lag fraction, 0.02 extra requests/minute) is indistinguishable from normal for every model here.** I expect that floor comes from the data (cumulative counters on a median 43-minute page) more than from the architecture, but I did not test that.
- **A model trained on his generator detects only lag-based miners, and only at higher strength** (recall 0.64 to 0.66 at the strongest settings). It misses pool-traffic-only miners (0.19 to 0.20) and counts-only ones (0.00).
- **Logistic regression and the single feature need a much stronger lag effect** than his recipe on main_thread miners (onset at +0.26 and +0.60 lag fraction vs +0.02, i.e. about 13x and 30x). On `worker_pool` they overtake him at the top (single feature 0.994 vs his 0.735 at s=1.5).
- **His recipe (rebuilt-trained) plateaus at about 0.73 for `worker_pool`** even with large pool traffic. My *hypothesis*, untested: young pages accumulate too few cumulative requests to show.
- **s > 1 is out of distribution**, and his recipe's recall *falls* there (main_thread 0.980 at s=1.0 to 0.941 at s=1.5; network_only 0.493 to 0.215). Treat s = 1.5 as extrapolation.
- Reading B shows the same ordering with wider uncertainty (see `sweep_onset_B.csv`).

### Two caveats on the sweep (both measured, neither fixed)
1. **Generator flaw, found after seeing results, not fixed per your rule:** the `network_only` family borrows an uptime from other rows in its batch to scale cumulative requests, but its base pool is *all* counts-only rows, so it silently falls back to a **constant 60 s**. Its effect is "about one minute of pool traffic": median added+base requests are 36 at s=1.0 and 153 at s=1.5 (real counts-only normals: median 14, p90 82). **Its "req/min" axis is therefore wrong, and `network_only` results (and the 10% of training attacks from it) understate that family.** I will fix this in a versioned v2 generator only if you ask, and re-run.
2. **`network_only` has a nonzero floor from the regime, not from detection.** Models trained on the rebuilt attacks false-alarm on **12.4%** of counts-only (uptime = 0) normals vs 1.3% of others (his recipe, Reading A, pooled over folds and seeds: 81/654 vs 321/24,291; logistic regression 11.5% vs 2.9%). That is why the `network_only` curves start at recall 0.145 and PR-AUC 0.53 at zero effect. A counts-only row is nearly 1000x off-scale in his "per second" features, and the model treats that as suspicious. That is a real false-positive failure mode of the recipe, and it shows up on real normal rows.

## 7. Test set (locked, untouched)
Fingerprint `aef6cae8bd4179c5` (checked by a test). **Class counts per test group** (no test attack data has been generated; counts below are what the final evaluation will use):

| Test group (by size rank in Reading A) | Real normals | Attacks at his prevalence (8.35%) | Attacks at the 0.25 evaluation ratio |
|---|---|---|---|
| rank 2 user | 644 | 59 | 161 |
| rank 4 user | 284 | 26 | 71 |

The same 928 normals are the test set under both readings.

## 8. Deviations from his recipe (and from the brief)
- **Torch instead of Keras.** BatchNorm momentum/epsilon, Glorot init, Adam epsilon and callback logic were matched by hand. Not bit-identical.
- **Class weights:** his Keras loss returns a scalar, so how Keras applied `class_weight` cannot be reproduced without TensorFlow. I applied per-sample "balanced" weights on top of the focal loss, as described.
- **Condition 1 uses dev data only** (9,888 normals), not all 10,973, to keep the locked test rows out.
- **"18 features"** run as a separate variant because his artefacts show the model used 11.
- **No dedupe in condition 1; dedupe everywhere else.** The deduped normal set is harder than raw collection (1,343 idle all-zero rows become one), so honest-protocol FPRs are for a harder-than-deployment normal class.
- **xgboost** needed an OpenMP runtime: I patched the venv-local library to use the one inside PyTorch's wheel (`scripts/fix_xgboost_macos.sh`); nothing outside `.venv` was touched.

## 9. What this does not show
- Nothing about real mining. Every attack is simulated with assumed effects; the rebuilt generator has a known flaw in one family.
- Conclusions about the *relative* ordering and about artefacts are firmer than the absolute numbers.
- Only three real validation groups (A) or two (B). CIs understate uncertainty.
- Stage C used dev folds only; the single final test evaluation is still to come.

## Files
`configs/stage_c.yaml` · `src/hisrecipe.py` · `src/baselines.py` · `src/metrics.py` · `src/stage_c.py` · `src/stage_c_report.py` · `tests/test_hisrecipe.py` · `scripts/fix_xgboost_macos.sh` · `reports/stage_c/` (`tables.md`, `main_results.json`, `per_fold_*.csv`, `sweep_*.csv|png`, `his_generator_artefacts.json`, `training_epochs.csv`, `raw/`)
