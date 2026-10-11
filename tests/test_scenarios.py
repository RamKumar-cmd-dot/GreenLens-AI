import pandas as pd
import numpy as np
import pytest
from fastapi import HTTPException

from backend.app import create_app
from backend import recommendations as recommendation_module
from backend.eligibility import assess
from backend.impact import estimate
from backend.recommendations import Recommendations
from backend.scenarios import SCENARIO_PRESETS, normalize_selection
from backend.schemas import Impact, Recommendation, ScenarioRequest, ScenarioResponse
from ml.common import FEATURES, TARGETS
from ml.inference import reasons

CID = "C_SCENARIO_TEST"


def profile(region="London"):
    values = {key: 0 for key in FEATURES}
    values.update(
        {
            "customer_id": CID,
            "data_timestamp": "2026-01-01",
            "region": region,
            "age_band": "30-44",
            "employment_status": "employed",
            "property_type": "terraced",
            "vehicle_type": "petrol",
            "heating_technology": "gas_boiler",
            "homeowner": 0,
            "vehicle_ownership": 1,
            "owns_ev": 0,
            "annual_mileage_estimate": 10000,
            "electricity_kwh_year": 4000,
            "gas_kwh_year": 8000,
            "roof_suitable": 0,
            "replacement_intent": 1,
            "paper_statements_enabled": 1,
            "mean_monthly_fuel": 150,
            "digital_logins_month": 18,
            "digital_transaction_ratio": 0.7,
        }
    )
    return values


class CountingModel:
    def __init__(self, score=0.61):
        self.score = score
        self.rows = []

    def predict_proba(self, frame):
        self.rows.append(frame.copy(deep=True))
        return np.array([[1 - self.score, self.score]])


class MemoryStore:
    def __init__(self):
        self.reads = 0

    def latest_interaction(self, *_):
        self.reads += 1
        return None


def fake_assemble(features, pid, score, metadata, threshold):
    status, rules = assess(pid, features)
    codes, evidence = reasons(pid, features)
    impact = (
        estimate(pid, features)
        if status == "POTENTIAL_OPPORTUNITY"
        else Impact(
            impact_status="UNAVAILABLE",
            reason="Screening excludes this scenario or requires more information.",
        )
    )
    return Recommendation(
        customer_id=features["customer_id"],
        product_id=pid,
        product_name={
            "GP01": "EV Finance",
            "GP02": "Green Home Loan",
            "GP03": "Solar Finance",
            "GP04": "Paperless Banking",
        }[pid],
        propensity=score,
        threshold_screen={
            "threshold": threshold,
            "above_threshold": score >= threshold,
        },
        confidence=None,
        confidence_level="medium",
        reliability={"scope": "test"},
        status=status,
        applicable_exclusions=rules["applicable_exclusions"],
        missing_or_conflicting=rules["missing_or_conflicting"],
        reason_codes=codes,
        evidence=evidence,
        data_timestamp=features["data_timestamp"],
        model_version="test-v1",
        impact=impact,
        recommended_action="Illustrative only.",
    )


def service_for(monkeypatch, customer=None):
    monkeypatch.setattr(recommendation_module, "assemble", fake_assemble)
    row = customer or profile()
    service = Recommendations.__new__(Recommendations)
    service.store = MemoryStore()
    service.features = pd.DataFrame(
        [row], columns=list(dict.fromkeys([*FEATURES, "customer_id", "data_timestamp"]))
    )
    service.models = {
        "metadata": {"products": {pid: {} for pid in TARGETS}},
        "thresholds": {pid: 0.25 for pid in TARGETS},
        "confidence_reference": None,
        **{pid: CountingModel() for pid in TARGETS},
    }
    service.by_customer = {
        CID: [
            fake_assemble(row, pid, 0.4, service.models["metadata"], 0.25)
            for pid in TARGETS
        ]
    }
    return service


def run(service, chips):
    return ScenarioResponse.model_validate(service.scenario(CID, chips))


def test_request_accepts_empty_deduplicates_and_legacy_buttons():
    assert ScenarioRequest(apply=[]).apply == []
    assert ScenarioRequest(apply=["EV", "SOLAR", "EV"]).apply == ["EV", "SOLAR"]
    assert ScenarioRequest(changes={"paper_statements_enabled": 0}).apply == [
        "PAPERLESS"
    ]
    assert ScenarioRequest(
        changes={
            "vehicle_ownership": 1,
            "vehicle_type": "electric",
            "owns_ev": 1,
            "replacement_intent": 0,
        }
    ).apply == ["EV"]
    with pytest.raises(ValueError):
        ScenarioRequest(apply=["INVALID"])
    with pytest.raises(ValueError):
        ScenarioRequest(apply=["EV"], changes={})
    with pytest.raises(ValueError):
        ScenarioRequest(changes={"ev_finance_takeup": 1})


@pytest.mark.parametrize(
    "chip,expected",
    [
        (
            "EV",
            {
                "vehicle_ownership": 1,
                "vehicle_type": "electric",
                "owns_ev": 1,
                "replacement_intent": 0,
            },
        ),
        ("GREEN_HOME", {"homeowner": 1, "heating_technology": "gas_boiler"}),
        ("SOLAR", {"homeowner": 1, "roof_suitable": 1}),
        ("PAPERLESS", {"paper_statements_enabled": 0}),
    ],
)
def test_each_chip_has_documented_preset_and_expected_changes(
    monkeypatch, chip, expected
):
    service = service_for(monkeypatch)
    result = run(service, [chip])
    assert result.applied_chips == [chip]
    assert {key: result.scenario_changes[key] for key in expected} == expected
    assert result.changed_attributes == {
        key: value for key, value in expected.items() if profile().get(key) != value
    }
    assert len(result.comparisons) == 4
    assert result.disclaimers and result.chip_notes[0].chip_id == chip
    assert SCENARIO_PRESETS[chip]["meaning"]


def test_ev_solar_combination_is_one_merged_model_call_per_product_and_excludes_existing_ev(
    monkeypatch,
):
    original = profile()
    service = service_for(monkeypatch, original)
    result = run(service, ["EV", "SOLAR"])
    assert result.applied_chips == ["EV", "SOLAR"]
    assert result.changed_attributes == {
        "vehicle_type": "electric",
        "owns_ev": 1,
        "replacement_intent": 0,
        "homeowner": 1,
        "roof_suitable": 1,
    }
    assert all(len(service.models[pid].rows) == 1 for pid in TARGETS)
    merged = service.models["GP03"].rows[0].iloc[0]
    assert (
        merged["vehicle_type"] == "electric"
        and merged["roof_suitable"] == 1
        and merged["homeowner"] == 1
    )
    assert service.by_customer[CID][0].status == "POTENTIAL_OPPORTUNITY"
    assert result.comparisons[0].scenario.status == "EXCLUDED"
    assert "EXISTING_EV_NO_REPLACEMENT" in result.opportunities[0].applicable_exclusions
    assert original["vehicle_type"] == "petrol" and original["homeowner"] == 0
    assert (
        service.features.iloc[0]["vehicle_type"] == "petrol"
        and service.features.iloc[0]["homeowner"] == 0
    )
    assert service.store.reads == 0


def test_all_chips_and_paperless_exclusion(monkeypatch):
    service = service_for(monkeypatch)
    result = run(service, ["EV", "GREEN_HOME", "SOLAR", "PAPERLESS"])
    assert result.applied_chips == ["EV", "GREEN_HOME", "SOLAR", "PAPERLESS"]
    by_id = {item.product_id: item for item in result.opportunities}
    assert by_id["GP01"].status == "EXCLUDED"
    assert by_id["GP04"].status == "EXCLUDED"
    assert by_id["GP02"].status == "POTENTIAL_OPPORTUNITY"
    assert by_id["GP03"].status == "POTENTIAL_OPPORTUNITY"
    assert "ALREADY_PAPERLESS" in by_id["GP04"].applicable_exclusions


def test_no_change_notes_and_empty_baseline_are_returned(monkeypatch):
    row = profile()
    row.update(
        {
            "homeowner": 1,
            "roof_suitable": 1,
            "paper_statements_enabled": 0,
            "owns_ev": 1,
            "vehicle_type": "electric",
            "replacement_intent": 0,
        }
    )
    service = service_for(monkeypatch, row)
    result = run(service, ["EV", "SOLAR", "PAPERLESS", "GREEN_HOME"])
    assert result.changed_attributes == {}
    assert all(
        note.note.startswith("No customer features changed:")
        for note in result.chip_notes[:3]
    )
    baseline = run(service, [])
    assert (
        baseline.applied_chips == []
        and baseline.scenario_changes == {}
        and baseline.changed_attributes == {}
    )
    assert len(baseline.opportunities) == 4


def test_later_chip_wins_when_presets_overlap(monkeypatch):
    service = service_for(monkeypatch)
    monkeypatch.setitem(SCENARIO_PRESETS["PAPERLESS"], "overrides", {"homeowner": 0})
    solar_then_paperless = run(service, ["SOLAR", "PAPERLESS"])
    paperless_then_solar = run(service, ["PAPERLESS", "SOLAR"])
    assert solar_then_paperless.scenario_changes["homeowner"] == 0
    assert paperless_then_solar.scenario_changes["homeowner"] == 1


def test_solar_uses_only_supported_london_yield_and_requires_demand(monkeypatch):
    london = service_for(monkeypatch)
    london_result = run(london, ["SOLAR"])
    solar = next(
        item for item in london_result.opportunities if item.product_id == "GP03"
    )
    assert solar.impact.impact_status == "ESTIMATED"
    assert solar.impact.generation_kwh is not None

    outside = service_for(monkeypatch, profile("Scotland"))
    outside_result = run(outside, ["SOLAR"])
    outside_impact = next(
        item for item in outside_result.opportunities if item.product_id == "GP03"
    ).impact
    assert outside_impact.impact_status == "UNAVAILABLE"
    assert "reference yield" in outside_impact.reason
    assert "regional PV impact remains unavailable" in outside_result.chip_notes[0].note

    missing = profile()
    missing["electricity_kwh_year"] = None
    missing_service = service_for(monkeypatch, missing)
    missing_result = run(missing_service, ["SOLAR"])
    missing_impact = next(
        item for item in missing_result.opportunities if item.product_id == "GP03"
    ).impact
    assert missing_impact.impact_status == "UNAVAILABLE"
    assert "electricity demand" in missing_impact.reason


def test_unknown_customer_and_request_order_validation(monkeypatch):
    service = service_for(monkeypatch)
    with pytest.raises(KeyError):
        service.scenario("C_UNKNOWN", ["EV"])
    assert normalize_selection(["EV", "EV", "PAPERLESS"]) == ["EV", "PAPERLESS"]
    with pytest.raises(ValueError):
        normalize_selection(["BAD"])


def test_fastapi_scenario_route_returns_typed_json_and_404(monkeypatch):
    service = service_for(monkeypatch)
    app = create_app()
    app.state.service = service
    route = next(
        route
        for route in app.routes
        if getattr(route, "path", None) == "/customers/{customer_id}/scenario"
    )
    response = ScenarioResponse.model_validate(
        route.endpoint(CID, ScenarioRequest(apply=["EV", "SOLAR"]))
    )
    payload = response.model_dump(mode="json")
    assert payload["applied_chips"] == ["EV", "SOLAR"]
    assert len(payload["comparisons"]) == 4
    with pytest.raises(HTTPException) as unknown:
        route.endpoint("C_UNKNOWN", ScenarioRequest(apply=[]))
    assert getattr(unknown.value, "status_code", None) == 404


def test_missing_original_override_serializes_as_json_null(monkeypatch):
    row = profile()
    row["vehicle_ownership"] = None
    result = run(service_for(monkeypatch, row), ["EV"])
    assert result.original_attributes["vehicle_ownership"] is None
    assert '"vehicle_ownership":null' in result.model_dump_json()
