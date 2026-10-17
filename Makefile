PY := ./.venv/bin/python

.PHONY: deidentify protocol stageb test reproduce
deidentify:   ## one-time; needs the friend's folder (read-only) and creates a local salt
	$(PY) -m src.deidentify
protocol:     ## dedupe + group split sizes -> reports/stage_a/protocol.json
	$(PY) -m src.protocol_report
stageb:       ## adversarial-validity check (dev data only) -> reports/stage_b/
	$(PY) -m src.adversarial
test:
	$(PY) -m pytest -q
# Starts from the de-identified files in data/raw/ (not the original data).
# Later stages (baseline, models, export) are appended here as they are built.
reproduce: protocol stageb stagec stagec-report stagec-v2 staged staged-report test

.PHONY: stagec stagec-report
stagec:        ## runs 21 jobs (his recipe + baselines, both readings, 3 seeds); ~3 min on 10 cores
	WORKERS=9 $(PY) -m src.stage_c
stagec-report: ## bootstrap CIs, sweep curves, tables -> reports/stage_c/
	$(PY) -m src.stage_c_report

.PHONY: stagec-v2 staged staged-report
stagec-v2:      ## Stage C re-run under generator v2 (frozen Stage C config, separate output folder)
	GEN_VERSION=2 STAGEC_DIR=stage_c_v2 WORKERS=9 $(PY) -m src.stage_c
	GEN_VERSION=2 STAGEC_DIR=stage_c_v2 $(PY) -m src.stage_c_report
staged:         ## Stage D: 15 jobs, ~10 min on 10 cores
	WORKERS=9 $(PY) -m src.stage_d
staged-report:
	$(PY) -m src.stage_d_report
	$(PY) -m src.v1_v2_compare

.PHONY: stagee stagee-analysis freeze-e oddity
stagee:          ## Stage E: 15 jobs (M2 tuning is slow: ~25 min on 10 cores)
	WORKERS=9 $(PY) -m src.stage_e
stagee-analysis: ## calibration, ensemble, regime variants, threshold policy (rule-driven) -> reports/stage_e/
	$(PY) -m src.stage_e_analysis
oddity:
	$(PY) -m src.oddity
freeze-e:        ## writes configs/stage_e_final.yaml + lock; run ONCE, before any test-set access
	$(PY) -m src.stage_e_freeze

.PHONY: export-bundle demo
export-bundle:   ## exports trained model and calibration to extension/model_bundle.json
	$(PY) -m src.export_model

demo: export-bundle ## starts a local HTTP preview server for the Chrome extension & demo studio
	@echo "Opening BrowserShield-Pro Studio at http://localhost:8000/demo/index.html"
	$(PY) -m http.server 8000

