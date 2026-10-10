
import json
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score
from ml.common import DATA, MODELS, REPORTS, FEATURES, TARGETS
import joblib

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

    results = {}

    for pid, target in TARGETS.items():
        model = joblib.load(MODELS / f"{pid}.joblib")

        validation_ids = splits["validation"]
        X_val = features.loc[validation_ids, FEATURES]
        y_val = labels.loc[validation_ids, target]

        probabilities = model.predict_proba(X_val)[:, 1]

        candidates = []

        for threshold in np.arange(0.05, 0.96, 0.01):
            predictions = probabilities >= threshold

            candidates.append({
                "threshold": round(float(threshold), 3),
                "precision": float(precision_score(
                    y_val, predictions, zero_division=0
                )),
                "recall": float(recall_score(
                    y_val, predictions, zero_division=0
                )),
                "f1": float(f1_score(
                    y_val, predictions, zero_division=0
                ))
            })

        best = max(candidates, key=lambda x: x["f1"])
        results[pid] = best

        print(f"\n{pid}")
        print("Best validation threshold:", best["threshold"])
        print("Validation precision:", round(best["precision"], 4))
        print("Validation recall:", round(best["recall"], 4))
        print("Validation F1:", round(best["f1"], 4))

    with open(REPORTS / "selected_thresholds.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
