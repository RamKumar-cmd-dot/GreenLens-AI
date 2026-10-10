# Lloyds PS1 submission checklist

| Deliverable | Current evidence | Status / limitation |
|---|---|---|
| 1. Working prototype | FastAPI endpoints, SQLite snapshot, React customer/business dashboards | Implemented locally; no auth and no production customer data access |
| 2. Source and run instructions | README, requirements, reproduction guide | Implemented; package install needs network or a prepared environment |
| 3. Trained models and inference | Four saved propensity pipelines, transaction classifier, `ml.inference` | Artifacts preserved and read-only audited; Python 3.12 / sklearn 1.9.1 runtime pinned |
| 4. Preprocessing and feature engineering | Synthetic relational generator, Customer 360, classifier and ML pipelines | Implemented; historical source coverage has proxy limitations |
| 5. LLM implementation and evaluation | Optional constrained OpenAI sentence selection, deterministic fallback, `docs/llm_methodology.md`, 28 offline guardrail cases with dimension scores | Live provider output could not be validated; implementation intentionally does not generate new prose |
| 6. Architecture diagram | Mermaid in `docs/architecture.md` | Implemented |
| 7. Evaluation report | `docs/model_evaluation.md`, product heuristic comparison, customer-held-out and merchant-held-out classifier reports | Uses synthetic targets and merchants; no real-world generalization claim |
| 8. Responsible AI note | `docs/responsible_ai.md` | Implemented; fairness is not empirically established |
| 9. Held-out predictions | `ml/reports/GP*_test_predictions.csv`, transaction predictions | Present for the existing customer-level test split; threshold test report is final and must not be retuned |

Remaining before a production-oriented submission: verify the exact Low Carbon London download license, validate a live LLM provider response if the brief requires generated text, obtain site-specific solar yields outside the London reference scenario, run a final visual review on the judging display, and obtain the full official Lloyds PS1 brief for exact compliance mapping. This is a synthetic hackathon prototype, not a deployable financial decision system.
