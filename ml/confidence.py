"""Validation-informed, per-customer reliability diagnostics.

The module deliberately returns no numerical confidence score. It combines
product-specific input coverage, training-distribution familiarity and
validation score-band support into a documented qualitative reliability tier.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.common import CATEGORICAL, DATA, FEATURES, NUMERIC, REPORTS, TARGETS
from ml.eligibility import missing


PRODUCT_INPUTS = {
    "GP01": {
        "critical": ["vehicle_ownership", "vehicle_type", "owns_ev", "replacement_intent"],
        "supporting": ["annual_mileage_estimate", "mean_monthly_fuel", "fuel_trend", "existing_vehicle_loan"],
    },
    "GP02": {
        "critical": ["homeowner", "property_type"],
        "supporting": ["electricity_kwh_year", "gas_kwh_year", "heating_technology", "existing_mortgage"],
    },
    "GP03": {
        "critical": ["homeowner", "roof_suitable"],
        "supporting": ["property_type", "electricity_kwh_year", "region", "household_size"],
    },
    "GP04": {
        "critical": ["paper_statements_enabled", "digital_logins_month"],
        "supporting": ["mobile_app_active", "digital_transaction_ratio", "age_band"],
    },
}

METHOD = "validation-informed reliability assessment v1"
LIMITATION = "Reliability evidence is evaluated only against synthetic customer and take-up data; real-customer performance is unknown."


def _wilson(successes: int, n: int) -> list[float] | None:
    if n <= 0:
        return None
    p = successes / n
    z = 1.959963984540054
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return [max(0.0, center - half), min(1.0, center + half)]


def _validation_bins(pid: str) -> list[dict[str, Any]]:
    path = REPORTS / f"{pid}.json"
    if not path.exists():
        return []
    report = json.loads(path.read_text())
    selected = report.get("selected")
    metrics = report.get("validation", {}).get(selected, {})
    result = []
    for item in metrics.get("calibration_bins", []):
        n = int(item.get("n", 0))
        rate = float(item.get("observed_rate", 0.0))
        lower = round(float(item["lower"]), 1)
        interval = _wilson(round(rate * n), n)
        result.append({
            "lower": lower,
            "upper": min(1.0, lower + 0.1),
            "n": n,
            "validation_customers": n,
            "mean_probability": float(item["mean_probability"]),
            "observed_rate": rate,
            "observed_simulated_takeup_rate": rate,
            "observed_rate_wilson_95_interval": interval,
        })
    return result


def build_reference() -> dict[str, Any]:
    """Fit distribution reference on training customers only; read validation bins as diagnostics."""
    split_path = DATA / "processed/splits.json"
    feature_path = DATA / "processed/customer_360.csv"
    if not split_path.exists() or not feature_path.exists():
        raise FileNotFoundError("Customer 360 data and saved customer splits are required")
    splits = json.loads(split_path.read_text())
    train_ids = set(splits["train"])
    val_ids = set(splits["validation"])
    test_ids = set(splits["test"])
    if train_ids & val_ids or train_ids & test_ids or val_ids & test_ids:
        raise ValueError("Customer split identifiers overlap")
    frame = pd.read_csv(feature_path).set_index("customer_id")
    train = frame.loc[frame.index.intersection(train_ids)]
    if len(train) != len(train_ids):
        raise ValueError("Some saved training customer IDs are absent from Customer 360")

    products: dict[str, Any] = {}
    for pid, groups in PRODUCT_INPUTS.items():
        relevant = groups["critical"] + groups["supporting"]
        numeric_bounds = {}
        categorical_values = {}
        missing_rates = {}
        for feature in relevant:
            values = train[feature]
            missing_rates[feature] = float(values.isna().mean())
            if feature in NUMERIC:
                valid = pd.to_numeric(values, errors="coerce").dropna()
                numeric_bounds[feature] = {
                    "lower_01": float(valid.quantile(0.01)) if len(valid) else None,
                    "upper_99": float(valid.quantile(0.99)) if len(valid) else None,
                    "training_nonmissing": int(len(valid)),
                }
            elif feature in CATEGORICAL:
                categorical_values[feature] = sorted(str(v) for v in values.dropna().unique())
        report_path = REPORTS / f"{pid}.json"
        report = json.loads(report_path.read_text()) if report_path.exists() else {}
        model_name = report.get("selected")
        validation_metrics = report.get("validation", {}).get(model_name, {})
        products[pid] = {
            **groups,
            "numeric_bounds": numeric_bounds,
            "categorical_values": categorical_values,
            "training_missing_rates": missing_rates,
            "validation": {
                "n": int(validation_metrics.get("n", 0)),
                "brier": validation_metrics.get("brier"),
                "ece": validation_metrics.get("ece"),
                "bins": _validation_bins(pid),
            },
        }
    return {
        "method": METHOD,
        "scope": "synthetic_validation_only",
        "features": FEATURES,
        "training_customer_count": len(train),
        "validation_customer_count": len(val_ids),
        "distribution_reference_split": "train only",
        "validation_calibration_split": "validation only",
        "products": products,
    }


def save_reference(path: Path | None = None) -> Path:
    path = path or REPORTS / "confidence_reference.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_reference(), indent=2, allow_nan=False) + "\n")
    return path


def _level(missing_count: int, total: int, critical_missing: int) -> str:
    if total == 0 or missing_count == total:
        return "unavailable"
    if critical_missing or missing_count >= 2:
        return "low"
    if missing_count == 1:
        return "medium"
    return "high"


def assess_reliability(pid: str, features: dict[str, Any], propensity: float,
                       reference: dict[str, Any] | None, conflicts: list[str] | None = None) -> dict[str, Any]:
    """Assess per-row reliability without changing propensity or eligibility."""
    if pid not in PRODUCT_INPUTS:
        raise ValueError(f"Unknown product: {pid}")
    if not isinstance(propensity, (int, float)) or not math.isfinite(float(propensity)) or not 0 <= propensity <= 1:
        raise ValueError("propensity must be finite and in [0, 1]")
    group = PRODUCT_INPUTS[pid]
    relevant = group["critical"] + group["supporting"]
    codes: list[str] = []
    details: dict[str, Any] = {"missing_features": [], "numeric_out_of_range": {}, "unseen_categories": {}}
    observed = [key for key in relevant if not missing(features.get(key))]
    missing_features = [key for key in relevant if missing(features.get(key))]
    critical_missing = [key for key in group["critical"] if missing(features.get(key))]
    details["missing_features"] = missing_features
    if missing_features:
        codes.append("IMPORTANT_FEATURES_MISSING" if critical_missing else "SUPPORTING_FEATURES_MISSING")
    completeness = _level(len(missing_features), len(relevant), len(critical_missing))

    ref_product = (reference or {}).get("products", {}).get(pid)
    numeric_bounds = (ref_product or {}).get("numeric_bounds", {})
    categorical_values = (ref_product or {}).get("categorical_values", {})
    distribution_unavailable = ref_product is None
    outliers = []
    if ref_product is not None:
        for key in relevant:
            value = features.get(key)
            if missing(value):
                # Missingness substantially unlike training is a separate warning.
                if (ref_product.get("training_missing_rates", {}).get(key, 1.0) < 0.01):
                    codes.append("UNUSUAL_MISSINGNESS_PATTERN")
                continue
            if key in numeric_bounds:
                bound = numeric_bounds[key]
                try:
                    numeric_value = float(value)
                except (TypeError, ValueError):
                    outliers.append(key)
                    continue
                if not math.isfinite(numeric_value):
                    outliers.append(key)
                    continue
                lo, hi = bound.get("lower_01"), bound.get("upper_99")
                if lo is not None and hi is not None and not lo <= numeric_value <= hi:
                    outliers.append(key)
            elif key in categorical_values and str(value) not in categorical_values[key]:
                details["unseen_categories"][key] = str(value)
        details["numeric_out_of_range"] = outliers
        if outliers:
            codes.append("NUMERIC_FEATURE_OUTSIDE_TRAINING_RANGE")
        if details["unseen_categories"]:
            codes.append("UNSEEN_CATEGORICAL_VALUE")
    familiarity_issues = len(outliers) + len(details["unseen_categories"])
    familiarity = "unavailable" if distribution_unavailable else "high" if familiarity_issues == 0 else "medium" if familiarity_issues == 1 else "low"

    band = None
    validation = (ref_product or {}).get("validation", {})
    for candidate in validation.get("bins", []):
        if candidate["lower"] <= propensity < candidate["upper"] or (propensity == 1 and candidate["upper"] == 1):
            band = candidate
            break
    if band is None:
        calibration = "unavailable"
    else:
        ece = validation.get("ece")
        brier = validation.get("brier")
        interval = band.get("observed_rate_wilson_95_interval")
        width = interval[1] - interval[0] if interval else 1.0
        n = int(band.get("n", 0))
        if n >= 100 and width <= 0.20 and ece is not None and ece <= 0.05 and brier is not None and brier <= 0.15:
            calibration = "high"
        elif n >= 30 and ece is not None and ece <= 0.08 and brier is not None and brier <= 0.20:
            calibration = "medium"
        else:
            calibration = "low"
        if n < 30:
            codes.append("LIMITED_VALIDATION_SCORE_BAND")
        if calibration == "low":
            codes.append("WEAK_VALIDATION_CALIBRATION_EVIDENCE")
    if band is not None:
        details["validation_score_band"] = band
    details["validation_metrics"] = {key: validation.get(key) for key in ("n", "brier", "ece")}
    details["input_feature_count"] = len(relevant)
    details["observed_feature_count"] = len(observed)
    details["critical_feature_count"] = len(group["critical"])
    details["critical_observed_count"] = len(group["critical"]) - len(critical_missing)

    conflict_list = conflicts or []
    if conflict_list:
        codes.append("CONFLICTING_CUSTOMER_INFORMATION")
        details["conflicts"] = conflict_list
    all_missing = not observed
    if all_missing or distribution_unavailable or calibration == "unavailable":
        level = "unavailable"
    elif conflict_list or completeness == "low" or familiarity == "low" or calibration == "low":
        level = "low"
    elif completeness == "high" and familiarity == "high" and calibration == "high":
        level = "high"
    else:
        level = "medium"
    if all_missing:
        codes.append("NO_PRODUCT_RELEVANT_FEATURES_AVAILABLE")
    codes = list(dict.fromkeys(codes))
    return {
        "confidence": None,
        "confidence_level": level,
        "confidence_method": METHOD,
        "reliability": {
            "scope": "synthetic_validation_only",
            "feature_completeness": completeness,
            "distribution_familiarity": familiarity,
            "validation_calibration": calibration,
            "reason_codes": codes,
            "details": details,
            "limitations": [LIMITATION, "No numerical per-customer confidence or correctness probability is claimed."],
        },
    }


if __name__ == "__main__":
    output = save_reference()
    print(f"Saved training-only reliability reference: {output}")
