# Executed ML evaluation

All results below were read from the existing reports and independently reproduced from the saved propensity pipelines by `python -m ml.verify_artifacts`. No model was fit during this audit. Targets are simulated outcomes. These metrics do not establish performance on Lloyds customers or real merchants.

## Product propensity

Each product compares logistic regression with a random forest. Selection uses the lowest validation Brier score; the test set is held out. The no-signal baseline is constant training prevalence. The table lists selected-model ROC-AUC, average precision and Brier score on validation and test; threshold-dependent classification metrics at 0.5 are in the machine-readable JSON and are intentionally not the business priority policy.

| Product | Train positives / n | Selected | Validation AUC / AP / Brier | Test AUC / AP / Brier |
|---|---:|---|---|---|
| GP01 EV Finance | 490 / 3,500 (14.0%) | Logistic Regression | 0.7705 / 0.3253 / 0.0936 | 0.7508 / 0.2981 / 0.1160 |
| GP02 Green Home Loan | 372 / 3,500 (10.6%) | Logistic Regression | 0.7706 / 0.2589 / 0.0939 | 0.8147 / 0.2715 / 0.0796 |
| GP03 Solar Finance | 256 / 3,500 (7.3%) | Logistic Regression | 0.9131 / 0.5007 / 0.0515 | 0.9009 / 0.3440 / 0.0456 |
| GP04 Paperless Banking | 659 / 3,500 (18.8%) | Random Forest | 0.8773 / 0.4443 / 0.1000 | 0.8657 / 0.4719 / 0.1074 |

Split sizes are 3,500 train, 750 validation and 750 test customers. The 70/15/15 customer split has no overlap. Confusion matrices, precision, recall, F1, Brier, ten-bin calibration and expected calibration error are in `ml/reports/GP01.json` through `GP04.json`; held-out scores/labels are in `ml/reports/GP*_test_predictions.csv`. The saved pipeline verifies that numeric imputation statistics equal the training-only medians. The propensity probabilities are uncalibrated estimates from synthetic labels; per-customer confidence is unavailable.

### Priority-threshold screen

Thresholds were chosen on validation by F1 and saved in `ml/reports/selected_thresholds.json`. The subsequent held-out threshold results are preserved in `ml/reports/threshold_test_metrics.json`. They have already been used for final reporting; do not tune again against this test set.

| Product | Validation threshold | Test precision | Test recall | Test F1 | Test customers flagged / 750 |
|---|---:|---:|---:|---:|---:|
| GP01 | 0.24 | 0.3551 | 0.4298 | 0.3889 | 138 |
| GP02 | 0.10 | 0.1983 | 0.9333 | 0.3271 | 353 |
| GP03 | 0.23 | 0.2800 | 0.4773 | 0.3529 | 75 |
| GP04 | 0.28 | 0.4318 | 0.8702 | 0.5772 | 264 |

This threshold is a candidate-review prioritization aid only. It does not set eligibility or credit approval and does not replace the continuous score. The high GP02/GP04 recall comes with many flagged customers and lower precision; the threshold is not a product-contact policy.

## Transaction classification

| Model | Validation macro F1 | Test macro F1 |
|---|---:|---:|
| TF-IDF + Logistic Regression | 0.9808 | 0.9803 |
| Rule baseline | 0.9177 | 0.9181 |

Evaluation includes 55,157 validation and 55,207 test transactions. Detailed per-category precision, recall, F1 and confusion matrices are in `ml/reports/transaction_metrics.json`. Customer IDs are split, but synthetic merchant templates are shared across splits; these high scores do not measure unseen real-merchant generalization.

### Merchant-held-out diagnostic

To test this limitation directly, a separate diagnostic held out seven merchant names across the full transaction set, with no merchant name crossing partitions and all eight categories retained on each side. This is not the primary customer-level evaluation and does not alter the shipped classifier. TF-IDF + Logistic Regression macro F1 was **0.0946** on 108,289 held-out transactions; the fixed rule baseline scored **0.9209**. The large gap shows that the learned classifier depends heavily on repeated merchant/text templates. These are still synthetic merchants and descriptions. See `ml/reports/transaction_merchant_holdout.json`.

### Explainable product-rule baseline

Before measuring this diagnostic, we fixed four simple binary rules using the existing explanation cutoffs: (GP01) an owned petrol/diesel vehicle and fuel spend at least £100/month or mileage at least 10,000/year; (GP02) homeowner and gas demand at least 12,000 kWh/year; (GP03) homeowner, suitable roof and electricity demand at least 4,000 kWh/year; (GP04) paper statements and at least 15 digital logins/month. These are screening heuristics, not eligibility rules. They are not tuned on the held-out test set. Model F1 below is the existing report at its fixed 0.5 classification cutoff; the validation-F1 priority thresholds remain separately reported above.

| Product | Heuristic validation F1 | Heuristic test F1 | Selected model validation F1 @ 0.5 | Selected model test F1 @ 0.5 |
|---|---:|---:|---:|---:|
| GP01 | 0.2618 | 0.3049 | 0.0220 | 0.0000 |
| GP02 | 0.3402 | 0.3116 | 0.0000 | 0.0000 |
| GP03 | 0.4865 | 0.3394 | 0.3684 | 0.2222 |
| GP04 | 0.5429 | 0.5121 | 0.0000 | 0.0149 |

The heuristics outperform model hard classifications at 0.5 in this synthetic cohort, although the models' continuous scores are selected on validation Brier score and separate lower thresholds were selected for prioritization. This is a useful baseline challenge, not evidence that the heuristic is a superior general model. Full metrics are in `ml/reports/rule_baseline_metrics.json`.

## Limits

Labels were generated by explicit synthetic probabilistic processes, not observed product decisions. All propensity validation and test metrics reflect agreement with those simulated labels, including their assumptions and artifacts. There are no real-bank outcomes, external population benchmark, overall model-performance confidence intervals or deployment fairness guarantees. The score-band Wilson intervals described in the ML method summarize only synthetic validation cohorts; they are not individual confidence intervals. See [ML method](ml_methodology.md) and [responsible-AI note](responsible_ai.md).
