import platform
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from ml.common import *
from ml.evaluate import binary_metrics


def split_customers(ids, seed=SEED):
    train, hold = train_test_split(sorted(ids), test_size=0.3, random_state=seed)
    val, test = train_test_split(hold, test_size=0.5, random_state=seed)
    return {"train": train, "validation": val, "test": test}


def pipeline(kind, seed=SEED):
    prep = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        (
                            "impute",
                            SimpleImputer(
                                strategy="median",
                                add_indicator=True,
                                keep_empty_features=True,
                            ),
                        ),
                        ("scale", StandardScaler()),
                    ]
                ),
                NUMERIC,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        (
                            "impute",
                            SimpleImputer(
                                strategy="most_frequent", keep_empty_features=True
                            ),
                        ),
                        (
                            "encode",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                CATEGORICAL,
            ),
        ]
    )
    model = (
        LogisticRegression(max_iter=1200, random_state=seed)
        if kind == "logistic"
        else RandomForestClassifier(
            n_estimators=120,
            min_samples_leaf=20,
            max_depth=8,
            n_jobs=-1,
            random_state=seed,
        )
    )
    return Pipeline([("preprocess", prep), ("model", model)])


def train(seed=SEED):
    df = (
        pd.read_csv(DATA / "processed/customer_360.csv")
        .merge(
            pd.read_csv(DATA / "synthetic/product_takeup_labels.csv"),
            on="customer_id",
            validate="one_to_one",
        )
        .set_index("customer_id")
    )
    splits = split_customers(df.index, seed)
    save_json(DATA / "processed/splits.json", splits)
    metadata = {
        "version": VERSION,
        "seed": seed,
        "as_of": AS_OF,
        "python": platform.python_version(),
        "sklearn": sklearn.__version__,
        "features": FEATURES,
        "products": {},
    }
    for pid, target in TARGETS.items():
        subsets = {k: df.loc[v] for k, v in splits.items()}
        tr = subsets["train"]
        fitted = {}
        report = {
            "train": {
                "n": len(tr),
                "positives": int(tr[target].sum()),
                "negatives": int((1 - tr[target]).sum()),
            },
            "validation": {},
            "test": {},
        }
        if tr[target].nunique() != 2:
            raise ValueError(f"{pid} needs both classes; increase cohort size")
        for kind in ["logistic", "random_forest"]:
            fitted[kind] = pipeline(kind, seed).fit(tr[FEATURES], tr[target])
            val = subsets["validation"]
            report["validation"][kind] = binary_metrics(
                val[target], fitted[kind].predict_proba(val[FEATURES])[:, 1]
            )
        chosen = min(fitted, key=lambda k: report["validation"][k]["brier"])
        for split in ["validation", "test"]:
            s = subsets[split]
            report[split]["constant_prevalence"] = binary_metrics(
                s[target], np.full(len(s), tr[target].mean())
            )
            if split == "test":
                for kind, model in fitted.items():
                    report[split][kind] = binary_metrics(
                        s[target], model.predict_proba(s[FEATURES])[:, 1]
                    )
        model = fitted[chosen]
        joblib.dump(model, MODELS / f"{pid}.joblib")
        te = subsets["test"]
        pd.DataFrame(
            {
                "customer_id": te.index,
                "actual": te[target].values,
                "propensity": model.predict_proba(te[FEATURES])[:, 1],
            }
        ).to_csv(REPORTS / f"{pid}_test_predictions.csv", index=False)
        report["selected"] = chosen
        report["selection"] = (
            "lowest validation Brier; held-out test never used for selection"
        )
        save_json(REPORTS / f"{pid}.json", report)
        metadata["products"][pid] = {
            "target": target,
            "selected": chosen,
            "probability_status": "uncalibrated model estimate of simulated take-up",
            "validation_brier": report["validation"][chosen]["brier"],
            "validation_ece": report["validation"][chosen]["ece"],
            "training_prevalence": float(tr[target].mean()),
        }
    save_json(MODELS / "metadata.json", metadata)
    print("Saved four propensity pipelines and evaluation artifacts")


if __name__ == "__main__":
    train()
