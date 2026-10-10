# Resume checklist — 11 October 2026

## Verified current state

- 5,000 synthetic customers, 368,323 transactions, six relational CSV tables, Customer 360 features and pre-cutoff splits are present.
- Split sizes are 3,500/750/750; customer IDs are disjoint. No orphan customer references or target columns in Customer 360 were found.
- Four saved propensity models and the transaction classifier load without retraining. Full reports compare with exact counts/confusion matrices and rtol=1e-10 / atol=1e-12 numeric tolerance. Saved training imputers match train-only medians.
- Inference consumes `ml/reports/selected_thresholds.json` and returns both continuous propensity and `threshold_screen`. Eligibility remains independent. Missing values, unknown categories, product exclusions and serialized outputs are exercised by tests.
- API, SQLite snapshot, four product responses, business summaries, emissions scenarios and constrained explanation fallback work together. Local HTTP/browser smoke checked C002056, C000042, all four product cards, business aggregate, threshold filter and drill-down.
- Historical LCL summaries are available. `complete_days` in the preserved legacy summary remains a coverage proxy, not verified complete calendar days; the newly named profile avoids that implication. Raw 8 GB files remain excluded from Git.
- The generated browser screenshots in `docs/screenshots/` are from the actual local app and saved models.

## Last checks

```text
python -m ml.run_pipeline                  PASS (read-only; no model fitting)
python -m backend.evaluate_explanations    PASS (24/24 offline guardrail cases)
python -m pytest -q                        PASS (49 tests)
npm test -- --run                          PASS (5 tests)
npm run build                              PASS
```

The Python suite needs to run outside this restricted desktop sandbox because its sandbox prevents cross-thread asyncio event-loop wakeups used by FastAPI TestClient. The real test command completes normally on the host.

## Remaining before judging/submission

- Confirm the license attached to the exact downloaded Low Carbon London distribution; the National Data Library record currently shows no license, and the acquisition directory has no license file.
- If live provider explanations are required, run a smoke check with a valid server-side OpenAI key; the deterministic fallback and 24 offline groundedness cases already pass. Do not report offline cases as live model accuracy.
- At the venue, use a fresh local terminal pair and run the commands in README; default to LLM disabled if provider connectivity is uncertain.
- Do not regenerate the current cohort or retrain the current models for the demo. `python -m ml.run_pipeline` without flags is a read-only audit. Explicit replacements require `--confirm-overwrite`.
- Do not stage/commit broad paths. This project directory sits under a home-level Git root; preserve the uncommitted cohort/model artifacts and exclude `data/external/`, `data/synthetic_backup/`, `ml/models_backup/` and `ml/reports_backup/`.
