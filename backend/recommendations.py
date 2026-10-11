from datetime import datetime, timezone
import pandas as pd
from ml.common import FEATURES, TARGETS, VERSION
from ml.eligibility import CATALOGUE, screen, missing
from ml.inference import load_models, reasons, normalize, validation_score_band
from ml.confidence import assess_reliability
from backend.schemas import Recommendation, Impact
from backend.impact import estimate
from backend.eligibility import assess
from backend.scenarios import SCENARIO_PRESETS, normalize_selection


def assemble(features, pid, score, metadata, threshold=None):
    if threshold is None:
        threshold = load_models()["thresholds"][pid]
    features = {**features, **normalize(features)}
    status, rule = assess(pid, features)
    # Keep use-case screening distinct from credit approval and model probability.
    issues = rule["missing_or_conflicting"]
    codes, evidence = reasons(pid, features)
    action = {
        "EXCLUDED": "Review the exclusion; no application is suggested.",
        "INSUFFICIENT_DATA": "Confirm the missing information with your relationship team.",
        "NEEDS_REVIEW": "Resolve conflicting information before considering this product.",
        "POTENTIAL_OPPORTUNITY": "Explore the illustrative scenario with your relationship team; institutional checks still apply.",
    }[status]
    reliability_assessment = assess_reliability(
        pid, features, score, load_models().get("confidence_reference"), issues
    )
    return Recommendation(
        customer_id=features["customer_id"],
        product_id=pid,
        product_name=CATALOGUE[pid]["name"],
        propensity=score,
        threshold_screen={
            "threshold": threshold,
            "above_threshold": score >= threshold,
            "status": (
                "ABOVE_VALIDATION_SELECTED_THRESHOLD"
                if score >= threshold
                else "BELOW_VALIDATION_SELECTED_THRESHOLD"
            ),
            "selection_basis": "validation-set F1; statistical prioritization only",
        },
        confidence=None,
        confidence_level=reliability_assessment["confidence_level"],
        confidence_method=reliability_assessment["confidence_method"],
        reliability={
            **reliability_assessment["reliability"],
            **metadata["products"][pid],
            "status": "validation_informed_synthetic_reliability",
            "per_customer_confidence": "unavailable",
            "validation_score_band": reliability_assessment["reliability"][
                "details"
            ].get("validation_score_band", validation_score_band(pid, score)),
            "missing_feature_count": sum(missing(features.get(k)) for k in FEATURES),
        },
        status=status,
        applicable_exclusions=rule["applicable_exclusions"],
        missing_or_conflicting=issues,
        reason_codes=codes,
        evidence=evidence,
        data_timestamp=features["data_timestamp"],
        model_version=VERSION,
        impact=(
            estimate(pid, features)
            if status == "POTENTIAL_OPPORTUNITY"
            else Impact(
                impact_status="UNAVAILABLE",
                reason="Use-case screening excludes this scenario or requires more information",
            )
        ),
        recommended_action=action,
    )


class Recommendations:
    def __init__(self, store):
        self.store = store
        self.models = load_models()
        self.features = store.all_features()
        self.by_customer = {}
        scores = {
            pid: self.models[pid].predict_proba(self.features[FEATURES])[:, 1]
            for pid in TARGETS
        }
        for i, row in self.features.iterrows():
            f = row.to_dict()
            self.by_customer[f["customer_id"]] = [
                assemble(
                    f,
                    pid,
                    float(scores[pid][i]),
                    self.models["metadata"],
                    self.models["thresholds"][pid],
                )
                for pid in TARGETS
            ]

    def customer(self, cid):
        if cid not in self.by_customer:
            raise KeyError(cid)
        return {
            "customer_id": cid,
            "opportunities": [
                self._with_memory(cid, row) for row in self.by_customer[cid]
            ],
        }

    def _with_memory(self, cid, recommendation):
        interaction = self.store.latest_interaction(cid, recommendation.product_id)
        update = {
            "presentation_status": "STANDARD",
            "presentation_priority": 100,
            "presentation_note": None,
            "customer_memory": {},
        }
        if interaction is None:
            return recommendation.model_copy(update=update)

        action = interaction["action"]
        memory = {
            key: interaction[key]
            for key in ("action", "reason", "created_at", "snooze_until")
        }
        update["customer_memory"] = memory
        if action == "clear":
            update["presentation_note"] = (
                "Your previous preference was cleared; the standard recommendation is shown."
            )
        elif action == "explore":
            update.update(
                presentation_status="EXPLORED",
                presentation_priority=105,
                presentation_note="You explored this opportunity previously.",
            )
        elif action == "interested":
            update.update(
                presentation_status="INTERESTED",
                presentation_priority=120,
                presentation_note="You marked this opportunity as interesting. Product checks still apply.",
            )
        elif action == "dismiss":
            update.update(
                presentation_status="DEPRIORITIZED",
                presentation_priority=40,
                presentation_note="You dismissed this opportunity; it is shown lower in the list. Update or clear your preference any time.",
            )
        elif action == "not_interested":
            update.update(
                presentation_status="SUPPRESSED",
                presentation_priority=0,
                presentation_note="You asked not to see proactive reminders for this product. The underlying screening result is unchanged.",
            )
        elif action == "remind_later":
            snooze_until = datetime.fromisoformat(
                interaction["snooze_until"].replace("Z", "+00:00")
            )
            if snooze_until > datetime.now(timezone.utc):
                update.update(
                    presentation_status="SNOOZED",
                    presentation_priority=10,
                    presentation_note=f'Reminder requested for {interaction["snooze_until"]}; this item is shown lower until then.',
                )
            else:
                update["presentation_note"] = (
                    "Your reminder date passed; this opportunity is visible at its standard priority again."
                )
        return recommendation.model_copy(update=update)

    def scenario(self, cid, apply=None, changes=None):
        # Preserve direct callers of the former scenario(cid, changes) method.
        if isinstance(apply, dict) and changes is None:
            changes, apply = apply, None
        chips = normalize_selection(apply, changes)
        if cid not in self.by_customer:
            raise KeyError(cid)
        original = self.features.loc[self.features.customer_id == cid].iloc[0].to_dict()
        merged = dict(original)
        overrides = {}
        notes = []
        for chip in chips:
            preset = SCENARIO_PRESETS[chip]
            changed = []
            for key, value in preset["overrides"].items():
                before = merged.get(key)
                if not _same_value(before, value):
                    changed.append(key)
                merged[key] = value
                overrides[key] = value
            note = preset["meaning"]
            if not changed:
                note = f'No customer features changed: this profile already matches the {preset["label"]} preset. {note}'
            if chip == "SOLAR" and original.get("region") != "London":
                note += " The regional PV impact remains unavailable because this profile has no supported regional yield."
            notes.append({"chip_id": chip, "changed_features": changed, "note": note})
        changed_attributes = {
            key: value
            for key, value in overrides.items()
            if key in original and not _same_value(original.get(key), value)
        }
        original_attributes = {
            key: _json_scalar(original[key]) for key in changed_attributes
        }
        f = {**merged, **normalize(merged)}
        row = pd.DataFrame([f], columns=FEATURES)
        baseline_recommendations = self.by_customer[cid]
        predictions = []
        comparisons = []
        for pid, baseline in zip(TARGETS, baseline_recommendations):
            score = float(self.models[pid].predict_proba(row)[0, 1])
            scenario = assemble(
                f, pid, score, self.models["metadata"], self.models["thresholds"][pid]
            )
            predictions.append(scenario)
            comparisons.append(
                {
                    "product_id": pid,
                    "product_name": scenario.product_name,
                    "baseline": _scenario_side(baseline),
                    "scenario": _scenario_side(scenario),
                }
            )
        return {
            "customer_id": cid,
            "opportunities": predictions,
            "scenario_changes": overrides,
            "applied_chips": chips,
            "changed_attributes": changed_attributes,
            "original_attributes": original_attributes,
            "chip_notes": notes,
            "comparisons": comparisons,
            "disclaimers": [
                "This is a hypothetical synthetic customer state; no stored profile or customer preference was changed.",
                "Propensity differences are model responses to changed inputs, not causal estimates of intervention effects or take-up.",
                "Use-case screening is not financial eligibility or credit approval.",
                "Environmental outputs are deterministic conditional scenarios, not realized savings; impacts across products are separate and must not be added.",
            ],
            "synthetic": True,
        }


def _same_value(left, right):
    try:
        if pd.isna(left) and pd.isna(right):
            return True
    except (TypeError, ValueError):
        pass
    try:
        return bool(left == right)
    except (TypeError, ValueError):
        return False


def _json_scalar(value):
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value.item() if hasattr(value, "item") else value


def _scenario_side(recommendation):
    return {
        "propensity": recommendation.propensity,
        "status": recommendation.status,
        "confidence_level": recommendation.confidence_level,
        "reason_codes": recommendation.reason_codes,
        "evidence": recommendation.evidence,
        "impact": recommendation.impact,
    }
