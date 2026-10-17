# Phase 1 Analysis: "BE Project - BrowserShield" (CryptoShield)

Source analysed (read-only): `Research Papers/BE Project - BrowserShield/`
Everything below was read from the files or measured directly from the CSVs with the Python standard library. Nothing was run from the notebooks; their stored outputs are quoted as "reported".

## 0. Findings that change the brief

| Brief assumed | What the folder actually contains |
|---|---|
| Folder named `BE PROJECT Browsershield` | Real path is `Research Papers/BE Project - BrowserShield/`. The project calls itself **CryptoShield**. |
| A browser extension, possibly URL/phishing based | **Behavioural cryptojacking / resource-abuse detection** from per-tab runtime telemetry. There are **no URLs, HTML or content features used by the model.** |
| Extension source in the folder | **No extension source is present** (no `manifest.json`, no JS or HTML). It exists only as report text and screenshots. |
| Labelled dataset | Real telemetry is **unlabelled**. "Attack" rows are **synthetic**. The label is "synthetic vs real". |

The Phase 2 URL-model ideas (char-CNN, DistilBERT on URLs) do not apply to this data. See section 7.

## 1. Threat and core technique

- **Threat:** cryptojacking and hidden resource abuse by web pages (covert mining, background computation, bot-like traffic, data exfiltration).
- **Technique:** a Chrome extension samples per-tab behavioural telemetry. It sends the telemetry to a backend, which turns it into features and scores it with an ML model. High score means "anomalous session".
- **Original framing (report):** Isolation Forest trained only on normal browsing, so no attack labels needed. **Final implementation:** a supervised Attention-MLP + XGBoost ensemble trained on real-normal vs synthetic-attack rows. The unsupervised framing was dropped, but the report still describes it.

## 2. Dataset

All files are in the project root, as CSVs.

| File | Rows x cols | What it is |
|---|---|---|
| `telemetry_features.csv` | 3,098 x 22 | Raw collected telemetry. Has `user_id`, `timestamp`, `domain` and 19 numeric columns. |
| `telemetry_ml_final.csv` | 3,098 x 11 | The 11 model features derived from the raw file. |
| `telemetry_ml_final1.csv` | 10,973 x 11 | A larger "normal" set. **Provenance not documented.** It is 3.5x the raw file and nothing in the folder says how it was produced. |
| `synthetic_anomalies.csv` | 1,000 x 11 | Synthetic "attack" rows. **The generator script is not in the folder.** |
| `telemetry_ml_final_full.csv` | 11,973 x 11 | Concatenation of `final1` and `synthetic` (unlabelled). |

**Labels (from the notebook):** `synthetic_anomalies.csv` gets `isAnomaly=1`, `telemetry_ml_final1.csv` gets `isAnomaly=0`. Class balance is 1,000 vs 10,973, so **8.35% positive**.

**Raw telemetry provenance (measured):** 6 `user_id`s, 78 distinct domains, a 4.8-day span. Rows per user are 1,502 / 855 / 394 / 333 / 8 / 6, so **two users make up 76% of the data**. Top domains are YouTube, ChatGPT, WhatsApp Web, Google Docs and Meet. 74% of raw rows have `active=0`.

**Measured quality issues:**
- **12.2% of the "normal" rows are all zeros** (1,343 of 10,973). Those are idle or background tabs.
- **15.7% of the "normal" rows are exact duplicates** (1,718 of 10,973). Synthetic rows have 0 duplicates. In the raw file, 81 rows have duplicated feature vectors.
- **Heavy-tailed, uncapped values.** `event_loop_lag_ms` has a maximum of 74,280,502 ms (about 20 hours) in the normal class. That is a collection artefact, not behaviour.
- **No missing values** in any CSV, but zeros appear to stand in for "not measured" (for example `cpu_hint`, `worker_count`).
- **Synthetic rows look nothing like real ones.** Medians: `event_loop_lag_ms` is 458,640 (synthetic) vs 8 (real). `dom_mutation_count` is 2.08M vs 4.7k. `network_per_second` is 36.6 vs 0.0.
- **Single-feature ROC-AUC, synthetic vs real (measured):** `network_per_second` 0.973, `lag_per_second` 0.932, `dom_per_second` 0.919, `network_request_count` 0.879, `event_loop_lag_ms` 0.859. The classes are largely separable on one feature, so the task is easy by construction.
- **Privacy:** the raw file pairs `user_id` with the domains visited. That is effectively browsing history of real people. Treat it as sensitive.

**Licence:** no LICENSE, README or dataset-source file anywhere in the folder. **Unclear. Flagged.** The data appears to be collected by the author with their own extension, so I need you to confirm that (a) the friend owns it, (b) the participants consented, and (c) you have their permission to reuse it.

## 3. Preprocessing and features

**Model inputs (11):** `idle_ratio`, `lag_per_second`, `dom_per_second`, `network_per_second`, `event_loop_lag_ms`, `dom_mutation_count`, `network_request_count`, `post_request_count`, `unique_domains_contacted`, `visibility_hidden`, `visibility_changes`.

- **Rate features** are derived from raw columns, for example `dom_per_second = dom_mutation_count / page_uptime`.
- **Baseline notebook:** RobustScaler, StandardScaler and MinMaxScaler are all fitted on the **whole dataset before the split**. This is a minor leak, since scaling statistics see test rows.
- **Final notebook (section 2.2):** the normal data is clipped at its own 99th percentile, then **the 1,000 anomalies are regenerated in three tiers**: A "clear" at 40%, B "moderate" at 40%, C "borderline" at 20%. Each tier is sampled from uniform ranges set by percentiles of the normal data. Seven features are added (`lag_per_dom`, `network_per_dom`, `post_per_network`, `cpu_stress_score`, `stealth_score`, `loop_pressure`, `domain_concentration`), for 18 in total. The split is 70/15/15 stratified: 8,381 train, 1,796 val, 1,796 test.
- **So the evaluated "attacks" are not the CSV's synthetic rows.** They are fresh draws from hand-picked ranges inside the notebook, and the generator is not saved as a standalone script.
- The notebook's own overlap check printed "overlap≈0.0" for `event_loop_lag_ms` and `lag_per_second` for tier C (anomaly 64k to 200k ms vs normal 0 to 60.6k). The "borderline" tier is therefore **not actually borderline** on the most important feature.

## 4. Model

- **Final model:** Attention-MLP (Keras/TensorFlow 2.19) plus XGBoost, blended 50/50 on probabilities.
  - MLP: Dense 64 + BN + ReLU + Dropout 0.5, a residual block, a sigmoid attention gate (64-wide, over hidden units, not input features), then Dense 32 and 16, sigmoid output. L2 = 1e-3.
  - Loss: asymmetric focal loss (gamma 2.0, alpha 0.85, FN weight 3.0 in the code; the markdown says 5.0, so the **docs and code disagree**).
  - Training: Adam 3e-4, batch 64, up to 150 epochs, ReduceLROnPlateau, EarlyStopping (patience 20) on val loss. Class weights are also applied on top of the focal loss, which double-counts the imbalance. The log shows training ran all 150 epochs with the best epoch being the last one.
  - XGBoost: 300 trees, lr 0.05, depth 5, `scale_pos_weight` about 11.
  - Decision threshold 0.4666, chosen on validation as max F1 subject to recall >= 0.97.
- **Baselines:** Random Forest, XGBoost, SVM (RBF), Logistic Regression, Isolation Forest (contamination 0.084, which is simply the known positive rate).
- **Seeds:** 42 set globally, but the anomaly generation uses the NumPy global RNG with no per-call seed.
- **Saved artefacts:** `models/` and `models1/` hold a `.keras` model, weights, XGBoost pickle, scaler and config pickles. The XGBoost pickles are byte-identical, and the two `model_config.pkl` files differ, so **I cannot tell which is the one in use**.
- **Explainability:** SHAP and LIME cells exist, but only the plots are stored. Permutation importance is computed. Attention-gate weights are not tied to named features.

## 5. Reported metrics and whether they are sound

**Reported (final notebook, test set of 1,796 with 150 positives):**

| Model | Acc | Prec | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Attention-MLP + XGB | 0.9994 | 1.0000 | 0.9933 | 0.9967 | 0.9999 |
| XGBoost | 0.9989 | 1.0000 | 0.9867 | 0.9933 | 1.0000 |
| Random Forest | 0.9983 | 1.0000 | 0.9800 | 0.9899 | 1.0000 |
| SVM (RBF) | 0.9967 | 1.0000 | 0.9600 | 0.9796 | 0.9996 |
| Logistic Regression | 0.9933 | 0.9929 | 0.9267 | 0.9586 | 0.9975 |

The earlier baseline notebook reported Random Forest and XGBoost at **exactly 1.000** on all metrics, with Isolation Forest F1 of 0.9975.

**Verdict: the evaluation does not support the headline claims.**
1. **The label is the data source.** A positive row means "synthetic", not "attack". The model learns to tell a simulator from real browsing, which is not evidence it detects real cryptojacking.
2. **No real attack data anywhere.** Nothing was measured against actual mining scripts. The report itself says "controlled mining scripts" are a plan.
3. **Circular generation.** In the final notebook the anomalies are built from percentiles of the same normal data and are then "detected" by a model fitted on them. Test anomalies come from the same generator as train anomalies.
4. **Random row-level split.** Rows from the same user, domain and session land in train and test. Duplicates are not removed (15.7% of normal rows), so exact copies can appear on both sides. No split by user or domain.
5. **Test set reused for choices.** Threshold sensitivity tables and the final comparison are computed on test, and several cells were re-run repeatedly. It is not a single-shot test.
6. **Perfect scores are a warning sign** (1.000 across the board). With the single-feature AUCs measured above, that is expected, not impressive.
7. **Very few real sessions.** 6 users over under 5 days, dominated by 2 users, and in practice no evidence of generalisation to other users, sites, or machines.
8. **No false-positive rate on real data.** On the real normal class, 0 FP of 1,646 in the test set sounds good, but the normal class is the same 6 users and about 15% duplicated rows.
9. **No latency, no cross-validation, no calibration, no confidence intervals.**

The numbers are probably reproducible. What is unsound is what they claim to mean.

## 6. Extension internals

**Not recoverable from this folder.** What the report and diagrams say:
- A Chrome extension (Chromium, standard APIs) with content scripts collecting per-tab telemetry at fixed intervals (sampling at most every 1 s), with a `userConsent` flag.
- Telemetry goes as JSON over REST to a **cloud backend** (FastAPI is the likely stack: the `.venv` has FastAPI and uvicorn, but this is circumstantial). Storage is described as AWS S3 or GCS, deployment as a serverless API. These are described as design intent, not confirmed.
- The extension shows alerts. Screenshots are `UI_1/2/3.jpeg`.
- Manifest version, permissions, and the exact JS/HTML are **unknown**. I won't guess.
- Architecture trade-off: **every user's browsing telemetry (including which domains) is sent to a server**, which conflicts with the report's own "privacy-conscious" claim.

## 7. Weaknesses and what I can improve on

| Gap | Improvement plan |
|---|---|
| Label = data source; no real attacks | Build **more realistic simulated cryptojacking traces** (sustained CPU or event-loop pressure, hidden-tab activity, worker bursts, mining-like periodic network) and, if you agree, also run a benign-but-heavy class (video, games, Meet, Colab) as *hard negatives*. State plainly that it is still simulated. |
| Random split, duplicates | Dedupe, then **group split by user and by domain**. Report it next to the random split to show the optimism gap. |
| Test-set reuse | Fix thresholds on validation or CV only. **Touch test once.** |
| Easy by construction | Add overlapping, harder attack generators, **a held-out generator** (train on one attack family, test on another), and a heavy-legit class. Report FPR at fixed recall. |
| Outliers and zeros | Cap or log-transform lag and counts, drop all-zero idle rows, add an explicit "measured" mask. |
| Per-snapshot features only | **Sequence model** (1D-CNN / GRU / small Transformer over a window of snapshots per tab), since mining is a *sustained* behaviour. This is the natural "more advanced" architecture for this data. |
| Double-counted imbalance | One mechanism only (focal or weights), tuned with CV. |
| No calibration or uncertainty | Calibrate (isotonic/Platt), report ECE, give a verdict with confidence. |
| Server round-trip leaks browsing data | **In-browser inference** (ONNX Runtime Web or a tree/MLP compiled to JS), so telemetry never leaves the device. Also removes the server dependency and gives an offline fallback by default. |
| Weak explainability | Per-feature SHAP for the tabular branch, so the extension can say "sustained event-loop lag + hidden tab + high POST rate". |
| Docs vs code mismatch | One config file with seeds and hyperparameters, and tests. |

## 8. Open questions for you

1. **Licence and consent:** do you have the friend's permission, and did the 6 users consent? I will not publish the raw file in the repo until you answer.
2. **Scope:** keep the project as **behavioural cryptojacking detection** (what the data supports), or do you want a different problem (for example URL phishing, which would need a new dataset)? I recommend the former.
3. **Which model folder** (`models` or `models1`) is the final one?

## Files created in this phase
- `BrowserShield-Pro/docs/ANALYSIS.md` (this file)

---

## Corrections (added in Stage A, after measuring more)

1. **`event_loop_lag_ms` maximum of 74,280,502 ms is not a "collection artefact".** The counts are **cumulative since page load**, and the longest recovered page uptime is 82,095,497 ms (22.8 h). It is a long-lived tab. (Section 2, "Heavy-tailed, uncapped values".)
2. **The "per_second" features are not per second.** They equal `count / page_uptime_ms` (per millisecond) when uptime > 0 and the raw count when uptime = 0 (96-99% match). See `DATA_LINEAGE.md` section 6. This regime mix is one of the artefacts that separates his synthetic rows from real ones (`STAGE_B_REPORT.md`).
3. **Provenance:** 6,602 of the 9,255 unique "normal" vectors have no recoverable user (stated in Phase 1 as 6,602 unique rows; now measured against the raw file).
4. **Models folder:** see `DATA_NOTES.md`; not resolved by the folder alone.
