# Resume checklist — 11 October 2026

## Verified current state

- 5,000 synthetic customers, 368,323 transactions, six relational CSV tables, Customer 360 features and pre-cutoff splits are present.
- Split sizes are 3,500/750/750; customer IDs are disjoint. No orphan customer references or target columns in Customer 360 were found.
- Four saved propensity models and the transaction classifier load without retraining. Full reports compare with exact counts/confusion matrices and rtol=1e-10 / atol=1e-12 numeric tolerance. Saved training imputers match train-only medians.
- Inference consumes `ml/reports/selected_thresholds.json` and returns both continuous propensity and `threshold_screen`. Eligibility remains independent. Missing values, unknown categories, product exclusions and serialized outputs are exercised by tests.
- API, SQLite snapshot, four product responses, business summaries, sourced London solar scenarios, other-region solar unavailability, annual portfolio energy/digital metrics, monthly spending trends, scenario reruns and constrained explanation fallback work together.
- Historical LCL summaries are available. `complete_days` in the preserved legacy summary remains a coverage proxy, not verified complete calendar days; the newly named profile avoids that implication. Raw 8 GB files remain excluded from Git.
- Existing screenshots in `docs/screenshots/` come from the actual local app but predate the new trend/scenario sections; capture fresh screenshots for final judging materials.

## Last checks

```text
.venv/bin/python -m ml.evaluate_rule_baselines       PASS (saved models loaded, no fitting)
.venv/bin/python -m ml.evaluate_merchant_holdout     PASS (diagnostic only; shipped model unchanged)
.venv/bin/python -m ml.verify_artifacts               PASS (saved metrics reproduced; no model fitting)
.venv/bin/python -m backend.evaluate_explanations   PASS (28/28 offline guardrail checks)
.venv/bin/python -m backend.smoke_check             PASS (10 live GETs plus scenario/classifier/exclusion/error checks)
.venv/bin/python -m pytest -q tests                  PASS (51 tests)
cd frontend && node_modules/.bin/vitest run --config vite.config.js PASS (6 tests)
cd frontend && node_modules/.bin/vite build                         PASS
```

The project root is the home directory, so test commands must be scoped to `tests/` and frontend commands run from `frontend/`. Bare pytest discovery otherwise enters unrelated personal folders. `pyproject.toml` now limits discovery to the project's tests.

## Remaining before judging/submission

- Confirm the license attached to the exact downloaded Low Carbon London distribution; the National Data Library record currently shows no license, and the acquisition directory has no license file.
- If live provider explanations are required, run a smoke check with a valid server-side OpenAI key; the deterministic fallback and 28 offline allow-list guardrails pass. The current LLM integration selects approved wording rather than generating new prose. Do not report offline cases as live model accuracy.
- The solar demonstration is a documented London reference scenario; other coarse regions remain UNAVAILABLE until site-specific yield data is supplied. Paperless impact reports pages only because a credible statement lifecycle factor is absent.
- At the venue, use a fresh local terminal pair and run the commands in README; default to LLM disabled if provider connectivity is uncertain.
- Do not regenerate the current cohort or retrain the current models for the demo. `python -m ml.run_pipeline` without flags is a read-only audit. Explicit replacements require `--confirm-overwrite`.
- Do not stage/commit broad paths. This project directory sits under a home-level Git root; preserve the cohort/model artifacts and exclude unrelated home files, `data/external/`, `data/synthetic_backup/`, `ml/models_backup/` and `ml/reports_backup/`.
