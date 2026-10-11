"""Read-only integrity and serialization audit; never fits or overwrites models."""

import json
import joblib
import numpy as np
import pandas as pd
from ml.common import (
    DATA,
    MODELS,
    REPORTS,
    FEATURES,
    NUMERIC,
    TARGETS,
    CATEGORIES,
    AS_OF,
    VERSION,
    save_json,
)
from ml.evaluate import binary_metrics
from ml.inference import load_models, predict_opportunities

FLOAT_ATOL = 1e-12
FLOAT_RTOL = 1e-10


def compare_metrics(actual, expected, context):
    """Compare complete metric payloads with exact counts and tolerant floats."""
    assert isinstance(actual, dict) and isinstance(expected, dict), context
    assert set(actual) == set(expected), f"{context}: metric fields differ"
    for key in actual:
        a, e = actual[key], expected[key]
        label = f"{context}.{key}"
        if key == "calibration_bins":
            assert (
                isinstance(a, list) and isinstance(e, list) and len(a) == len(e)
            ), label
            for index, (ab, eb) in enumerate(zip(a, e)):
                assert (
                    set(ab)
                    == set(eb)
                    == {"lower", "n", "mean_probability", "observed_rate"}
                ), f"{label}[{index}] fields"
                assert (
                    type(ab["n"]) is int and type(eb["n"]) is int and ab["n"] == eb["n"]
                ), f"{label}[{index}].n"
                for field in ("lower", "mean_probability", "observed_rate"):
                    np.testing.assert_allclose(
                        ab[field],
                        eb[field],
                        rtol=FLOAT_RTOL,
                        atol=FLOAT_ATOL,
                        err_msg=f"{label}[{index}].{field}",
                    )
        elif key == "confusion_matrix":
            np.testing.assert_array_equal(a, e, err_msg=label)
        elif a is None or e is None:
            assert a is None and e is None, label
        elif isinstance(a, (float, np.floating)):
            assert isinstance(e, (int, float)), label
            np.testing.assert_allclose(
                a, e, rtol=FLOAT_RTOL, atol=FLOAT_ATOL, err_msg=label
            )
        else:
            assert type(a) is type(e) and a == e, label


def main():
    customers = pd.read_csv(DATA / "synthetic/customers.csv")
    ids = set(customers.customer_id)
    assert customers.customer_id.is_unique and customers.customer_id.notna().all()
    tables = {}
    for name in [
        "transactions",
        "customer_assets",
        "customer_behaviour",
        "customer_products",
        "product_takeup_labels",
    ]:
        frame = pd.read_csv(DATA / f"synthetic/{name}.csv")
        assert (
            frame.customer_id.notna().all() and set(frame.customer_id) <= ids
        ), f"Orphan customer in {name}"
        if name not in ["transactions", "customer_products"]:
            assert (
                frame.customer_id.is_unique and set(frame.customer_id) == ids
            ), f"Unexpected customer coverage in {name}"
        tables[name] = frame
    tx = tables["transactions"]
    assert tx.transaction_id.is_unique
    assert tx.sustainability_category.notna().all() and set(
        tx.sustainability_category
    ) == set(CATEGORIES)
    assert np.isfinite(tx.amount_gbp).all() and tx.amount_gbp.gt(0).all()
    assert pd.to_datetime(tx.transaction_date).lt(pd.Timestamp(AS_OF)).all()
    labels = tables["product_takeup_labels"].set_index("customer_id")
    assert (
        labels.index.is_unique
        and labels[list(TARGETS.values())].isin([0, 1]).all().all()
    )
    features = pd.read_csv(DATA / "processed/customer_360.csv").set_index("customer_id")
    assert features.index.is_unique and set(features.index) == ids
    assert not set(TARGETS.values()) & set(features.columns) and not set(
        TARGETS.values()
    ) & set(FEATURES)
    splits = json.loads((DATA / "processed/splits.json").read_text())
    assert set(splits) == {"train", "validation", "test"}
    groups = {k: set(v) for k, v in splits.items()}
    assert all(
        len(groups[k]) == len(splits[k]) for k in groups
    ), "Duplicate IDs in a split"
    assert set.union(*groups.values()) == ids, "Split coverage mismatch"
    assert not (
        groups["train"] & groups["validation"]
        or groups["train"] & groups["test"]
        or groups["validation"] & groups["test"]
    ), "Customer leakage across splits"
    models = load_models()
    assert (
        models["metadata"]["version"] == VERSION
        and models["metadata"]["features"] == FEATURES
    )
    assert set(models["thresholds"]) == set(TARGETS)
    threshold_results = json.loads(
        (REPORTS / "threshold_test_metrics.json").read_text()
    )
    assert set(threshold_results) == set(TARGETS)
    report = {
        "customers": len(customers),
        "transactions": len(tx),
        "split_counts": {k: len(v) for k, v in groups.items()},
        "overlapping_customers": 0,
        "orphan_records": 0,
        "target_columns_in_features": [],
        "products": {},
    }
    train_medians = features.loc[splits["train"], NUMERIC].median().to_numpy()
    for pid, target in TARGETS.items():
        model = models[pid]
        selected_thresholds = json.loads(
            (REPORTS / "selected_thresholds.json").read_text()
        )
        assert selected_thresholds[pid]["threshold"] == models["thresholds"][pid]
        threshold_record = threshold_results[pid]
        assert threshold_record["threshold"] == models["thresholds"][pid]
        for split_name in ("original", "tuned"):
            assert set(threshold_record[split_name]) == {
                "precision",
                "recall",
                "f1",
                "flagged",
            }
            assert type(threshold_record[split_name]["flagged"]) is int
            assert 0 <= threshold_record[split_name]["flagged"] <= len(groups["test"])
            for metric_name in ("precision", "recall", "f1"):
                metric_value = threshold_record[split_name][metric_name]
                assert np.isfinite(metric_value) and 0 <= metric_value <= 1
        assert (
            list(model.feature_names_in_) == FEATURES
        ), f"{pid} feature ordering mismatch"
        imputer = (
            model.named_steps["preprocess"]
            .named_transformers_["numeric"]
            .named_steps["impute"]
        )
        np.testing.assert_allclose(
            imputer.statistics_, train_medians, rtol=FLOAT_RTOL, atol=FLOAT_ATOL
        )
        scores = model.predict_proba(features[FEATURES])[:, 1]
        assert np.isfinite(scores).all() and ((scores >= 0) & (scores <= 1)).all()
        reloaded = joblib.load(MODELS / f"{pid}.joblib")
        np.testing.assert_allclose(
            scores,
            reloaded.predict_proba(features[FEATURES])[:, 1],
            rtol=FLOAT_RTOL,
            atol=FLOAT_ATOL,
        )
        saved = json.loads((REPORTS / f"{pid}.json").read_text())
        selected = saved.get("selected")
        assert selected in {"logistic", "random_forest"}
        verified = {}
        for split in ["validation", "test"]:
            assert (
                selected in saved[split]
            ), f"{pid} missing selected model metrics for {split}"
            subset = features.loc[splits[split], FEATURES]
            predicted = model.predict_proba(subset)[:, 1]
            actual = labels.loc[splits[split], target]
            metrics = binary_metrics(actual, predicted)
            recorded = saved[split][selected]
            compare_metrics(metrics, recorded, f"{pid}.{split}")
            verified[split] = {
                "metrics_match_saved_report": True,
                "n": metrics["n"],
                "brier": metrics["brier"],
                "roc_auc": metrics["roc_auc"],
            }
        heldout = pd.read_csv(REPORTS / f"{pid}_test_predictions.csv").set_index(
            "customer_id"
        )
        assert heldout.index.is_unique and set(heldout.index) == groups["test"]
        np.testing.assert_allclose(
            heldout.loc[splits["test"], "propensity"],
            model.predict_proba(features.loc[splits["test"], FEATURES])[:, 1],
            rtol=FLOAT_RTOL,
            atol=FLOAT_ATOL,
        )
        np.testing.assert_array_equal(
            heldout.loc[splits["test"], "actual"], labels.loc[splits["test"], target]
        )
        report["products"][pid] = {
            "selected": selected,
            "threshold": models["thresholds"][pid],
            "scored_customers": len(scores),
            "min_propensity": float(scores.min()),
            "max_propensity": float(scores.max()),
            "reload_within_tolerance": True,
            "training_imputer_verified": True,
            "verified_metrics": verified,
        }
    classifier = models["transaction"]
    assert set(classifier.classes_) == set(CATEGORIES)
    from ml.transaction_classifier import text_of

    classifier_sample = tables["transactions"].head(256)
    classifier_text = text_of(classifier_sample)
    classifier_scores = classifier.predict_proba(classifier_text)
    classifier_reload = joblib.load(MODELS / "transaction_classifier.joblib")
    np.testing.assert_allclose(
        classifier_scores,
        classifier_reload.predict_proba(classifier_text),
        rtol=FLOAT_RTOL,
        atol=FLOAT_ATOL,
    )
    np.testing.assert_array_equal(
        classifier.predict(classifier_text), classifier_reload.predict(classifier_text)
    )
    report["transaction_classifier"] = {
        "classes": sorted(classifier.classes_.tolist()),
        "reloaded_within_tolerance": True,
        "checked_transactions": len(classifier_sample),
    }
    for payload in [{}, {k: None for k in FEATURES}, {"region": "unknown_region"}]:
        result = predict_opportunities(payload)
        json.dumps(result, allow_nan=False)
        assert {p["product_id"] for p in result["opportunities"]} == set(TARGETS)
        assert all(
            0 <= p["propensity"] <= 1 and p["recommendation_status"] == "needs_review"
            for p in result["opportunities"]
        )
        assert all(
            0 <= p["threshold_screen"]["threshold"] <= 1
            for p in result["opportunities"]
        )
    report["missing_data_cases_passed"] = 3
    report["leakage_scope"] = (
        "No target fields, disjoint customer partitions, pre-cutoff transactions, training-only fitted numeric imputation; asset/behaviour snapshots rely on the documented synthetic pre-cutoff assumption."
    )
    save_json(REPORTS / "artifact_audit.json", report)
    print(json.dumps(report, indent=2))
    print(
        "All four saved pipelines reproduce their recorded validation/test metrics; no models fitted."
    )


if __name__ == "__main__":
    main()
