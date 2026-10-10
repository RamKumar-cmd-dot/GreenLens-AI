# Reproduce
From repository root, Python 3.11+ recommended (executed environment recorded in ml/models/metadata.json):
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-ml.txt
python -m data.generate_synthetic --customers 5000 --seed 42
python -m ml.feature_engineering
python -m ml.propensity_models
python -m ml.transaction_classifier
python -m ml.evaluate
python -m ml.inference
python -m pytest -q
```
requirements-ml.lock.txt records the executed environment for stricter reproduction. Scripts overwrite only their generated data/ML artifacts. Run from repo root; inference paths resolve relative to the package. For a changed cohort, regenerate all downstream artifacts. Tests use the required default 5,000-customer cohort. Never put confidential banking records under data/raw.

Optional London inspection (no download required for the main pipeline):
```bash
python -m data.process_london_energy /path/to/file.csv
```
For ZIP, select an actual member with --member. After inspecting the emitted schema and checking source documentation, rerun with --id-column, --timestamp-column, --reading-column, --timestamp-format, --unit kWh_per_interval, --interval-minutes, and --source-url. Defaults to at most one million rows and 50,000-row chunks; only that bounded sample is materialized. Process individual split files separately; cross-file full-history aggregation is not implemented. Partial days are not extrapolated. Output is a compact per-meter summary plus provenance. No raw dataset was available or processed during this implementation.

To opt into an inspected/processed historical demand variability profile, use `python -m data.generate_synthetic --london-summary data/processed/london_household_summary.csv`, then rebuild all downstream artifacts. The default cohort is independent of London data.

Alternatively `python -m ml.run_pipeline` performs all generation/training/report steps and emits feature-schema and catalogue JSON. Run pytest afterward. Generated artifacts remain on disk for the backend.
