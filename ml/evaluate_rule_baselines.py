"""Evaluate predeclared, explainable screening heuristics without model retraining."""

import json
import pandas as pd
from ml.common import DATA, REPORTS, MODELS, FEATURES, TARGETS, save_json
from ml.evaluate import binary_metrics
import joblib


def rule_scores(frame):
    return {
        "GP01": (
            (frame.vehicle_ownership == 1)
            & frame.vehicle_type.isin(["petrol", "diesel"])
            & (
                (frame.mean_monthly_fuel >= 100)
                | (frame.annual_mileage_estimate >= 10000)
            )
        ).astype(float),
        "GP02": ((frame.homeowner == 1) & (frame.gas_kwh_year >= 12000)).astype(float),
        "GP03": (
            (frame.homeowner == 1)
            & (frame.roof_suitable == 1)
            & (frame.electricity_kwh_year >= 4000)
        ).astype(float),
        "GP04": (
            (frame.paper_statements_enabled == 1) & (frame.digital_logins_month >= 15)
        ).astype(float),
    }


def main():
    features = pd.read_csv(DATA / "processed/customer_360.csv").set_index("customer_id")
    labels = pd.read_csv(DATA / "synthetic/product_takeup_labels.csv").set_index(
        "customer_id"
    )
    splits = json.loads((DATA / "processed/splits.json").read_text())
    results = {
        "evaluation": "Predeclared domain heuristics; no fitting or threshold tuning; customer-level saved splits; synthetic outcomes only.",
        "products": {},
    }
    for pid, target in TARGETS.items():
        model = joblib.load(MODELS / f"{pid}.joblib")
        results["products"][pid] = {}
        for split in ["validation", "test"]:
            ids = splits[split]
            x = features.loc[ids]
            y = labels.loc[ids, target].to_numpy()
            model_score = model.predict_proba(x[FEATURES])[:, 1]
            heuristic = rule_scores(x)[pid].to_numpy()
            results["products"][pid][split] = {
                "selected_model": binary_metrics(y, model_score),
                "rule_heuristic": binary_metrics(y, heuristic),
            }
    save_json(REPORTS / "rule_baseline_metrics.json", results)
    print(
        "Saved predeclared heuristic comparison to ml/reports/rule_baseline_metrics.json"
    )


if __name__ == "__main__":
    main()
