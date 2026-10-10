# Setup, execution and data provenance

## Verify and run without replacing saved work

The recorded propensity artifacts were trained with Python 3.12.12 and scikit-learn 1.9.1. Install the project environment once, then use the read-only default pipeline:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements-api.txt
python -m ml.run_pipeline
python -m pytest -q
```

`ml.run_pipeline` with no flags verifies current relational data, Customer 360, customer-level splits, model/feature schema, saved model predictions and stored validation/test metrics. It does not generate a new cohort, tune thresholds, train models or rewrite artifacts. Saved artifacts were tested with an allclose tolerance of rtol=1e-10 and atol=1e-12 for floating-point predictions/metrics; counts and confusion matrices compare exactly.

Launch backend in a second terminal (`LLM_ENABLED=false uvicorn backend.app:app --reload`) and frontend from `frontend/` (`npm ci && npm run dev`). The frontend defaults to C002056; search for C000042 to demonstrate an existing EV with no replacement use case. See [demo script](demo_script.md).

## Explicit cohort regeneration and retraining

Regeneration is intentionally explicit because it replaces current generated tables, feature data, saved model artifacts and evaluation reports. Before doing this, preserve an external backup. To intentionally rebuild from synthetic inputs:

```bash
python -m ml.run_pipeline --regenerate-data --rebuild-features --retrain-models --confirm-overwrite
```

To use the optional historical demand profile, add `--london-summary data/processed/london_summary_profile.csv`. That profile informs synthetic demand variability only. The model-retraining path selects thresholds on validation and produces a single held-out threshold report; do not repeatedly tune against held-out test results. No retraining was needed for the current integration work.

Other explicit actions: `--rebuild-features --retrain-models --confirm-overwrite` rebuilds from existing relational data; `--retrain-models --confirm-overwrite` retrains on existing Customer 360; `--refresh-metrics` only renders the default 0.5-threshold evaluation report. Do not use `ml.evaluate_thresholds` on the existing held-out set again; its saved report is the final one.

## Low Carbon London source and processing notes

Raw files are optional and ignored by Git at `data/external/`. The local directory contains 168 CSV files totaling roughly 8 GB. A bounded five-row inspection of one split confirmed headers `LCLid`, `stdorToU`, `DateTime`, and `KWH/hh (per half hour) ` (trailing space); sampled timestamps were strings like `2012-10-12 00:30:00.0000000`; the reading is kWh for the preceding half-hour. The existing aggregate `lcl_household_features.csv` has 5,561 meter IDs, annualized `electricity_kwh_year`, `observed_kwh` and `readings_count`. It was built from valid nonnegative numeric interval readings and annualized as mean reading × 48 × 365. Its method does not prove distinct, complete calendar days or de-duplicate meter/timestamps.

`london_summary_proxy.csv` uses `readings_count // 48` as an approximate coverage-days count. This is **not** a verified complete-day count. The separately generated `london_summary_profile.csv` keeps that proxy explicit and labels `electricity_kwh_year / 365` as an annualized daily average. It does not read or reprocess the 8 GB raw files. The current synthetic cohort records the legacy proxy as its demand-profile input; existing customer/model artifacts have been preserved. Historical energy data carries no bank identity or product outcomes.

The dataset is the “SmartMeter Energy Consumption Data in London Households” / Low Carbon London material, describing UK Power Networks' trial from Nov 2011 to Feb 2014. The [National Data Library listing](https://www.data.gov.uk/dataset/df8e55d4-c6d0-498e-abd8-f4c678766cbe/smartmeter-energy-consumption-data-in-london-households1) gives the publisher as Greater London Authority and shows the licence as “Not set”. The project's acquisition copy contains no license/readme. Attribute the UK Power Networks Low Carbon London project and Greater London Authority listing; confirm the license attached to the exact download before redistributing raw/derived data. Do not commit the local raw files.

## Environment and secrets

`requirements-ml.lock.txt` pins the ML runtime; `requirements-api.lock.txt` freezes the installed API+ML runtime. Use `requirements-api.txt` for setup. Node package versions are locked by `frontend/package-lock.json`. `.env.example` is the configuration template. API keys belong in server-side environment variables only; leave `LLM_ENABLED=false` for a deterministic offline demo.
