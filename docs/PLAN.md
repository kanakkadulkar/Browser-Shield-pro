# Phase 2 Plan: BrowserShield-Pro (behavioural cryptojacking detection)

Status: **proposal, awaiting approval. Nothing has been trained, installed or run.**
Scope fixed by you: behavioural cryptojacking detection from per-tab telemetry. No URL phishing.

## 1. Facts that shape the plan (all measured; see ANALYSIS.md)

| Fact | Consequence |
|---|---|
| Positives are synthetic, negatives are real | A "simulator vs real" shortcut exists. Plan section 3 attacks it directly. |
| Only **3,098** of 10,973 "normal" rows have a user/domain. The other **6,602 unique rows have no provenance** (`final1` contains every unique `final` row plus these) | Group splits are possible on only 3,098 rows. The 6,602 form one extra **"unknown-source" group** and are never split across train and test. |
| 6 users, but 4 hold 99% of rows (1,502 / 855 / 394 / 333) | Leave-one-user-out gives **4 meaningful folds**. Per-user results will be noisy and I will say so. |
| 15.7% exact duplicate rows | Dedupe first, then split. |
| Raw telemetry is time-stamped at **180 s** cadence, about 14 tabs per snapshot. The 10,973-row and synthetic files have **no timestamps** | A sequence model **cannot be trained on existing data**. It depends on the lab collection (section 4), sampled at 1 to 5 s. This is stated as a condition, not a promise. |
| `models/` vs `models1/` | See section 2. |

### Friend's model folder ambiguity (item 3)
- The `xgb_ensemble.pkl` and `scaler_dl.pkl` files are byte-identical. `.keras`, weights, bundle and config differ (`models/` dated 12 Mar, `models1/` dated 14 Apr).
- Configs: `models/` threshold **0.4666**, `models1/` threshold **0.4998**. Both use 18 features and a 0.5/0.5 blend.
- The final notebook's **code** saves to `models1/`, but its **stored output** (which matches the report's metrics run) prints `models/` and threshold **0.4666**.
- The report states no threshold value, and the folder has **no API code**, so neither source settles it.
- **Decision:** use `models/` (0.4666), because it matches the stored outputs behind the reported numbers. Ambiguity goes in `docs/DATA_NOTES.md`.
- The pickles can't be loaded without TensorFlow and XGBoost, and the anomaly generator is not saved as a script. So I **re-implement his recipe** (18 features, tiered generator from notebook section 2.2, Attention-MLP, focal loss, XGB blend, 50/50, threshold rule) as the baseline and run it under my protocol. I will label it "reproduction of the described method", not his checkpoint.

## 2. Evaluation protocol (built first, before any model)

1. **De-identify** (your item 1): drop `user_id`, `domain`, `timestamp`. Keep a salted hash of user and of domain, **used only to build group splits** and never exported. Salt is generated locally and not committed. Output goes to `data/processed/`. `data/raw/` holds only the de-identified file, not the original. Documented in `docs/DATA_NOTES.md`; licence/source placeholder in README.
2. **Exact-duplicate removal** (on the feature vector, per class) **before** any split. Log how many rows are removed.
3. **Groups:** user (4 usable users), plus an "unknown-source" group, plus (once collected) lab **session** and **workload family**.
4. **Splits:**
   - **Test:** fixed hold-out of whole groups, **touched once**, at the very end. Candidates: one real user plus one lab session set. Locked in `configs/split.yaml` before training.
   - **Development:** grouped k-fold / leave-one-user-out over the remainder, for model selection, tuning and threshold choice.
   - **Threshold:** chosen on validation folds only (fixed-recall rule, below), then frozen.
5. **Report both** the friend's original protocol (random row split, no dedupe) **and** the honest protocol for every model. The gap is a headline result: "how much his numbers drop".
6. **Seeds and CIs:** fixed seeds in YAML; 5 seeds for stochastic models; bootstrap confidence intervals on the test set. With so few groups, I report intervals, not just point values.
7. **Fitting rule:** scalers and caps are fit on training folds only.

## 3. Reducing the simulator-vs-real shortcut

**(b) Adversarial-validity check (first deliverable).**
- Train a small classifier (synthetic vs real) **on each single feature**, and on all features, using grouped CV. Report AUC per feature and permutation importance, so the leaking features are named.
- Already measured: `network_per_second` 0.973, `lag_per_second` 0.932, `dom_per_second` 0.919 (see ANALYSIS.md). This shows how much of any score is the generator, not behaviour.
- Use it to rebuild the generator: remove features that leak purely from implausible ranges (e.g. `event_loop_lag_ms` in the hundreds of thousands of ms), so no single feature gives AUC above about 0.8 for the synthetic **hard** tiers. Report the check before and after.

**(a) One-class track** (trained on normal rows only, never sees synthetic attacks):
- Baselines: Isolation Forest, One-Class SVM.
- Neural: autoencoder (reconstruction error), Deep SVDD.
- Evaluated against the same attack rows. Because training is label-free, it cannot learn the generator's fingerprint. If it scores far below the supervised models, that gap is evidence the supervised numbers are inflated.

**(c) Lab collection**: the only source of non-synthetic attacks (section 4).

## 4. Lab collection plan (collector script written; **not run without your OK**)

**Components (all local):**
- `lab/collector/`: the telemetry collector. It reuses the exact production schema (same 11 features plus the raw columns) and samples at **1 to 5 s** to give temporal windows. It is the same code the extension's content/background scripts will use, so there is no schema drift between training and deployment.
- `lab/pages/`: a local test server on `localhost`.
  - **Attack pages:** a CPU-bound **WebAssembly hashing kernel** (mining-like: tight compute loop, optional Web Workers) with a **duty-cycle throttle** (10% / 25% / 50% / 100%) and a worker count (1..N). It adds mining-like network chatter (small periodic POSTs to localhost) and a hidden-tab variant.
  - **Benign heavy pages (hard negatives):** video playback, a WebRTC loopback "call", a WebGL/canvas demo, a large JS app, a heavy-DOM page, plus ordinary idle and browsing tabs.
- `lab/run_session.py` (or a JS runner) writes one CSV per session with labels `session_id`, `workload`, `family`, `throttle`.

**Two things you should know before approving:**
1. **It will be a mining-equivalent workload, not a pool-connected miner.** Real miner code (e.g. xmrig-wasm builds) means downloading untrusted binaries and connecting to a pool. I do not propose that. My kernel reproduces the compute signature only. Labels in the report will say "simulated miner workload", never "real cryptojacking". If you want a real miner build, tell me explicitly and I will list the exact source for your sign-off.
2. **Compiling WASM needs a toolchain** (clang with the wasm32 target, or `wabt`). I will check what you have and ask before installing anything.

**Safety:** every run is gated. I will ask before any sustained CPU use, with the expected duration, CPU percentage, and a hard timeout. Default duration is 60 s per session, capped at 100% on at most N-1 cores, with a kill switch.

**Volume target:** roughly 60 sessions (about 10 attack configs x 3 repeats, about 10 benign workloads x 3 repeats), several minutes each. Grouped by `family` so a held-out family tests generalisation (train on throttle 10/50%, test on 25/100%, and hold out a whole benign family).

**Limits:** one machine, one browser, one user. It supports the claim "works on this machine's workloads", not "generalises to the web". I will report it that way.

## 5. Models

| # | Model | Role | Notes |
|---|---|---|---|
| B0 | Friend's recipe (Attention-MLP + XGBoost, focal loss, 18 features) | **Baseline** | Run under both protocols. |
| M1 | LightGBM / XGBoost | Gradient-boosting baseline | Optuna-tuned on dev folds, monotone constraints where sensible. |
| M2 | **FT-Transformer-style tabular attention network** (feature tokens, so attention is over *named features*) | Tabular attention net | Fixes his gate, which attends over hidden units, not features. |
| M3 | **1D-CNN / TCN** (optionally a small Transformer) on windows of 8 to 32 snapshots | Sequence model | **Only if the lab data is collected.** Otherwise dropped and reported as such. |
| M4 | Autoencoder / Deep SVDD, Isolation Forest | One-class track | Section 3(a). |
| E | **Calibrated stacked ensemble** of M1, M2, (M3) with isotonic or Platt calibration on validation folds | Final | Weights/stacker fit on dev folds only. |

Imbalance handling uses **one mechanism per model** (class weight **or** focal loss, tuned by CV), not both, as in his notebook. Early stopping on validation. LR scheduling for neural nets.

## 6. Metrics (all on the locked test set, with CIs)

- **F1, PR-AUC, ROC-AUC**, precision, recall.
- **FPR at fixed recall** (95% and 99%) and **recall at fixed FPR** (1% and 0.1%). The operating point is chosen on validation only.
- **False positives on benign-heavy workloads**, reported on their own line.
- **Per-user and per-family** results. Leave-one-user-out gives 4 folds, so I show spread, not a single mean.
- **Calibration:** ECE and reliability curves, before and after calibration.
- **Latency** (p50/p95 per verdict, in Python and in-browser), **model size** (float32 vs int8).
- **Robustness:** unseen user, unseen attack family/throttle, distribution shift (different machine settings, if available), and feature perturbation (lag/network jitter).
- A single comparison table in `reports/`: his approach vs mine, under his protocol and under the honest one. Any number I did not measure does not appear.

## 7. Explainability

- **Tree and tabular models:** SHAP (TreeExplainer for boosting) per verdict, giving the top 3 signed contributions in real units, e.g. "event-loop lag 4x above normal, hidden tab, POST rate high".
- **Extension:** the model ships a small **precomputed explanation** path. For in-browser inference, I use either (i) a distilled linear/shallow-tree explainer approximating SHAP, with its fidelity measured and reported, or (ii) exported SHAP-style contributions from the boosted model. I will say which one and report the approximation error. No claim of "exact SHAP in the browser".
- Attention maps from M2 are reported as a diagnostic, not as proof of reasoning.

## 8. Deployment recommendation

**Recommend: quantized ONNX, in-browser (ONNX Runtime Web, WASM backend), inside the extension's service worker or an offscreen document.** No FastAPI by default.

| | In-browser ONNX | FastAPI backend |
|---|---|---|
| Privacy | **Telemetry never leaves the device.** This matters because the data pairs activity with domains; the original design shipped it to a server. | Needs consent, transport security, retention policy. |
| Latency | No network round-trip. The model is tiny, so expected **sub-10 ms**. *Estimate; will be measured.* | Round-trip dominated, and it fails offline. |
| Size | A few hundred KB to low MB after int8. ORT Web runtime adds about 10+ MB WASM. *Estimate; will be measured.* | N/A in the extension. |
| Ops | Nothing to host. Offline fallback is the default. | Hosting, auth, scaling. |
| Risk | MV3 service workers are short-lived, so I use an offscreen document or a lightweight JS tree/MLP evaluator. If ORT Web proves too heavy, **fallback: export the boosted model to plain JS** (no runtime). | Simpler to update models. |

I keep a small **optional FastAPI** in `src/` only for developing and benchmarking, not shipped.

**Extension (built from scratch, Manifest V3):**
- A telemetry collector in the content script (event-loop lag, DOM mutations, network counts via PerformanceObserver, visibility) with a background service worker aggregating per-tab windows. Same schema as the lab collector.
- **Minimal permissions:** `storage` and `activeTab`; host access limited to what a content script needs. I will list and justify each in the README. No `<all_urls>` unless the collector cannot work without it, and then it will be flagged for your decision.
- Verdict safe / suspicious / dangerous with a confidence score and the top reasons, a loading state, error handling, and an offline fallback (a rule-based heuristic if the model fails to load).
- **Data stays local by default.** Nothing is uploaded.

## 9. Compute and dependencies (need your approval)

- **Hardware:** I have not checked for a GPU. These models are tiny (tens of thousands of rows). **CPU is enough**, and I will say so if I find otherwise.
- **Python packages needed** (none installed yet; only `fastapi`, `h5py`, `numpy`-ish pieces exist in the friend's venv, which I will not use): `numpy`, `pandas`, `scikit-learn`, `lightgbm` (or `xgboost`), `shap`, `optuna`, `pyyaml`, `matplotlib`, `pytest`, `onnx`, `onnxruntime`, `skl2onnx` / `onnxmltools`.
- **Heavy item:** **PyTorch (CPU build)** for M2/M3/M4, a few hundred MB. I recommend PyTorch over the friend's TensorFlow (cleaner ONNX export, smaller install). **Please approve or decline.** If declined, M2-M4 become scikit-learn / MLP approximations and the plan shrinks accordingly.
- Everything goes in a fresh `BrowserShield-Pro/.venv`. I will not touch the friend's venv.
- No model downloads. All models train from scratch on this data.

## 10. Build order (Phase 3, each step verified before the next)

1. Project skeleton, configs, de-identification + `DATA_NOTES.md`, dedupe, split code **and its tests**.
2. Adversarial-validity check and rebuilt synthetic generator.
3. Baseline reproduction (B0) under both protocols. The "how much his numbers drop" result.
4. M1, M4, then M2, with tuning on dev folds only.
5. Lab collector and test pages written, then **stop and ask you** before any sustained-CPU run. M3 and the held-out-family tests happen only if you run the collection.
6. Calibrated ensemble, then the **one-time test-set evaluation**.
7. ONNX export, quantization, size/latency measurements, SHAP-based explanations.
8. Extension (Phase 4), README and tests (Phase 5).

## 11. Risks I am stating up front

- **Results may look worse than his.** That is the point. If honest numbers are lower, I report them as they are.
- **With 4 usable users and a single lab machine, confidence intervals will be wide.** I will not claim generalisation I cannot show.
- **Without the lab data there is no real or simulated-real attack, only synthetic.** The report will say so in the results table, not buried.
- **If no model beats Isolation Forest or boosting under the honest protocol,** I will report that rather than pick a winner by narrative.

## Decisions I need from you
1. **Approve the plan** (or tell me what to change).
2. **PyTorch CPU build and the other packages in section 9:** approve?
3. **Lab collection:** OK to write the collector and the mining-equivalent test page (no run yet)? And do you accept "simulated miner workload" instead of a real pool-connected miner?
4. **Extension permissions:** I will ask before using any broad host permission.

---

# Addendum A: Demo-ability (interview use)

Status: **proposal.** Honesty rules from sections 2, 6 and 11 are unchanged. Where a demo wish conflicts with them, the conflict is stated below, not hidden.

## A1. Dependencies and conflicts you should know first

1. **The live detector needs the lab data.** A static page can only measure its own tab. Visitors' machines differ from mine. A model trained only on the friend's rows plus a generator has **never seen real browser telemetry from a running workload**, so a live verdict would be unreliable and any "it works" on screen would be unearned. **Without the lab collection (section 4) I would not ship the live detector as a detection claim**; it would be a replay-only demo. Recommendation: treat lab collection as required for the demo.
2. **The live attack is in-distribution by design.** The page's miner workload is the same family as the lab attack training data. A correct verdict on stage shows "detects the workload it was trained on", not generalisation. The UI says that in one line and links to the held-out-family results (hard negatives, unseen throttle/family) on the dashboard.
3. **Visitor-machine drift.** CPU speed, background-tab timer throttling, browser version and extensions all shift features. I add an **out-of-range guard**: if inputs fall outside the training range, the verdict is "unsure, outside what this model has seen", not a forced safe/dangerous.
4. **Worker-based CPU load barely moves main-thread event-loop lag.** Real browser miners run in Web Workers. So the demo's signal may come from other features (worker count, network chatter, sustained activity), not lag. The raw data has `worker_count` and `cpu_hint`, but the friend's 11 features omit them. I will **include them in my feature set if the collector can measure them in-page**, and the "top reasons" shown will be whatever SHAP actually reports, even if it is not the story you expect.
5. **Friend's data in a public repo/site.** Until you have the permission (your item 1): the repo and the site ship **no friend-derived rows**. Replays use **only my lab sessions**. The dashboard shows aggregate metrics only. `data/raw/` stays git-ignored until you confirm.
6. **Publishing is outward-facing.** I will build the site and verify it locally. I will **not deploy to GitHub Pages/Vercel/Netlify or push anything** without your explicit go-ahead.

## A2. Demo site (`demo/`, static, no backend, nothing uploaded)

Plain HTML/JS modules (no framework; fewer bytes, nothing to break offline). One shared telemetry-collector module, **the same file the extension uses**, so the demo cannot drift from the product.

| Page | Content | Safety / honesty |
|---|---|---|
| **Live detector** | "Start simulated miner workload" button, always-visible **Stop**, **hard auto-stop at 30 s**, intensity slider **capped at 50% duty on 1 worker** (cap value is my proposal; you can change it). Live verdict (safe / suspicious / dangerous / unsure), confidence, top 3 SHAP reasons. | **Never auto-starts.** Plain-language notice: "burns CPU in this tab only, uses no network, mines nothing". Workload is a hashing loop, labelled **"simulated miner workload"** everywhere. Pauses itself if the tab is hidden. |
| **Benign comparison** | Buttons: video-like playback (canvas to `<video>` via `captureStream`, no bundled video file), WebGL shader, big-DOM churn. Same stop and 30 s cap. | Shows the model does not flag everything. If a benign workload **is** flagged, the UI shows it. No retuning to make it pass. |
| **Results dashboard** | Charts generated from `reports/*.json|csv` by a build script: friend's method under random split vs honest split vs my models, PR curves, FPR at fixed recall, calibration, per-user and per-family. | **Honest-protocol numbers are the headline.** Friend's-protocol numbers appear only as the labelled comparison. Charts are drawn from files, never hand-typed. Confidence intervals shown. |
| **Method and limits** | Evaluation design, data caveats, what was **not** proven (no real-world coverage, one machine, 4 usable users, simulated attacks). | Static text, plus numbers pulled from `reports/`. |

Footer on every page: model size, inference latency (measured live in the visitor's browser), first-load size, and credit to the original BE project (CryptoShield / BrowserShield) and the dataset source (**placeholder until you provide it**).

## A3. Model runtime and size budget

- **Default for the demo: plain-JS export** (tree ensemble plus small MLP evaluated in JS). ONNX Runtime Web's WASM runtime is about 10+ MB (estimate, to be measured), too heavy for a "small first load".
- ONNX Runtime Web stays as an **optional comparison**: if the measured first load is acceptable, it can ship as a lazy-loaded second backend; otherwise the repo still contains the ONNX export and benchmark, but the site does not load it.
- **Targets, not promises:** first-load JS + model under about 500 KB before charts; charts library bundled locally (not CDN) so it works offline. All values are **measured and printed** by a `make size` check, and shown in the UI footer. If a target is missed, the report says so.
- JS-export fidelity: predictions are compared against the Python model on the full test set (max absolute difference reported), including after int8 quantization.

## A4. Offline-safe operation and replay mode

- **Service worker** pre-caches all assets (pages, JS, model, chart lib, replay JSONs). After first load, the demo works with no internet.
- **Replay mode** drives the **same UI** from `demo/replays/*.json`: pre-recorded lab sessions (attack at several intensities, each benign workload, idle). A persistent banner says **"REPLAY of a recorded lab session, not live telemetry"**, and the verdict panel is labelled "model run on recorded data".
- Auto-fallback: if live telemetry fails to initialise or looks implausible (e.g. all zeros), the UI offers replay, **it does not silently switch**.
- If the lab collection is not run, replays would have to come from the generator. They would then be labelled **"synthetic replay"**, and I would tell you that this weakens the demo.

## A5. Extension packaging (Manifest V3)

- **Permissions proposal (minimal, each justified in README):** `activeTab`, `scripting`, `storage`. The popup's "Analyse this tab" injects the collector **into the current tab only, on click, for a limited window**. **No host permissions by default.**
- **Continuous background monitoring of all tabs** would need broad host access. I propose making it an **optional permission requested at runtime**, off by default. Not building it as the default unless you say so.
- **Popup demo mode:** a toggle that attaches to the bundled local demo page (served from the extension or `localhost`) so you can show the extension without visiting any real site. Needs only a narrow match for the demo origin.
- **Deliverables:** `extension/` (unpacked) and `dist/browsershield-pro-<version>.zip`, plus README "Install in 60 seconds" (`chrome://extensions` > Developer mode > Load unpacked).
- Offline fallback inside the extension: a rule-based heuristic if the model fails to load, shown as a distinct "fallback" badge.

## A6. Demo artifacts

| File | Notes |
|---|---|
| `docs/DEMO_SCRIPT.md` | 2-minute and 5-minute walkthroughs with exact click order and speaking points. **Written last**, with numbers quoted from `reports/` so they cannot be wrong. |
| `docs/INTERVIEW_QA.md` | Honest answers: why not his model, how I know it is not overfit (grouped splits, one-shot test, CIs), what the data cannot show, why in-browser inference, how SHAP reasons are produced and approximated, failure cases (drift, workers vs lag, benign false positives). **Numbers filled in after measurement**, not before. |
| `docs/ARCHITECTURE.md` | One page, mermaid diagram. |
| `README.md` top | One-line pitch, GIF/screenshot placeholders, live-demo link placeholder, results table (honest numbers first), "What I improved over the original" (specific and honest), licence/source placeholder. |
| `Makefile` (`make reproduce`) | Regenerates processed data, splits, metrics, plots, dashboard JSON, JS/ONNX export and size report **from the committed de-identified raw file and my lab CSVs**. It does **not** re-run the lab collection (needs a human at the machine). It needs the friend's permission before the de-identified file is committed. Also `make test`, `make size`, `make demo`. |

## A7. Revised build order

My earlier steps (section 10) are labelled stages A to H below. You referred to "stage D" and "stage E"; I am reading those as the models and the lab-collector steps. Tell me if you meant otherwise.

| Stage | Work | Demo items |
|---|---|---|
| A | Skeleton, configs, de-identification, dedupe, split code + tests | `Makefile` skeleton |
| B | Adversarial-validity check, rebuilt generator | |
| C | Baseline reproduction under both protocols | |
| D | M1, M4, M2 tuned on dev folds | **Demo shell + dashboard skeleton** (using dev-fold numbers, clearly marked "development, not final") |
| E | Lab collector + test pages written; **pause for your OK to run** | **Shared collector module, live-detector page UI** (no verdicts yet) |
| F | Lab sessions (if you run them), M3, calibrated ensemble, **one-shot test evaluation** | Dashboard switches to final numbers; replays recorded |
| G | JS/ONNX export, quantization, SHAP explanations, size/latency | **Live detector wired up, offline service worker, replay mode, footer metrics** |
| H | Extension (MV3), packaging, zip | Popup demo mode, "Install in 60 seconds" |
| I | README, ARCHITECTURE, DEMO_SCRIPT, INTERVIEW_QA, `make reproduce` check | |

**Note:** the live verdict cannot be real before stage G, so the shell exists earlier but shows no verdict until then.

**If time is short, priority is as you set it:** live detector page, results dashboard, README, demo script. Without lab data, the live detector degrades to replay-only (A1.1).

## A8. Additional approvals needed

1. **Lab collection is now required for the live demo.** OK to proceed on that basis (I still ask before each sustained-CPU run)?
2. **Safety caps:** 30 s auto-stop, 50% duty on 1 worker. Acceptable, or different caps?
3. **Permissions:** `activeTab` + `scripting` + `storage` only, with continuous monitoring as an optional runtime permission. OK?
4. **Hosting:** I build and test locally only. Tell me when and where (GitHub Pages / Vercel / Netlify) to deploy.
5. **Dataset source / licence text** for the footer and README: I'll leave placeholders until you send it.
