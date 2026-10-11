"""Reproducible fictional UK banking cohort; outcomes follow the observation window."""

import argparse
import warnings
import numpy as np
import pandas as pd
from ml.common import DATA, SEED, AS_OF, TARGETS, save_json

# Merchant pools include shared brands, payment noise and imperfect descriptions.
MERCHANTS = {
    "Fuel": [
        ("Shell", "service station forecourt"),
        ("BP", "pay at pump"),
        ("Tesco", "petrol station"),
        ("Esso", "motor fuel"),
    ],
    "Electricity": [
        ("Octopus", "electric account"),
        ("EDF", "power meter"),
        ("British Gas", "electricity direct debit"),
    ],
    "Gas": [
        ("British Gas", "gas supply"),
        ("EDF", "gas meter"),
        ("E.ON", "natural gas account"),
    ],
    "Public Transport": [
        ("TfL", "contactless journey"),
        ("Northern", "rail ticket"),
        ("Stagecoach", "bus pass"),
    ],
    "Home Improvement": [
        ("B&Q", "building materials"),
        ("Wickes", "insulation supplies"),
        ("Homebase", "renovation order"),
    ],
    "Automotive": [
        ("Halfords", "service and MOT"),
        ("Kwik Fit", "tyre replacement"),
        ("Shell", "car wash"),
    ],
    "Utilities": [
        ("Thames Water", "water bill"),
        ("BT", "broadband account"),
        ("EE", "mobile plan"),
        ("Octopus", "dual energy account"),
    ],
    "Other": [
        ("Tesco", "weekly shop"),
        ("Aldi", "groceries"),
        ("Amazon", "marketplace order"),
        ("Costa", "card purchase"),
    ],
}


def generate(
    n=5000, seed=SEED, output=DATA / "synthetic", london_summary=None, overwrite=False
):
    if n < 100:
        raise ValueError("Use at least 100 customers; 5000 recommended for evaluation.")
    if output.exists() and any(output.glob("*.csv")) and not overwrite:
        raise FileExistsError(
            f"{output} already contains generated tables; pass overwrite=True only when replacement is intended"
        )
    rng = np.random.default_rng(seed)
    output.mkdir(parents=True, exist_ok=True)
    profiles = None
    london_profile_methodology = None
    if london_summary is not None:
        profile_frame = pd.read_csv(london_summary)
        if {"coverage_days_proxy", "mean_annualized_daily_kwh"} <= set(
            profile_frame.columns
        ):
            coverage = profile_frame.coverage_days_proxy
            profile_values = profile_frame.mean_annualized_daily_kwh
            london_profile_methodology = "Historical LCL meter averages; coverage_days_proxy is reading_count//48, not verified complete calendar days; profile values are annualized mean half-hour kWh converted to a daily average."
        elif {"complete_days", "mean_complete_daily_kwh"} <= set(profile_frame.columns):
            warnings.warn(
                "Legacy London summary column complete_days is an observation-count proxy, not verified complete days.",
                RuntimeWarning,
            )
            coverage = profile_frame.complete_days
            profile_values = profile_frame.mean_complete_daily_kwh
            london_profile_methodology = "Legacy historical LCL summary; complete_days is a reading-count proxy (not verified complete calendar days); profile values are annualized mean half-hour kWh converted to a daily average."
        else:
            raise ValueError(
                "London summary must have coverage_days_proxy/mean_annualized_daily_kwh columns or the documented legacy proxy columns"
            )
        profiles = profile_values.loc[coverage >= 7].dropna().to_numpy()
        profiles = profiles[(profiles > 0) & np.isfinite(profiles)]
        if len(profiles) == 0:
            raise ValueError(
                "London summary needs meters with coverage_days_proxy >= 7 and a finite positive annualized daily mean"
            )
    customers = []
    assets = []
    behaviours = []
    products = []
    transactions = []
    labels = []
    for i in range(n):
        cid = f"C{i:06d}"
        age = rng.choice(["18-29", "30-44", "45-59", "60+"], p=[0.22, 0.32, 0.28, 0.18])
        income = round(float(np.clip(rng.lognormal(7.85, 0.46), 700, 14000)), 2)
        owner = int(
            rng.random()
            < ({"18-29": 0.2, "30-44": 0.57, "45-59": 0.73, "60+": 0.78}[age])
        )
        house = rng.choice(
            ["flat", "terraced", "semi_detached", "detached"], p=[0.28, 0.3, 0.28, 0.14]
        )
        size = int(rng.integers(1, 6))
        vehicle = int(rng.random() < 0.76)
        ev = int(vehicle and rng.random() < 0.11)
        vtype = (
            "electric"
            if ev
            else rng.choice(["petrol", "diesel"]) if vehicle else "none"
        )
        mileage = round(float(rng.lognormal(8.9, 0.42))) if vehicle else 0
        heat = rng.choice(
            ["gas_boiler", "electric_resistance", "heat_pump"], p=[0.77, 0.17, 0.06]
        )
        multiplier = {
            "flat": 0.7,
            "terraced": 1.0,
            "semi_detached": 1.2,
            "detached": 1.6,
        }[house]
        electricity = round(
            (
                1500
                + 500 * size
                + ev * mileage * 0.28
                + (
                    3500
                    if heat == "electric_resistance"
                    else 1800 if heat == "heat_pump" else 0
                )
            )
            * multiplier
            * rng.uniform(0.75, 1.3)
        )
        if profiles is not None:
            electricity = round(
                electricity
                * float(np.clip(rng.choice(profiles) / np.median(profiles), 0.5, 2))
            )
        gas = (
            round((6500 + 1600 * size) * multiplier * rng.uniform(0.7, 1.3))
            if heat == "gas_boiler"
            else 0
        )
        engagement = rng.beta(3, 2)
        logins = int(rng.poisson(engagement * 25))
        paper = int(rng.random() < 0.65 - 0.35 * engagement)
        roof = int(house != "flat" and rng.random() < 0.8)
        intent = int(vehicle and rng.random() < 0.25)
        customers.append(
            [
                cid,
                age,
                rng.choice(
                    [
                        "London",
                        "South East",
                        "North West",
                        "Scotland",
                        "Wales",
                        "Midlands",
                    ]
                ),
                income,
                rng.choice(
                    ["employed", "self_employed", "retired", "not_employed"],
                    p=[0.65, 0.16, 0.13, 0.06],
                ),
                f"{rng.integers(2005,2024)}-01-01",
            ]
        )
        asset = [
            cid,
            owner,
            house,
            vehicle,
            vtype,
            ev,
            mileage,
            electricity,
            gas,
            heat,
            size,
            roof,
            intent,
        ]
        if rng.random() < 0.035:
            asset[1] = np.nan
        if rng.random() < 0.035:
            asset[6] = np.nan
        if rng.random() < 0.01:
            asset[5] = (
                1 if vtype == "petrol" else 0
            )  # deliberate conflict, flagged downstream
        assets.append(asset)
        behaviours.append(
            [cid, logins, int(engagement > 0.25), paper, round(engagement, 4)]
        )
        products.append([cid, "current_account", "active", "2020-01-01", None])
        if owner and rng.random() < 0.65:
            products.append([cid, "mortgage", "active", "2021-02-01", None])
        if vehicle and rng.random() < 0.24:
            products.append([cid, "vehicle_loan", "active", "2023-02-01", None])
        fuel_year = 0
        for month in range(1, 13):
            seasonal = 1 + 0.4 * np.cos((month - 1) * np.pi / 6)
            spends = {
                "Fuel": mileage / 12 * 0.15 * (0.03 if ev else 1) if vehicle else 0,
                "Electricity": electricity
                / 12
                * 0.25
                * (1 + 0.12 * np.cos((month - 1) * np.pi / 6)),
                "Gas": gas / 12 * 0.065 * seasonal,
                "Public Transport": 40 + (1 - vehicle) * 80,
                "Home Improvement": income * 0.035,
                "Automotive": 35 * vehicle,
                "Utilities": 80,
                "Other": income * 0.28,
            }
            for category, base in spends.items():
                if base <= 0 or (
                    category in ["Home Improvement", "Automotive"]
                    and rng.random() < 0.65
                ):
                    continue
                amount = round(base * rng.lognormal(-0.08, 0.4), 2)
                if category == "Fuel":
                    fuel_year += amount
                merchant, desc = MERCHANTS[category][
                    rng.integers(len(MERCHANTS[category]))
                ]
                if rng.random() < 0.12:
                    desc = rng.choice(["card payment", "DD monthly", "online purchase"])
                transactions.append(
                    [
                        f"T{len(transactions):08d}",
                        cid,
                        f"2025-{month:02d}-{rng.integers(1,29):02d}",
                        merchant,
                        f"{desc} REF {rng.integers(1000,9999)}",
                        amount,
                        category,
                    ]
                )
        willingness = rng.normal(
            0, 1.0
        )  # latent, deliberately unavailable at inference
        sigmoid = lambda z: 1 / (1 + np.exp(-z))
        z = [
            -3
            + 0.75 * (vtype in ["petrol", "diesel"])
            + 1.1 * intent
            + 0.003 * fuel_year / 12
            + 0.00008 * (income - 2500)
            + 0.7 * willingness,
            -3
            + 0.00006 * gas
            + 0.45 * owner
            + 0.3 * (heat == "gas_boiler")
            + 0.00007 * (income - 2500)
            + 0.8 * willingness,
            -3.5
            + 0.00022 * electricity
            + 0.7 * roof
            + 0.00009 * (income - 2500)
            + 0.9 * willingness,
            -2 + 2.0 * engagement + 0.035 * logins + 0.7 * willingness,
        ]
        allowed = [vehicle and (not ev or intent), owner, owner and roof, paper]
        labels.append(
            [cid] + [int(allowed[j] and rng.random() < sigmoid(z[j])) for j in range(4)]
        )
    tables = {
        "customers": (
            customers,
            [
                "customer_id",
                "age_band",
                "region",
                "monthly_income_gbp",
                "employment_status",
                "customer_since",
            ],
        ),
        "customer_assets": (
            assets,
            [
                "customer_id",
                "homeowner",
                "property_type",
                "vehicle_ownership",
                "vehicle_type",
                "owns_ev",
                "annual_mileage_estimate",
                "electricity_kwh_year",
                "gas_kwh_year",
                "heating_technology",
                "household_size",
                "roof_suitable",
                "replacement_intent",
            ],
        ),
        "customer_behaviour": (
            behaviours,
            [
                "customer_id",
                "digital_logins_month",
                "mobile_app_active",
                "paper_statements_enabled",
                "digital_transaction_ratio",
            ],
        ),
        "customer_products": (
            products,
            ["customer_id", "product_type", "product_status", "start_date", "end_date"],
        ),
        "transactions": (
            transactions,
            [
                "transaction_id",
                "customer_id",
                "transaction_date",
                "merchant_name",
                "merchant_description",
                "amount_gbp",
                "sustainability_category",
            ],
        ),
        "product_takeup_labels": (labels, ["customer_id"] + list(TARGETS.values())),
    }
    for name, (rows, cols) in tables.items():
        pd.DataFrame(rows, columns=cols).to_csv(output / f"{name}.csv", index=False)
    save_json(
        output / "metadata.json",
        {
            "london_profile_source": str(london_summary) if london_summary else None,
            "london_profile_methodology": london_profile_methodology,
            "seed": seed,
            "customers": n,
            "as_of": AS_OF,
            "observation_start": "2025-01-01",
            "outcome_window": ["2026-01-01", "2026-06-30"],
            "source": "entirely synthetic; not real decisions",
            "prevalence": pd.DataFrame(
                labels, columns=["customer_id"] + list(TARGETS.values())
            )
            .drop(columns="customer_id")
            .mean()
            .to_dict(),
        },
    )
    print(f"Generated {n} customers, {len(transactions)} transactions in {output}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--customers", type=int, default=5000)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--london-summary", type=str)
    p.add_argument(
        "--overwrite", action="store_true", help="Replace existing synthetic CSVs"
    )
    a = p.parse_args()
    generate(
        a.customers, a.seed, london_summary=a.london_summary, overwrite=a.overwrite
    )
