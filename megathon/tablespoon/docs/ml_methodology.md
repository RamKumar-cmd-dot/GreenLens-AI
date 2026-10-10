# ML methodology and integration
Customer IDs split deterministically 70/15/15 using random_state=42; tables/transactions inherit the same partition. No target columns enter FEATURES. Snapshot fields are assumed collected before 2026-01-01; transaction and product dates are filtered. Do not use future asset/behaviour snapshots in production.

Separate logistic and random-forest candidates fit only training customers. Median numeric imputation, missing indicators, scaling, categorical imputation and unknown-safe one-hot encoding live inside fitted pipelines. Random forest: 120 trees, depth 8, minimum leaf 20. Logistic regression: max_iter 1200. Select lowest validation Brier score. Training-prevalence constant probabilities are the no-signal baseline. Natural prevalence is preserved: no oversampling/class weighting that would distort take-up probabilities. AP, label distributions and precision/recall expose imbalance. Threshold 0.5 is fixed for reporting, not tuned for business value. Low recall is possible and explicitly reported. ROC-AUC is null for one-class samples.

No additional calibration is claimed. JSON includes ten fixed-width calibration bins and expected calibration error (ECE), Brier score, ROC-AUC, AP, precision, recall, F1 and a confusion matrix ordered [negative, positive]. Validation and test results are separate. Confidence is null; reliability reports aggregate validation metrics and missing-feature count. Probabilities are uncalibrated estimates under a synthetic generator, with no real-bank validation or per-person uncertainty interval. Protected/proxy demographic fields require bank governance before real use.

`ml/reports/selected_thresholds.json` stores validation-set F1-selected thresholds (GP01 .24, GP02 .10, GP03 .23, GP04 .28). In inference these appear under `threshold_screen`, alongside the continuous propensity. `ABOVE_VALIDATION_SELECTED_THRESHOLD` means only that the score crosses a screening threshold chosen on validation data. It neither modifies use-case eligibility nor constitutes approval, customer confidence or an adoption forecast. The separate test-threshold report is historical final reporting; do not retune against that held-out set.

Transaction taxonomy: Fuel = purchased road fuel; Electricity = explicit electricity supply; Gas = explicit gas supply; Public Transport = passenger rail/bus/transit; Home Improvement = property renovation/materials; Automotive = vehicle service, tyres, MOT and washing, excluding fuel; Utilities = water, telecom and inseparable dual-fuel bills; Other = all remaining/unidentified transactions. Each record receives exactly one label. Automotive and combined-utility rules precede fuel/gas matches. Rule baseline defaults to Other. TF-IDF removes numeric references and uses unigram/bigram logistic regression. Unknown vocabulary defaults to Other and review; maximum class probability below .6 flags ambiguity, and is not calibrated confidence. Shared synthetic merchant vocabulary is an evaluation limitation. No unseen-merchant performance claim is made.

Reason codes are deterministic opportunity evidence, not causal explanations or model feature attributions. They are returned even when a product is excluded, with explicit status. Rules: fuel >=£100/month; mileage >=10,000/year; electricity >=4,000 kWh/year; gas >=12,000 kWh/year; logins >=15/month. Missing evidence never earns a reason code. These evidence cutoffs are independent of the validation-selected statistical priority thresholds.

Use-case screening does not establish financial eligibility. All products require authoritative institutional rules, consent/product availability checks and any applicable affordability/credit assessment. Missing ownership means needs_review. Renters, already-paperless customers, unsuitable roofs and existing EV owners without replacement intent have explicit exclusions. No LLM or carbon arithmetic is inside ML.

Backend imports:
```python
from ml.inference import load_models, predict_customer, predict_opportunities, classify_transaction
load_models()  # call at startup; trusted local joblib only
result = predict_customer('C000000')
result = predict_opportunities({'customer_id': 'new', 'homeowner': 1})
category = classify_transaction({'merchant_name': 'Shell', 'merchant_description': 'pay at pump'})
```
Return dictionaries serialize to JSON with no NaNs. Map ValueError to HTTP 422 and unknown customer KeyError to HTTP 404. predict_customer is a demo CSV lookup, not a production datastore; production should pass a validated Customer 360 snapshot to predict_opportunities. Model cache must be cleared/restarted after replacing artifacts. Preserve model feature order/schema and training library versions. Never load untrusted joblib files.

Carbon inputs include annual mileage, electricity/gas kWh, vehicle type, explicit missing values and synthetic-estimate provenance. A separate deterministic engine must supply documented factors, factor year, geography, baseline/counterfactual assumptions and formulas; no carbon savings are claimed here. Frontend displays status, exclusions, reasons and evidence without inventing eligibility or environmental benefits.

Supported scope: FR1 customer unification, FR2 transaction classification, FR3 opportunity/propensity prediction, FR7 evidence-backed reason codes, as described by the supplied brief. The original Lloyds PDF was not supplied, so broader compliance has not been independently checked.
