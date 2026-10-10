# Created file inventory
Existing README.md is preserved. All paths below are relative to the repository root. Runtime .venv and cache files are excluded.

| File | Purpose |
|---|---|
| `.gitignore` | Exclude runtime environment, caches and raw files |
| `requirements-ml.txt` | Direct dependency ranges |
| `requirements-ml.lock.txt` | Exact executed dependency versions |
| `data/__init__.py` | Python package marker |
| `data/generate_synthetic.py` | Seeded relational data and probabilistic outcome generation; optional demand-profile variation |
| `data/process_london_energy.py` | Inspect-first bounded CSV/ZIP electricity preprocessing |
| `data/processed/customer_360.csv` | Unified customer features |
| `data/processed/splits.json` | Explicit train/validation/test customer IDs |
| `data/schemas/feature_schema.json` | Ordered numeric/categorical model contract |
| `data/schemas/product_catalogue.json` | Mandatory product purposes |
| `data/schemas/relational_schema.json` | CSV column schemas and keys |
| `data/synthetic/customer_assets.csv` | Generated fictional relational table; fields documented in data_dictionary.md |
| `data/synthetic/customer_behaviour.csv` | Generated fictional relational table; fields documented in data_dictionary.md |
| `data/synthetic/customer_products.csv` | Generated fictional relational table; fields documented in data_dictionary.md |
| `data/synthetic/customers.csv` | Generated fictional relational table; fields documented in data_dictionary.md |
| `data/synthetic/metadata.json` | Generation provenance/prevalence |
| `data/synthetic/product_takeup_labels.csv` | Generated fictional relational table; fields documented in data_dictionary.md |
| `data/synthetic/transactions.csv` | Generated fictional relational table; fields documented in data_dictionary.md |
| `docs/backend_example.py` | Backend adapter/import guidance |
| `docs/data_dictionary.md` | Table and feature definitions |
| `docs/ml_methodology.md` | Model, reliability, taxonomy and integration contracts |
| `docs/reproduction.md` | Commands and optional historical processing |
| `docs/synthetic_methodology.md` | Generation equations, assumptions and limitations |
| `ml/__init__.py` | Python package marker |
| `ml/common.py` | Paths, seed, categories, feature and target contracts |
| `ml/eligibility.py` | Product purposes and explicit use-case exclusions |
| `ml/evaluate.py` | Binary metrics and readable comparison report |
| `ml/feature_engineering.py` | Pre-cutoff Customer 360 aggregation |
| `ml/inference.py` | JSON-safe cached model loading, customer/product/transaction inference |
| `ml/models/GP01.joblib` | Saved fitted preprocessing/classifier pipeline |
| `ml/models/GP02.joblib` | Saved fitted preprocessing/classifier pipeline |
| `ml/models/GP03.joblib` | Saved fitted preprocessing/classifier pipeline |
| `ml/models/GP04.joblib` | Saved fitted preprocessing/classifier pipeline |
| `ml/models/metadata.json` | Model version, runtime versions, feature schema and reliability metadata |
| `ml/models/transaction_classifier.joblib` | Saved fitted preprocessing/classifier pipeline |
| `ml/propensity_models.py` | Customer splits, train-only preprocessing, baseline/candidate selection and artifacts |
| `ml/reports/GP01.json` | Train distribution, validation/test candidate and baseline metrics, selection rationale |
| `ml/reports/GP01_test_predictions.csv` | Held-out predictions with true labels and customer identifiers |
| `ml/reports/GP02.json` | Train distribution, validation/test candidate and baseline metrics, selection rationale |
| `ml/reports/GP02_test_predictions.csv` | Held-out predictions with true labels and customer identifiers |
| `ml/reports/GP03.json` | Train distribution, validation/test candidate and baseline metrics, selection rationale |
| `ml/reports/GP03_test_predictions.csv` | Held-out predictions with true labels and customer identifiers |
| `ml/reports/GP04.json` | Train distribution, validation/test candidate and baseline metrics, selection rationale |
| `ml/reports/GP04_test_predictions.csv` | Held-out predictions with true labels and customer identifiers |
| `ml/reports/evaluation.md` | Readable validation/test comparisons |
| `ml/reports/sample_response.json` | Complete four-product example for C000025 |
| `ml/reports/test_results.txt` | Actual pytest execution results |
| `ml/reports/transaction_evaluation.md` | Readable transaction classifier/baseline results |
| `ml/reports/transaction_metrics.json` | Per-category reports and confusion matrices |
| `ml/reports/transaction_test_predictions.csv` | Held-out predictions with true labels and customer identifiers |
| `ml/run_pipeline.py` | One-command artifact regeneration |
| `ml/transaction_classifier.py` | Rule baseline and TF-IDF logistic classifier |
| `tests/test_data.py` | Relational integrity, splits, leakage and generator reproducibility tests |
| `tests/test_ml.py` | Inference, exclusion, reload, training reproducibility and interval-summary tests |
| `docs/file_inventory.md` | This complete deliverable inventory |
