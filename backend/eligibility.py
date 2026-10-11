"""Presentation rules extend the saved ML demo's product-use-case screen.
No affordability, credit approval or institutional eligibility is inferred.
"""

from ml.eligibility import screen, missing


def assess(pid, features):
    rule = screen(pid, features)
    if pid == "GP01":
        vehicle = features.get("vehicle_ownership")
        kind = features.get("vehicle_type")
        if (vehicle == 0 and kind in ["petrol", "diesel", "electric"]) or (
            vehicle == 1 and kind == "none"
        ):
            rule["missing_or_conflicting"].append("CONFLICTING_VEHICLE_OWNERSHIP")
        if not missing(kind) and kind not in ["petrol", "diesel", "electric", "none"]:
            rule["missing_or_conflicting"].append("UNSUPPORTED_VEHICLE_TYPE")
        if vehicle == 0 and kind == "none" and features.get("replacement_intent") == 0:
            rule["missing_or_conflicting"].append(
                "NO_CONFIRMED_VEHICLE_PURCHASE_USE_CASE"
            )
    issues = rule["missing_or_conflicting"]
    if rule["applicable_exclusions"]:
        status = "EXCLUDED"
    elif any(x.startswith(("CONFLICT", "UNSUPPORTED", "NO_CONFIRMED")) for x in issues):
        status = "NEEDS_REVIEW"
    elif issues:
        status = "INSUFFICIENT_DATA"
    else:
        status = "POTENTIAL_OPPORTUNITY"
    return status, rule
