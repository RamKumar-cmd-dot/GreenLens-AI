# Merchant-held-out transaction diagnostic

Fixed, predeclared merchant-name holdout chosen to retain every label in both partitions; no held-out merchant appears in training. This secondary synthetic diagnostic is not real-merchant generalization. Model is diagnostic only and does not replace the saved primary pipeline.

- tfidf_logistic: macro F1 0.0946; 108289 test rows
- rule_baseline: macro F1 0.9209; 108289 test rows
