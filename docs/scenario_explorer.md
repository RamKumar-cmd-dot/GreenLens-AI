# Combinable scenario explorer

The scenario endpoint evaluates one merged copy of a synthetic customer's current feature record. It reuses the saved product models, the existing reliability assessment, rules-based use-case screening, and deterministic impact engine. It never writes scenario features to the customer tables or Customer Memory.

## Presets

The single authoritative preset map is `backend/scenarios.py` (`SCENARIO_PRESETS`). Selected overrides are merged in the order sent; if future presets set the same field differently, the later selected chip wins. Duplicate chips are ignored while preserving order.

| Chip | Feature overrides | Meaning |
| --- | --- | --- |
| `EV` | `vehicle_ownership=1`, `vehicle_type="electric"`, `owns_ev=1`, `replacement_intent=0` | Preserves the old “Simulate owning an EV” behavior: assumes the customer already owns an EV and has no replacement use case. It does not simulate financing or buying an EV. The existing rules exclude GP01 for an EV owner without replacement intent. |
| `GREEN_HOME` | `homeowner=1`, `heating_technology="gas_boiler"` | Assumes ownership and an existing gas boiler so the existing Green Home efficiency scenario can be evaluated. The boiler is not presented as a green improvement. The carbon engine's efficiency package remains hypothetical and is not applied to the stored profile. |
| `SOLAR` | `homeowner=1`, `roof_suitable=1` | Assumes ownership and roof suitability only; it does not simulate installed panels. Existing solar impact rules require annual electricity demand and a supported London yield, or explicit site inputs already present in the feature record. The preset does not invent site-specific PV values. |
| `PAPERLESS` | `paper_statements_enabled=0` | Preserves the old “Simulate switching to paperless” behavior. It is a what-if input, not saved customer feedback; existing screening marks GP04 as already paperless in this hypothetical state. |

If a selected chip's values already match the current profile, its note says no feature changed. Solar notes also explain when the regional yield is unsupported. `changed_attributes` contains only fields whose values differ; `scenario_changes` contains the final merged preset values for compatibility and transparency.

## API

`POST /customers/{customer_id}/scenario`

```json
{"apply": ["EV", "SOLAR"]}
```

An empty list returns an unchanged baseline comparison. Unknown chip IDs and malformed requests return 422; unknown customer IDs return 404 when the recommendation service is available. The response retains `opportunities` and `scenario_changes` for the former response contract, and adds `applied_chips`, `changed_attributes`, `original_attributes`, `chip_notes`, `comparisons`, and explicit disclaimers. Each product comparison contains baseline and hypothetical propensity, use-case status, reliability tier, reason codes, evidence, and separate impact results.

For existing clients, the old exact `changes` payloads for the EV and Paperless buttons are translated to their chip IDs. Arbitrary model-feature writes are rejected. A direct legacy `Recommendations.scenario(customer_id, changes)` call is also supported for those two payloads.

## Interpretation

Propensity changes are model outputs conditional on changed input features, not causal intervention or adoption effects. Screening remains separate from credit or product approval. Impact is calculated independently for each product and is not summed. In particular, Solar impact remains `UNAVAILABLE` outside the current supported London regional-yield path when no explicit PV site inputs exist. An unavailable result includes the impact engine's reason.

Every response is marked synthetic and carries disclaimers that the hypothetical record is not stored, no completed intervention is implied, financial eligibility is not assessed, and separate product impacts must not be added. Activating a UI chip is not saved as a customer preference or interaction.
