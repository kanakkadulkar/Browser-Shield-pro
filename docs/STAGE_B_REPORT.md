# Stage B report: adversarial-validity check and rebuilt generator

Code: `src/adversarial.py`, `src/synth.py`, `configs/synth.yaml`. Raw results: `reports/stage_b/adversarial_validity.json`, `summary.md`, `single_feature_leakage.png`. Seed 42. **Dev data only; the locked test set was not touched.** Ran under both readings of "final" (`docs/DATA_LINEAGE.md`).

## Method
Train a classifier to tell **synthetic attack** from **real normal**, leave-one-group-out (a group is never on both sides), pooled out-of-fold ROC-AUC. 0.5 = indistinguishable, 1.0 = trivially separable. Tree model: depth-3 gradient boosting, so non-monotone separation is caught. Run per single feature, on all 11, on "signal" channels (lag, network, POST, domains: where a miner could plausibly leave a trace) and on "non-signal" channels (idle, DOM, visibility: where my generator leaves real values untouched).

Two attack sets: **friend** = his 1,000 rows (800 in dev after removing 4 of 20 random test batches) and **rebuilt** = my injection generator.

## Result 1: the friend's synthetic data is separable from real data by artefacts

| | Reading A | Reading B |
|---|---|---|
| All 11 features | **1.000** | **1.000** |
| Non-signal channels only (idle, DOM, visibility) | **0.997** | **0.903** |
| Best single feature (tree AUC) | `network_per_second` 0.994 | `event_loop_lag_ms` 0.991 |
| Permutation importance, top feature (AUC drop) | `network_per_second` 0.217 | `network_per_second` 0.345 |

Structural fingerprints, measured on the 800 dev rows of his synthetic data vs real dev normals (Reading A):

| Property | Real normals | Friend's synthetic |
|---|---|---|
| The 3 rate features imply one shared uptime (as the collector produces them) | **100%** | **0%** |
| Rows exceeding the real maximum on at least one feature | 0% | **100%** |
| `network_per_second` | real p99 (uptime>0) 0.0195 | median **37.2** (about 1,900x) |
| POST count <= request count | 100% | 94.4% (5.6% impossible) |
| `visibility_hidden` mean | 0.70 | 0.39 |
| Rows in the counts-only regime | 2.7% | 0% |

Reading: his attack rows were not produced by the same pipeline as the real rows (rates on a different scale, rates inconsistent with each other, impossible POST/request pairs). **Any model can win on those artefacts alone.** This is direct evidence for the simulator-vs-real shortcut. It does **not** show that his model fails on real mining; it shows his test cannot tell.

## Result 2: the rebuilt generator removes those artefacts, but not the separability

Design: each attack = a **real** dev normal row of the same group plus an injected miner-like effect on the signal channels only (four families, three strength tiers, all parameters in `configs/synth.yaml`, all **assumptions**). The three rates are recomputed with the collector's own formula. Attacks inherit their base row's group.

| | Reading A | Reading B |
|---|---|---|
| Attacks generated (dev) | 2,081 | 427 |
| Rates share one uptime | 100% | 100% |
| Rows above real max on >= 1 feature | 7.1% (the injected traffic) | 12.9% |
| Non-signal channels only, AUC | **0.545** | **0.479** |
| **Control:** un-injected eligible real rows vs all normals, all-feature AUC | 0.536 | 0.552 |
| All 11 features, AUC | **0.976** | **0.935** |
| Best single feature, AUC | `post_request_count` 0.846 | `network_per_second` 0.806 |

- The non-signal AUC sits at the **control's noise floor** (0.54 to 0.55: my attacks come only from rows with uptime >= 60 s, so a small selection effect remains). No artefact channel is left.
- **By tier** (all-feature AUC / best single feature):

| Tier | A: all-feature | A: best single | B: all-feature | B: best single |
|---|---|---|---|---|
| weak | 0.958 | `event_loop_lag_ms` 0.817 | 0.888 | `event_loop_lag_ms` 0.779 |
| medium | 0.983 | `network_per_second` 0.854 | 0.942 | `network_per_second` 0.816 |
| strong | 0.989 | `post_request_count` 0.911 | 0.976 | `post_request_count` 0.875 |

- **Plan target ("no single feature above about 0.8 on the hard tier"): met in Reading B (0.779), missed narrowly in Reading A (0.817).** I did not retune to hit it.
- **The weak tier is not hard for a multi-feature model** (0.958 / 0.888). Several small shifts add up. So the rebuilt set is *clean of artefacts* but still *easy*: it is dominated by the injected signal sitting on the tails of real data.
- By family (all-feature AUC, A): main_thread 0.995, throttled 0.985, worker_pool 0.957, network_only 0.951. Without a lag signal (worker_pool) the model still finds the pool traffic.

## What this does and does not establish
- **Establishes:** the friend's evaluation is confounded by generator artefacts (Result 1), and the rebuilt generator has none of the specific artefacts I measured (Result 2).
- **Does not establish:** that the rebuilt attacks resemble real mining. Passing this check means "not trivially separable by artefact", not "realistic". Every effect size is my assumption. Real validation needs the lab collection.
- A low non-signal AUC is partly **by construction** (I left those channels untouched). It rules out accidental leakage, it is not evidence of realism.
- **Not yet evaluated:** the benign-heavy hard-negative generator (`kind="benign_heavy"`) exists and is unit-tested but has not been used.
- Generator limits: attacks only from rows with uptime >= 60 s; strengths uniform; no temporal structure (the data has none).
- Dedupe changes the mix of "boring" states (all-zero idle rows 1,343 -> 1), so false-positive numbers on the deduped set are for a harder-than-deployment normal class.

## Readings A vs B
| | A | B |
|---|---|---|
| Dev normals / validation folds | 8,327 / 3 | 1,725 / 2 |
| Conclusions | same | same |
| Numeric differences | friend non-signal 0.997, rebuilt all 0.976 | 0.903, 0.935 |

Both readings agree on every qualitative finding. Numeric differences track sample size (B has 4.8x fewer dev rows and only 2 folds, so its figures are noisier; B's rebuilt non-signal AUC of 0.479 vs control 0.552 is noise).

**Recommendation: Reading A as the primary dataset.** It matches what the final notebook trained on (rules a, b, c), has 4.8x more dev rows and 3 folds, and gives the same conclusions. **Report Reading B beside it at every later stage** as a fully-provenanced sensitivity analysis. Caveat for A: 6,617 of its 8,327 dev normals are the single `unknown_source` group, so its "unknown" fold tells us about an unidentified mix, not about a user.

## Next (Stage C)
Baseline reproduction (his recipe) under both protocols. I expect, but have **not measured**, that it will still score high on the rebuilt attacks because they stay easy; I will report the size of the drop honestly, including if it is small.
