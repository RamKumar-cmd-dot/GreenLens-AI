"""Shared versioned contracts; paths are independent of the caller's cwd."""

from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MODELS = ROOT / "ml/models"
REPORTS = ROOT / "ml/reports"
SEED = 42
AS_OF = "2026-01-01"
VERSION = "greenlens-synthetic-v1"
CATEGORIES = [
    "Fuel",
    "Electricity",
    "Gas",
    "Public Transport",
    "Home Improvement",
    "Automotive",
    "Utilities",
    "Other",
]
TARGETS = {
    "GP01": "ev_finance_takeup",
    "GP02": "green_home_takeup",
    "GP03": "solar_finance_takeup",
    "GP04": "paperless_takeup",
}
NUMERIC = [
    "monthly_income_gbp",
    "mean_monthly_fuel",
    "mean_monthly_electricity",
    "mean_monthly_gas",
    "mean_monthly_public_transport",
    "mean_monthly_home_improvement",
    "fuel_trend",
    "homeowner",
    "vehicle_ownership",
    "owns_ev",
    "annual_mileage_estimate",
    "electricity_kwh_year",
    "gas_kwh_year",
    "digital_logins_month",
    "mobile_app_active",
    "paper_statements_enabled",
    "digital_transaction_ratio",
    "existing_mortgage",
    "existing_vehicle_loan",
    "roof_suitable",
    "replacement_intent",
    "household_size",
]
CATEGORICAL = [
    "age_band",
    "region",
    "employment_status",
    "property_type",
    "vehicle_type",
    "heating_technology",
]
FEATURES = NUMERIC + CATEGORICAL


def save_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(
            obj,
            indent=2,
            allow_nan=False,
            default=lambda v: v.item() if isinstance(v, np.generic) else str(v),
        )
    )
