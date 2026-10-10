# Data dictionary
All IDs are fictitious strings. customer_id is the primary key in customers and the foreign key in every related table. customers, assets, behaviour and labels have one row/customer. Products and transactions have many rows/customer. Dates use ISO YYYY-MM-DD. Amounts and income are GBP. Binary fields use 0/1 with missing values represented by blank CSV cells/null JSON. No confidential data is used.

| Table | Fields | Meaning/provenance |
|---|---|---|
| customers | customer_id, age_band, region, monthly_income_gbp, employment_status, customer_since | Synthetic observed snapshot; income monthly GBP; region fictional UK geography assignment |
| transactions | transaction_id, customer_id, transaction_date, merchant_name, merchant_description, amount_gbp, sustainability_category | Synthetic observed debit purchases/bills; positive amounts; one of eight reference labels, not model predictions |
| customer_products | customer_id, product_type, product_status, start_date, end_date | Synthetic account relationships; current_account, mortgage, vehicle_loan; blank end_date=open |
| customer_behaviour | customer_id, digital_logins_month, mobile_app_active, paper_statements_enabled, digital_transaction_ratio | Synthetic prior-month observed activity; ratio 0–1 |
| customer_assets | customer_id, homeowner, property_type, vehicle_ownership, vehicle_type, owns_ev | Synthetic reported attributes, may be missing/conflicting |
| customer_assets | annual_mileage_estimate, electricity_kwh_year, gas_kwh_year | Estimated annual miles and kWh; explicitly synthetic demand estimates |
| customer_assets | heating_technology, household_size, roof_suitable, replacement_intent | Added fields: synthetic pre-outcome reported heat type, household count, suitability and intent; support meaningful energy/adoption relationships |
| product_takeup_labels | customer_id, ev_finance_takeup, green_home_takeup, solar_finance_takeup, paperless_takeup | Simulated future binary adoption events, never eligibility labels or predictors |

Schema choices relative to the suggested brief: transactions contain outgoing purchases/bills only, so `amount_gbp` is a positive debit amount; a constant `debit_credit='debit'` field would add no information. `region` is coarse synthetic geography and intentionally replaces postcode to avoid unnecessary personal-location detail. Raw monthly income is retained, so a derived income band is not a source column. Product balances are omitted because the prototype has no balance-based rule or model feature. Vehicle replacement intent is captured directly; vehicle age is not synthesized because no source or credible aging process exists. Energy demand is represented by estimated annual electricity/gas kWh rather than a monthly meter series. Monthly digital logins, mobile-app activity, paper-statement preference, and digital transaction ratio provide prior-month digital behaviour; branch visits and a separate digital-statement flag are not simulated. The product catalogue documents each product's purpose, use cases, required information, exclusions and sustainability metric. These are deliberate schema adaptations, not claims that those values were observed.

Customer 360 carries snapshot attributes plus these features:

| Feature | Meaning |
|---|---|
| mean_monthly_fuel | Prior 12 months Fuel spend divided by 12, including zero-spend months |
| mean_monthly_electricity | Prior 12 months Electricity spend divided by 12 |
| mean_monthly_gas | Prior 12 months Gas spend divided by 12 |
| mean_monthly_public_transport | Prior 12 months Public Transport spend divided by 12 |
| mean_monthly_home_improvement | Prior 12 months Home Improvement spend divided by 12 |
| fuel_trend | Final three-month mean minus first three-month mean, GBP/month |
| existing_mortgage, existing_vehicle_loan | Active relationship with start before prediction date and no earlier end |
| data_timestamp | Snapshot cutoff, default 2026-01-01; excluded from model features |

Zero transaction spend assumes complete synthetic observation coverage; production must distinguish missing coverage from genuine zero spend. Source sustainability labels power the demo feature aggregation; production should use classifier outputs plus review where uncertain. The customer-split classifier is evaluated separately; classifier-error propagation into propensity has not been validated. Assets/behaviour are a single pre-cutoff snapshot, not a bitemporal database. customer_since and identifiers are not predictors. FEATURES in ml/common.py and data/schemas/feature_schema.json define the exact feature contract. Explanatory codes are documented in ml_methodology.md.

Optional historical electricity integration: `--london-summary` samples the distribution of historical meter-average daily electricity readings and applies a profile/cohort-median multiplier clipped to [0.5,2] to the synthetic structural electricity demand. In the preserved current cohort, `data/synthetic/metadata.json` records `data/processed/london_summary_proxy.csv` as the input. Its `complete_days` field is `floor(readings_count / 48)`, a coverage proxy, **not** verified calendar days containing 48 distinct valid half-hour readings. The new `data/processed/london_summary_profile.csv` names this `coverage_days_proxy` and the energy field `mean_annualized_daily_kwh`; its metadata records limitations. The separate `process_london_energy.py` can count unique timestamps per day for future processing, but the preserved generator input was the simpler proxy summary. This informs synthetic variation only; it does not calibrate current customer consumption or establish a modern UK population estimate. Meter IDs are never linked to synthetic customer IDs. Default generation uses no London data.
