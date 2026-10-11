# Model confidence and reliability assessment

## Meaning and separation

GreenLens reports propensity as the model's predicted probability of the **simulated** product take-up label. This propensity is not confidence, an observed personal preference, financial eligibility, credit approval, or a probability that the prediction is correct.

The per-customer `confidence` field intentionally remains `null`. The project has not established a statistically calibrated individual correctness probability, and the available labels are synthetic. Each GP01–GP04 result instead carries a `confidence_level` (`high`, `medium`, `low`, or `unavailable`) plus `confidence_method` and a structured `reliability` object. The tier is a qualitative diagnostic of available evidence, not a correctness guarantee.

## Signals and product-specific features

The assessment combines three independent signals:

1. **Feature completeness:** missing product-relevant inputs, with required use-case facts treated as critical. GP01 critical inputs are vehicle ownership, vehicle type, EV ownership, and replacement intent; supporting inputs are annual mileage, fuel spend/trend, and existing vehicle loan. GP02 critical inputs are homeownership and property type; supporting inputs are electricity/gas demand, heating technology, and existing mortgage. GP03 critical inputs are homeownership and roof suitability; supporting inputs are property type, electricity demand, region, and household size. GP04 critical inputs are paper-statement status and digital logins; supporting inputs are app activity, digital transaction ratio, and age band.
2. **Training-distribution familiarity:** numeric values are compared with per-feature 1st and 99th percentiles. The percentiles and missing rates are calculated from the saved training-customer identifiers only. Categorical values are compared with values observed in that same training split. Missingness on a feature with under 1% training missingness is also surfaced as an unusual missingness reason code. These checks identify unfamiliar inputs; they do not prove an input is invalid.
3. **Validation calibration support:** a customer's propensity is placed in the existing fixed 0.1-wide score band from validation evaluation. The output includes that band's validation sample count, mean score, observed synthetic take-up rate, and a 95% Wilson interval. The interval describes the observed event rate for the validation cohort in that band, not the individual customer. Empty bands are unavailable. Brier score and ECE are the already-reported validation metrics; no held-out test data is used to construct reliability references.

No numerical reliability formula is produced. Independent model ensembles were not retained for all products and no realistic perturbation protocol has been validated, so prediction stability is not claimed or used.

## Exact tier rules

Feature-completeness level is `high` if no product-relevant inputs are missing; `medium` if exactly one supporting input is missing and no critical input is missing; `low` if any critical input is missing or at least two product-relevant inputs are missing; `unavailable` if all product-relevant inputs are missing.

Distribution familiarity is `high` if all observed relevant inputs are within the numeric training bounds and known categories; `medium` for one numeric outlier or one unseen category; `low` for two or more such findings; and `unavailable` if the training reference is absent.

Validation-calibration support is `high` only when the local band has at least 100 validation customers, its Wilson interval width is at most 0.20, validation ECE is at most 0.05, and validation Brier score is at most 0.15. It is `medium` when the band has at least 30 customers, ECE is at most 0.08, and Brier score is at most 0.20. Otherwise it is `low`; if there is no validation band or reference, it is `unavailable`.

The overall `confidence_level` is `unavailable` if all product-relevant features are missing, the training reference is absent, or no validation band supports assessment. It is `low` if there are conflicting customer facts, low completeness, low distribution familiarity, or low validation support. It is `high` only if all three signals are high. Other assessable combinations are `medium`.

These cutoffs create reproducible evidence tiers for this prototype; they are not statistically optimized decision boundaries. `high` means the observed inputs and synthetic validation support satisfy the stricter stated criteria. It does **not** mean the customer prediction is correct with any stated probability, and it does not imply real-customer reliability.

## Artifact and leakage controls

`ml/confidence.py` builds `ml/reports/confidence_reference.json`. Training bounds and allowed categories use only IDs in `data/processed/splits.json` under `train`. Calibration bins and calibration metrics come from the existing validation reports. The script verifies customer split disjointness and that all training IDs have Customer 360 rows. It never reads test outcomes to set tier rules, never tunes the models, and never changes the selected propensity thresholds. Regenerate the reference with:

```bash
uv run python -m ml.confidence
```

The current validation set has 750 customers per product. Existing validation Brier/ECE are: GP01 0.0936 / 0.0210; GP02 0.0939 / 0.0189; GP03 0.0515 / 0.0106; GP04 0.1000 / 0.0573. These are calibration diagnostics against simulated labels, not evidence of performance on real banking customers. Score-band sample sizes vary substantially; sparse bands are explicitly marked low or unavailable.

## API and frontend interpretation

Every recommendation includes `propensity`, `confidence: null`, `confidence_level`, `confidence_method`, and `reliability`. The reliability object reports the three signal tiers, reason codes, feature/band details, and limitations. Missing or conflicting facts and out-of-range/unseen inputs are surfaced as reason codes. Reliability assessment is read-only and cannot alter propensity, use-case screening, exclusions, or institutional financial eligibility.

The frontend should say “simulated take-up propensity” for the percentage and “estimate reliability” for the qualitative tier. It should explain that the tier is a synthetic-data diagnostic and never render it as a second percentage. `unavailable` means the system lacks enough relevant inputs or validation support to assess reliability, not that propensity is zero.
