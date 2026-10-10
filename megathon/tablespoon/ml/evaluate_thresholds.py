
import json
import joblib
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score
from ml.common import DATA, MODELS, REPORTS, FEATURES, TARGETS

def main():
    features = pd.read_csv(
        DATA / "processed/customer_360.csv"
    ).set_index("customer_id")

    labels = pd.read_csv(
        DATA / "synthetic/product_takeup_labels.csv"
    ).set_index("customer_id")

    splits = json.loads(
        (DATA / "processed/splits.json").read_text()
    )

    thresholds = json.loads(
        (REPORTS / "selected_thresholds.json").read_text()
    )

    results = {}

    for pid, target in TARGETS.items():
        model = joblib.load(MODELS / f"{pid}.joblib")

        ids = splits["test"]
        X = features.loc[ids, FEATURES]
        y = labels.loc[ids, target]

        probabilities = model.predict_proba(X)[:, 1]

        threshold = thresholds[pid]["threshold"]

        old_predictions = probabilities >= 0.50
        new_predictions = probabilities >= threshold

        def metrics(pred):
            return {
                "precision": float(precision_score(
                    y, pred, zero_division=0
                )),
                "recall": float(recall_score(
                    y, pred, zero_division=0
                )),
                "f1": float(f1_score(
                    y, pred, zero_division=0
                )),
                "flagged": int(pred.sum())
            }

        old = metrics(old_predictions)
        new = metrics(new_predictions)

        results[pid] = {
            "threshold": threshold,
            "original": old,
            "tuned": new
        }

        print(f"\n{pid} (threshold={threshold})")
        print(
            f"Original: F1={old['f1']:.4f}, "
            f"Precision={old['precision']:.4f}, "
            f"Recall={old['recall']:.4f}"
        )
        print(
            f"Tuned:    F1={new['f1']:.4f}, "
            f"Precision={new['precision']:.4f}, "
            f"Recall={new['recall']:.4f}"
        )
        print("Customers flagged:", new["flagged"])

    with open(REPORTS / "threshold_test_metrics.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
