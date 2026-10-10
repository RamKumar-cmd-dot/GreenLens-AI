# Deterministic sustainability scenarios

All results are annual **operational scenario estimates**, not adoption predictions, financial eligibility decisions, lifecycle footprints or financed-emissions accounting. ML and LLM do not calculate these results. Implemented in backend/impact.py, with source records in data/reference/emission_factors_2025.json. Missing/invalid required inputs or factors yield UNAVAILABLE and null results. Eligible customers do not necessarily adopt.

## Verified factors

Source: UK Department for Energy Security and Net Zero, [2025 Government greenhouse-gas conversion factors](https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025), published 10 June 2025; [official flat workbook](https://assets.publishing.service.gov.uk/media/6846b6ea57f3515d9611f0dd/ghg-conversion-factors-2025-flat-format.xlsx). These values were extracted from the workbook, not guessed. The JSON stores row IDs, units, source URL, year, geographical applicability and workbook SHA-256.

| Activity | kgCO2e per unit | Unit | Workbook row |
|---|---:|---|---:|
| Petrol, average biofuel blend | 2.06916 | litre | 283 |
| Diesel, average biofuel blend | 2.57082 | litre | 187 |
| Natural gas | 0.18296 | kWh, gross calorific value | 83 |
| UK electricity generated | 0.17700 | kWh | 3066 |

UK factors are fixed at 2025 to align with the observation year. They are scenario factors, not a forecast of future grid intensity. Combustion and electricity-generation boundaries exclude upstream fuel production, transmission/distribution losses, manufacturing and end-of-life; biofuel biogenic CO2 reported outside scopes is not included. See the [official methodology](https://assets.publishing.service.gov.uk/media/6846b0870392ed9b784c0187/2025-GHG-CF-methodology-paper.pdf).

## EV Finance

`distance_km = annual_mileage_estimate × 1.609344`

`baseline_kgCO2e = distance_km × litres_per_100km / 100 × fuel_factor`

`EV_kgCO2e = distance_km × EV_grid_kWh_per_km × electricity_factor`

`avoided_kgCO2e = baseline - EV`

Defaults are **illustrative scenario choices**, not sourced emissions factors or measured vehicle attributes: petrol 7 litres/100 km, diesel 6 litres/100 km, EV grid electricity 0.18 kWh/km (assumed to include charging losses). Explicit supplied efficiency overrides are supported by the engine. Same distance in both cases; mileage is a synthetic estimate. Missing mileage or an unsupported powertrain returns UNAVAILABLE. EV-to-EV replacement lacks a supported counterfactual. Vehicle/battery manufacturing is excluded, so do not describe this as total lifecycle benefit.

## Green Home Loan

Representative scenario: a controls/efficiency package achieving a **hypothetical 10% reduction in total annual gas demand** for a homeowner with a gas boiler. This is sensitivity analysis, not a claim that a particular retrofit will achieve that reduction. Survey and engineering assessment are required.

`baseline = annual_gas_kWh × gas_factor`; `scenario = baseline × 0.90`; `avoided = baseline - scenario`.

Gas consumption assumes gross-CV metering. Electricity demand is unchanged. Other heating technologies return UNAVAILABLE for this package.

## Solar Finance

Requires ownership, suitable roof, system kWp, location-specific yield in kWh/kWp/year, the yield's source and location, self-consumption ratio, and annual electricity demand. A region label and generic roof flag alone are inadequate, so **the existing dataset produces UNAVAILABLE solar impacts**.

`generation = capacity_kWp × yield_kWh_per_kWp_year`

`displaced_grid_kWh = min(annual_demand, generation × self_consumption_ratio)`

`avoided = displaced_grid_kWh × electricity_factor`.

No export credit. No invented sunshine/yield coefficients. The calculation path is tested with an explicitly fictional fixture, not treated as sourced customer data. Do not use fixture yield values in demonstrations as verified estimates.

## Paperless Banking

Assumed one monthly statement with four printed pages: `avoided_pages = 12 × 4 = 48` if currently using paper and actually switching. Counts are illustrative, not observed. Already-paperless customers are excluded by recommendation rules. A reliable lifecycle factor for the actual statement/delivery chain is absent, so carbon impact stays null. Digital delivery and customer printing are unquantified.

## Edge cases, exclusions and aggregation

Zero consumption returns zero baseline/scenario; invalid negative/nonfinite physical inputs return UNAVAILABLE. Negative avoided emissions are preserved and mean increased emissions, never clamped into a benefit. Excluded/review/incomplete recommendations do not get an actionable scenario. Corporate summaries count unique customers separately from overlapping product matches and report conditional per-product totals only. They do not assume realized adoption, probability-weight carbon totals or sum overlapping home/solar benefits.
