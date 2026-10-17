# BrowserShield-Pro 🛡️

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Chrome Extension](https://img.shields.io/badge/Chrome-Manifest_V3-green.svg)](https://developer.chrome.com/docs/extensions/mv3/)
[![Tests Passing](https://img.shields.io/badge/tests-53%20passed-brightgreen.svg)](./tests)
[![Inference Latency](https://img.shields.io/badge/inference-%3C%201ms%20(on--device)-orange.svg)](./extension/inference.js)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

> **Real-time, on-device behavioural cryptojacking detection from browser telemetry, paired with a scientifically rigorous, leak-free evaluation protocol.**

BrowserShield-Pro is an end-to-end security system designed to detect in-browser cryptocurrency mining scripts (cryptojacking) purely from client-side behavioral telemetry—without relying on brittle domain blacklists, URL heuristics, or invasive code inspections. It features an **XGBoost** classification model calibrated via **Platt scaling**, an **out-of-distribution (OOD) safeguard**, a **sub-millisecond in-browser JavaScript inference engine**, and a production-grade **Google Chrome Manifest V3 extension** ("Sheilded").

---

## ⚡ Key Highlights & Benchmark Results

Evaluated on a **locked, single-access test set** of unseen real users' normal browsing telemetry and synthetic attack injections under a pre-registered protocol:

| Metric | Previous State-of-the-Art Recipe | **BrowserShield-Pro (Ours)** | Improvement / Impact |
| :--- | :---: | :---: | :--- |
| **ROC-AUC** | 0.955 | **0.972** | **+0.017** superior ranking discrimination |
| **PR-AUC (8.35% prevalence)** | 0.724 | **0.817** | **+0.093** precision-recall separation |
| **False Positive Rate (FPR)** | 13.0% (own rule) / 5.5% | **2.3%** (pooled) / **0.4%** (group 2) | **>82% reduction in false alarms** |
| **Detection Recall** | 81.0% | **97.0%** (dangerous + suspicious) | Catches evasive & throttled miners |
| **Inference Latency** | Network API Dependent | **< 1.0 ms (On-Device Client JS)** | 100% offline, zero network telemetry leak |
| **OOD Guardrail** | None (silent failure) | **Bounding Delta Policy** | Unseen extremes flagged as `UNSURE` |

*All results are generated deterministically and permanently archived in [`docs/FINAL_RESULTS.md`](./docs/FINAL_RESULTS.md) and [`reports/final_eval/`](./reports/final_eval/).*

---

## 🔬 Core Problem & Innovation

### The Challenge of Modern Cryptojacking
Cryptojacking attacks embed unauthorized WebAssembly (Wasm) or JavaScript hashing routines (e.g., RandomX, CryptoNight) into compromised or ad-injected web pages to monetize visitors' CPU cycles.
- **Why blacklists fail:** Attackers use fast-flux domains, dynamic CDNs, and short-lived proxies.
- **Why static code analysis fails:** Obfuscated JS and compiled WebAssembly binaries hide recognizable mining signatures.
- **Why existing ML models fail in practice:** Prior academic literature suffered from **data leakage**, **uncalibrated threshold rules**, and **synthetic shortcut learning** (models memorizing artifacts of the synthetic generator rather than true mining behavior).

### Our Approach: Honest Behavioral Telemetry
BrowserShield-Pro monitors runtime system signals per tab:
1. **Event Loop Lag (`event_loop_lag_ms`):** Heavy compute loops block the JavaScript main-thread event loop.
2. **DOM Mutation Cadence (`dom_mutation_count`):** Legitimate heavy pages (video streaming, WebGL games) mutate the DOM; cryptominers do intensive compute with near-zero visual updates.
3. **POST Network Heartbeats (`post_request_count`, `post_share`):** Mining pool share submissions manifest as periodic outgoing POST requests.
4. **Execution Context (`visibility_hidden`, `visibility_changes`):** Cryptominers deliberately continue heavy computation in hidden or background tabs.

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              BROWSER TAB RUNTIME                                │
│                                                                                 │
│   Page Hook (Main World)             Content Script (Isolated World)            │
│   ├── Overrides fetch / XHR / Beacon ├── Event Loop Tick Lag Monitor            │
│   └── Dispatches CustomEvents ───────►── DOM MutationObserver                   │
│                                      └── Page Visibility & Uptime Tracker       │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │ Raw Telemetry Stream
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ON-DEVICE INFERENCE ENGINE (inference.js)                    │
│                                                                                 │
│   1. Feature Extraction (15 BSP Features: log rates, lag fraction, ratios)      │
│   2. OOD Check (Dynamic bounding box: marks extreme outliers as UNSURE)         │
│   3. Standard Scaler Transform                                                  │
│   4. Tree Ensemble Evaluation (XGBoost JSON trees, sub-ms execution)             │
│   5. Platt Calibration (Maps raw ensemble margin to true risk probability)      │
│   6. Three-Tier Policy: [ SAFE < 5% FPR | SUSPICIOUS < 0.25% FPR | DANGEROUS ]   │
│   7. Heuristic Attribution Engine (Generates user-readable threat reasons)      │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │ Verdict & Attribution
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             CHROME EXTENSION POPUP                              │
│   - Real-time Threat Gauge (0 - 100% Risk Score)                                │
│   - Primary Risk Attribution Factor Badges                                      │
│   - Live Tab Telemetry Inspector (Lag, Network, DOM, Visibility)                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 💻 Chrome Extension ("Sheilded")

The project includes a ready-to-run Google Chrome extension built on **Manifest V3**:

- **Zero-Backend / Full Privacy:** All feature transformations, scaling, and XGBoost tree evaluations occur directly within the browser runtime using vanilla JavaScript. No telemetry ever leaves the machine.
- **Page Hook System:** Seamlessly monitors AJAX (`fetch`, `XMLHttpRequest`, `navigator.sendBeacon`) across pages without breaking site functionality.
- **Explainable Threat Attribution:** When an alert is triggered, the popup explains *why* (e.g., *"Main-thread blocked for 850ms (82% of execution time)"*, *"High POST frequency (92% of network traffic) matching mining pool shares"*).

### Quick Install in Chrome:
1. Open Google Chrome and go to `chrome://extensions/`.
2. Enable **Developer mode** (toggle in the upper right corner).
3. Click **Load unpacked** and select the [`extension/`](./extension) folder from this repository.
4. Open any website or the included local studio, click the **Sheilded** extension icon in your toolbar, and inspect live behavioral telemetry!

---

## 🧪 Interactive Benchmark Studio & Simulator

An interactive simulation and benchmark lab is included in [`demo/index.html`](./demo/index.html). It allows security researchers to test the detection engine against various workloads:

- **Mining Workloads:**
  - Full-throttle CPU WebAssembly compute loops.
  - Multi-threaded Web Worker hashing.
  - Throttled duty cycles (10%, 25%, 50%, 100%) designed to evade naive CPU threshold monitors.
  - Periodic mining pool POST share transmissions.
- **Hard Benign Workloads (False-Alarm Stress Tests):**
  - High-cadence DOM mutation churn (e-commerce / social feed simulations).
  - Heavy WebGL canvas rendering.
  - Active video playback with audio processing.

### Run the Studio Locally:
```bash
make demo
# Or: python3 -m http.server 8000
```
Then navigate to `http://localhost:8000/demo/index.html` in your browser.

---

## 📂 Repository Organization

```text
BrowserShield-Pro/
├── configs/                  # Frozen experiment configurations & hash locks
│   ├── stage_e_final.yaml    # Production pipeline definition
│   └── split.lock.json       # Locked holdout split fingerprints
├── demo/                     # Interactive Web Studio & Wasm miner simulator
│   ├── index.html            # Studio user interface
│   ├── demo.js               # Workload generation & benchmark runner
│   └── model_bundle.json     # Compiled model & calibration bundle
├── docs/                     # Research papers, formal analysis & reports
│   ├── FINAL_RESULTS.md      # Test-set evaluation results & comparative analysis
│   ├── STAGE_E_REPORT.md     # Model selection, tuning, & Platt calibration
│   ├── STAGE_D_REPORT.md     # Feature engineering & baseline comparisons
│   ├── STAGE_C_REPORT.md     # Reproduction of prior literature recipe
│   ├── ANALYSIS.md           # Dataset provenance & leakage vulnerability audit
│   └── PLAN.md               # Pre-registered experimental roadmap
├── extension/                # Manifest V3 Google Chrome Extension ("Sheilded")
│   ├── manifest.json         # Extension configuration
│   ├── background.js         # Service worker & tab lifecycle manager
│   ├── content.js            # In-page event loop & DOM telemetry collector
│   ├── page_hook.js          # Main-world fetch/XHR network hook
│   ├── inference.js          # On-device pure JavaScript inference engine
│   ├── popup.html            # User interface & real-time risk gauge
│   └── popup.js              # Gauge rendering & risk attribution logic
├── reports/                  # Generated figures, calibration plots, & metric tables
├── src/                      # Core Python ML research & evaluation pipeline
│   ├── models2.py            # XGBoost & tree model wrappers with Optuna tuning
│   ├── features2.py          # 15 BSP feature extraction pipeline
│   ├── synth.py              # Cryptojacking attack generator & throttle simulator
│   ├── splits.py             # Leak-free grouped cross-validation split engine
│   ├── export_model.py       # Serializes trained model & Platt scaler to JSON
│   ├── final_eval.py         # One-shot locked test set evaluation script
│   └── deidentify.py         # Salted hashing & privacy anonymization
├── tests/                    # Comprehensive unit tests (53 passing)
├── Makefile                  # Build, test, export, and demo automation
└── requirements.txt          # Python dependencies
```

---

## 🛠️ Getting Started & CLI Usage

### 1. Installation
```bash
git clone https://github.com/kanakkadulkar/Browser-Shield-pro.git
cd Browser-Shield-pro

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Test Suite
Verify that all 53 unit tests pass:
```bash
make test
# Or: pytest tests/
```

### 3. Export Model Bundle for Browser Inference
Re-train and export the model bundle directly to `extension/model_bundle.json` and `demo/model_bundle.json`:
```bash
make export-bundle
```

### 4. Run the Local Demonstration
```bash
make demo
```

---

## 📊 Scientific Methodology & Evaluation Protocol

1. **Leak-Free Group Splits:**
   Evaluations are split strictly across **user identity groups** (leave-one-user-out). No telemetry samples from the same user or machine appear in both training and test sets.
2. **Exact-Duplicate Removal:**
   Removed 1,718 identical zero-activity rows prior to fold creation, preventing artificially deflated baseline test difficulty.
3. **Locked Test Set:**
   A dedicated test set consisting of 928 real normal browsing rows across 2 held-out user groups was locked before training and evaluated strictly **once** with SHA-256 hash verification.
4. **Honest Reporting of Limitations:**
   Unlike prior works that reported uncalibrated 99%+ accuracy by testing on synthetic generator duplicates, our documentation openly audits domain shifts, counts-only telemetry failure modes, and unseen throttled miner families (see [`docs/FINAL_RESULTS.md`](./docs/FINAL_RESULTS.md)).

---

## 📄 License & Academic Attribution

This project is open-source under the [MIT License](./LICENSE).

- **Inspiration:** Inspired by the BE capstone project *"CryptoShield / BrowserShield"*.
- **Privacy Notice:** In compliance with ethical research practices, raw proprietary user telemetry is git-ignored and not redistributed. All evaluation artifacts, models, code, and deterministic verification scripts are fully included.

---

*Authored by **Kanak Kadulkar** · 2026*
