# Synthetic methodology
All records are fictional. Seed 42; default 5,000 customers. Observation window: calendar 2025. Prediction date: 2026-01-01. Labels simulate adoption during January–June 2026. No external banking records are used. These are plausible demonstration assumptions, not fitted population parameters.

Income is clipped lognormal (log mean 7.85, SD .46, £700–£14,000 monthly). Ownership depends on age group. Household demand depends on property type, household size, heating technology and EV ownership. Fuel expenditure depends on annual mileage and powertrain. Monthly gas has a cosine winter peak; electricity has a smaller peak. Spending has lognormal variation. Transactions are category-level monthly synthetic purchases/bills, not a complete ledger; income, balances, transfers and detailed supermarket baskets are out of scope. Category/merchant pools overlap (Shell, Tesco, EDF, British Gas, Octopus); 12% of descriptions are generic. Shared merchant templates make classification easier than real deployment.

Generator equations are authoritative in data/generate_synthetic.py. Let σ(z)=1/(1+exp(-z)), W~Normal(0,1) be latent willingness shared across outcomes; I monthly income; E annual electricity kWh; G annual gas kWh; F observed mean monthly fuel spend; D digital ratio; L monthly logins. Independent Bernoulli draws use the following probabilities, conditional on use-case constraints:

- EV: σ(-3 + .75×combustion_vehicle + 1.1×replacement_intent + .003×F + .00008×(I-2500) + .7×W). Requires a vehicle and either non-EV or replacement intent.
- Green home: σ(-3 + .00006×G + .45×owner + .3×gas_boiler + .00007×(I-2500) + .8×W). Requires ownership.
- Solar: σ(-3.5 + .00022×E + .7×roof_suitable + .00009×(I-2500) + .9×W). Requires ownership and suitable roof.
- Paperless: σ(-2 + 2×D + .035×L + .7×W). Requires paper statements.

Constraints use latent complete synthetic facts; observed records subsequently contain missing ownership (3.5%), missing mileage (3.5%), and attempted vehicle inconsistencies (1%). Thus recorded data may require review even where a simulated event occurred. Latent willingness is never exported as a feature. No credit-approval decisions are simulated or asserted. Coefficients are scenario assumptions, not empirical estimates; sensitivity/generalization remain unvalidated. Class prevalence is measured in data/synthetic/metadata.json; training/evaluation fail clearly if required classes are absent.

Low Carbon London is optional and historical. No raw file was supplied at implementation time. The inspection script uses no guessed source column names. It processes a bounded file-prefix sample, which is not guaranteed representative, and only summarizes complete interval-supported days. Its output must not be interpreted as bank customers or product labels.
