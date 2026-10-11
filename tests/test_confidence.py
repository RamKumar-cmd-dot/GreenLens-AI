import json

import numpy as np
import pandas as pd

from ml.common import DATA, FEATURES, TARGETS
from ml.confidence import PRODUCT_INPUTS, assess_reliability, build_reference
from ml.inference import load_models, normalize, predict_opportunities
from ml.eligibility import screen


def customer_features():
    frame = pd.read_csv(DATA / "processed/customer_360.csv")
    return normalize(frame.iloc[0].to_dict())


def reference():
    return build_reference()


def test_reference_uses_training_only_and_has_validation_calibration():
    ref = reference()
    assert ref["distribution_reference_split"] == "train only"
    assert ref["training_customer_count"] == 3500
    assert ref["validation_customer_count"] == 750
    for pid in TARGETS:
        assert ref["products"][pid]["validation"]["bins"]
        assert ref["products"][pid]["numeric_bounds"]


def test_complete_typical_customer_and_deterministic_json():
    f = customer_features()
    ref = reference()
    first = assess_reliability("GP01", f, 0.18, ref)
    second = assess_reliability("GP01", f, 0.18, ref)
    assert first == second
    assert first["reliability"]["feature_completeness"] == "high"
    assert first["reliability"]["distribution_familiarity"] in {"high", "medium"}
    assert first["confidence"] is None
    assert first["confidence_level"] in {"high", "medium", "low", "unavailable"}
    json.dumps(first, allow_nan=False)


def test_one_supporting_missing_is_distinguished_from_critical_missing():
    ref = reference()
    f = customer_features()
    f["annual_mileage_estimate"] = np.nan
    result = assess_reliability("GP01", f, 0.18, ref)
    assert result["reliability"]["feature_completeness"] == "medium"
    assert "SUPPORTING_FEATURES_MISSING" in result["reliability"]["reason_codes"]
    f["vehicle_type"] = np.nan
    result = assess_reliability("GP01", f, 0.18, ref)
    assert result["reliability"]["feature_completeness"] == "low"
    assert "IMPORTANT_FEATURES_MISSING" in result["reliability"]["reason_codes"]


def test_multiple_missing_unseen_category_and_extreme_numeric_are_flagged():
    ref = reference()
    f = customer_features()
    f["region"] = "unseen_region"
    result = assess_reliability("GP03", f, 0.05, ref)
    assert "UNSEEN_CATEGORICAL_VALUE" in result["reliability"]["reason_codes"]
    f["electricity_kwh_year"] = 1_000_000
    result = assess_reliability("GP03", f, 0.05, ref)
    assert "NUMERIC_FEATURE_OUTSIDE_TRAINING_RANGE" in result["reliability"]["reason_codes"]
    f["homeowner"] = np.nan
    f["roof_suitable"] = np.nan
    result = assess_reliability("GP03", f, 0.05, ref)
    assert result["reliability"]["feature_completeness"] == "low"


def test_conflicting_data_degrades_reliability_without_changing_eligibility_or_propensity():
    base = customer_features()
    features = {**base, "customer_id": "confidence-test", "owns_ev": 1, "vehicle_type": "petrol", "vehicle_ownership": 1}
    before = dict(features)
    rows = predict_opportunities(features)["opportunities"]
    ev = next(row for row in rows if row["product_id"] == "GP01")
    models = load_models()
    expected_propensity = float(models["GP01"].predict_proba(pd.DataFrame([normalize(features)], columns=FEATURES))[0, 1])
    assert ev["propensity"] == expected_propensity
    assert features == before
    assert ev["eligibility"] == screen("GP01", normalize(features))
    assert "CONFLICTING_CUSTOMER_INFORMATION" in ev["reliability"]["reason_codes"]
    assert ev["confidence_level"] in {"low", "medium", "unavailable"}


def test_all_missing_and_four_product_output_contract():
    result = predict_opportunities({"customer_id": "all-missing"})
    assert {row["product_id"] for row in result["opportunities"]} == set(TARGETS)
    assert all(row["confidence"] is None for row in result["opportunities"])
    assert all(row["confidence_level"] == "unavailable" for row in result["opportunities"])
    assert all("NO_PRODUCT_RELEVANT_FEATURES_AVAILABLE" in row["reliability"]["reason_codes"] for row in result["opportunities"])
    json.dumps(result, allow_nan=False)


def test_reliability_map_matches_four_product_input_contract():
    assert set(PRODUCT_INPUTS) == set(TARGETS)
    assert all(group["critical"] and group["supporting"] for group in PRODUCT_INPUTS.values())
