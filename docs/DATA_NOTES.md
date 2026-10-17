# Data notes

## Licence and consent: UNCONFIRMED
No licence, README or source statement exists in the friend's folder. The raw telemetry pairs user IDs with visited domains. **Until the owner's written permission and the participants' consent are confirmed:**
- `data/` is git-ignored; no friend-derived row is published (repo, demo site or replays).
- Replays and demos use only data I collect myself.
- README carries placeholders for source and licence.

## De-identification (`src/deidentify.py`, one-time)
- **Dropped:** `user_id`, `domain`, `timestamp`, and `cpu_cores`, `memory_available` (the last two fingerprint a machine).
- **Kept as salted SHA-256 (10 hex chars):** `user_hash`, `domain_hash`. The salt is random, stored in `.secrets/salt` (git-ignored). The hashes exist only to build group splits and are never reported or exported.
- **Time:** `t_rel_s` = seconds since that user's first snapshot (absolute time dropped).
- **Outputs (`data/raw/`):** `telemetry_raw_deid.csv`, `normal_final1_deid.csv` (adds `user_hash`, `n_users` = how many users produced that vector), `synthetic_anomalies.csv` (no identifiers existed), `MANIFEST.json`.
- **Checks (tests):** no forbidden columns, no UUID pattern, no domain-like strings in any output.
- **Residual risk:** hashed IDs are pseudonymous, not anonymous; 4 usable users means behaviour patterns could still be distinctive. Another reason not to publish.
- The friend's source files are verified unchanged (SHA-256 before and after).

## Cleaning and splitting rules (all in code and `configs/`)
1. **Exact duplicates removed before any split** (feature vector, first kept): Reading A 10,973 -> 9,255 (1,718 dropped); Reading B 3,098 -> 2,653 (445 dropped). This removes 1,343 all-zero idle rows down to **one**, which makes the normal set *harder* and the deduped class mix differ from raw collection (e.g. counts-only rows are 22% of raw rows but 2.7% of the deduped Reading A normals).
2. **Groups:** vector seen under exactly one user -> that user; otherwise `unknown_source` (no provenance, or the vector occurs under several users). One indivisible group.
3. **Locked test set:** two whole user groups, chosen by size rank (2nd and 4th largest) from group sizes alone, before any modelling. 928 rows, identical under both readings; fingerprint in `configs/split.lock.json` and checked by a test.
4. **Dev folds:** leave-one-group-out over dev groups with at least 50 rows; smaller groups are always in training.
5. **Stage B used dev data only.** The test set was not touched.

## The friend's model folder (models/ vs models1/)
Unresolvable from the folder alone, so I did not resolve it by guessing:
- `xgb_ensemble.pkl` and `scaler_dl.pkl` are byte-identical. `.keras`, weights, bundle and config differ (`models/` 12 Mar, threshold 0.4666; `models1/` 14 Apr, threshold 0.4998).
- The notebook's code saves to `models1/`; its stored output (the run behind the reported metrics) prints `models/` and 0.4666. The report states no threshold and the folder has no API code.
- **Decision:** the baseline reproduction (Stage C) re-implements the *described method* and uses `models/`'s threshold rule (max F1 with recall >= 0.97, chosen on validation). I do not load his pickles (TensorFlow/XGBoost not installed).

## Known data caveats
- "Per second" features are per-millisecond when uptime > 0 and plain counts when uptime = 0; all counts are cumulative since page load (`docs/DATA_LINEAGE.md` section 6). The baseline keeps this convention; my own collector will not.
- 71% of unique normal vectors have no recoverable user.
- 4 users hold >99% of provenance-known rows; per-user results will be noisy.
- Real normals come from 6 users over 4.8 days. Nothing here is real mining traffic.
