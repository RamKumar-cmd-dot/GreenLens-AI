# GreenLens project map

This is a project map rather than a generated exhaustive listing. Raw external inputs, model backups and generated backups are preserved locally and excluded by `.gitignore`.

| Area | Key files | Purpose |
|---|---|---|
| Team approach | `deliverables/M1.pdf` | Two-page M1 concept and testing plan; the full official Lloyds PS1 brief is not present |
| Synthetic data | `data/generate_synthetic.py`; `data/synthetic/*.csv`; `data/synthetic/metadata.json` | Seeded relational cohort and simulated adoption targets |
| Historical electricity | `data/process_lcl.py`; `data/process_london_energy.py`; `data/prepare_london_summary.py`; `data/processed/lcl_household_features.csv`; `data/processed/london_summary_profile.csv` | Optional chunked source summarization, inspect-first processing and explicitly labelled annualized/coverage proxy |
| Customer 360 | `ml/feature_engineering.py`; `data/processed/customer_360.csv`; `data/processed/splits.json`; `data/schemas/` | Pre-cutoff customer features, split IDs and versioned schemas/catalogue |
| ML models | `ml/transaction_classifier.py`; `ml/propensity_models.py`; `ml/inference.py`; `ml/eligibility.py`; `ml/models/*.joblib`; `ml/models/metadata.json` | Reusable classifier, four propensity pipelines, screening and serialized artifacts |
| Evaluation | `ml/evaluate.py`; `ml/evaluate_rule_baselines.py`; `ml/evaluate_merchant_holdout.py`; `ml/verify_artifacts.py`; `ml/reports/*.json`; `ml/reports/*predictions.csv`; `ml/reports/selected_thresholds.json`; `ml/reports/threshold_test_metrics.json` | Model validation, no-fit heuristic comparison, merchant-held-out diagnostic, reload audit and final threshold report |
| Backend | `backend/app.py`; `backend/store.py`; `backend/recommendations.py`; `backend/eligibility.py`; `backend/impact.py`; `backend/explanations.py`; `backend/business.py`; `backend/schemas.py` | FastAPI endpoints, SQLite snapshot, product screens, scenario reruns, deterministic impact, structured explanations and summaries |
| Frontend | `frontend/src/`; `frontend/tests/App.test.jsx`; `frontend/vite.config.js`; `frontend/package-lock.json` | React/Vite customer and business views, live API integration, tests/build |
| Tests | `tests/test_data.py`; `tests/test_ml.py`; `tests/integration/*` | Data, model, API, eligibility, carbon and explanation checks |
| Documentation | `README.md`; `docs/architecture.md`; `docs/model_evaluation.md`; `docs/sustainability_methodology.md`; `docs/responsible_ai.md`; `docs/llm_methodology.md`; `docs/audit_resolution_checklist.md`; `docs/demo_script.md`; `docs/submission_checklist.md`; `docs/reproduction.md` | Runtime, architecture, methods, responsible AI, audit traceability, demo and submission status |
| Visual QA | `docs/screenshots/customer-dashboard.png`; `docs/screenshots/ev-exclusion.png`; `docs/screenshots/business-dashboard.png` | Browser captures from the local synthetic prototype |

The root `requirements-api.txt` includes the pinned model-compatible requirements in `requirements-ml.txt`; matching resolved versions are recorded in `requirements-api.lock.txt` and `requirements-ml.lock.txt`. `.env.example` holds names and local defaults only.
