# GreenLens AI — Lloyds Green Customer Insights Platform

GreenLens is a synthetic-data hackathon prototype for the four mandatory Lloyds PS1 opportunities: GP01 EV Finance, GP02 Green Home Loan, GP03 Solar Finance and GP04 Paperless Banking. Its React customer and business dashboards call a FastAPI backend, which loads the saved ML pipelines, applies separate use-case screens, calculates deterministic sustainability scenarios and returns constrained explanations.

All customers, bank activity and product take-up labels are fictional. Propensity is a simulated-outcome model estimate; the validation-selected threshold is only a statistical prioritization signal. Neither establishes product eligibility, affordability or credit approval. Carbon values are conditional annual operating scenarios, not promised savings or financed-emissions accounting.

## Run the existing project

Python 3.12 is the artifact runtime recorded by the saved models. `requirements-ml.txt` pins scikit-learn 1.9.1 to match the serialized pipelines. The default pipeline is read-only: it verifies the checked-in/current cohort and saved artifacts and does not regenerate data or fit models.

```bash
uv sync
uv run python -m ml.run_pipeline
uv run pytest -q tests
```

Start the API and UI in separate terminals:

```bash
LLM_ENABLED=false uv run uvicorn backend.app:app --reload
```

```bash
cd frontend
npm ci
npm run dev
```

Open the Vite URL (normally `http://localhost:5173`). The API docs are at `http://localhost:8000/docs`. The UI opens to synthetic customer C002056, an EV-finance demo; search for C000042 to show an existing-EV/no-replacement exclusion. The business view supports product and validation-threshold filtering and customer drill-down. `.env.example` documents optional provider and API configuration; keep keys on the backend.

## Reproduction and artifacts

Use the installed `.venv` for the recorded model artifacts. `python -m ml.run_pipeline` audits saved CSVs, split IDs, feature schema, metrics and model reloads. To intentionally regenerate a cohort or replace trained models, use the explicit flags shown in [reproduction guide](docs/reproduction.md); existing files require `--confirm-overwrite`. A new cohort also requires a model retrain so data and model artifacts stay aligned. The default command does not run threshold tuning against the held-out set.

Core paths: relational synthetic data in `data/synthetic/`; Customer 360 and split IDs in `data/processed/`; saved models in `ml/models/`; metrics and held-out predictions in `ml/reports/`; backend modules in `backend/`; React source in `frontend/`. The 8 GB historical meter files under `data/external/` are optional local inputs and are ignored by Git. Do not commit the raw data or backup artifact directories.

See [evaluation report](docs/model_evaluation.md), [architecture](docs/architecture.md), [sustainability method](docs/sustainability_methodology.md), [responsible-AI notes](docs/responsible_ai.md), and [three-minute demo](docs/demo_script.md). The source brief is [deliverables/M1.pdf](deliverables/M1.pdf).
