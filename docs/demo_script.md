# Three-minute live demonstration

Keep the API and Vite app running with synthetic data. Use `LLM_ENABLED=false` for a deterministic, fast demo; the explanation cards use validated backend facts and a deterministic fallback. State that all people and product outcomes are fictional.

1. **Customer view — C002056 (45 seconds).** Point out the Customer 360 profile, prior-year spending, estimated energy data and transaction classifications. This synthetic profile has a petrol car, estimated 24,033 annual miles and mean monthly fuel spend of £288.70.
2. **EV opportunity (45 seconds).** Open GP01 details. The saved propensity is about 58.5%; the validation-selected statistical priority threshold is 24%. Show the `HIGH_FUEL_SPEND`, `EXISTING_PETROL_VEHICLE` and `HIGH_ANNUAL_MILEAGE` reasons with their supporting values. The deterministic EV estimate is a conditional annual operational scenario based on mileage, assumed vehicle efficiency and documented 2025 UK factors. It is neither a realized saving nor a lending decision.
3. **Eligibility separation and exclusion (35 seconds).** Search customer C000042. Their GP01 result carries an `EXISTING_EV_NO_REPLACEMENT` exclusion. The score remains visible but status is EXCLUDED. Emphasize that propensity does not override the use-case screen, and that neither the model nor the prototype determines credit approval.
4. **Other products and limits (25 seconds).** Return to C002056 and show the other three product cards. Solar impact is unavailable because location-specific yield and system facts are not present. Paperless shows an illustrative page count only; no unsupported paper-carbon factor is applied.
5. **Business view (30 seconds).** Show the product match counts, propensity distributions and conditional impact totals. Filter opportunities by product and the validation-selected threshold, then drill down to a customer. Counts across products can overlap and scenario totals assume adoption; they are not forecasts.
6. **Scenario explorer (20 seconds).** Return to a customer and simulate switching to paperless or owning an EV. Show that the backend reruns the saved models and product rules and does not persist the hypothetical change.

Close with the held-out results in [model evaluation](model_evaluation.md), the synthetic-label limitations and the fact that LCL only informed synthetic electricity-demand variation.
