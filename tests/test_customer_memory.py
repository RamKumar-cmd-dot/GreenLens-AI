from datetime import datetime, timedelta, timezone
import pandas as pd
import pytest

from backend.schemas import Impact, Recommendation
from backend.store import Store
from backend.recommendations import Recommendations


CID = "C_TEST_001"


def make_data_dir(path):
    processed = path / "processed"
    synthetic = path / "synthetic"
    processed.mkdir(parents=True)
    synthetic.mkdir(parents=True)
    pd.DataFrame([{
        "customer_id": CID, "region": "London", "age_band": "30-44",
        "data_timestamp": "2026-01-01", "homeowner": 1,
    }]).to_csv(processed / "customer_360.csv", index=False)
    pd.DataFrame([{
        "transaction_id": "T1", "customer_id": CID, "transaction_date": "2025-01-01",
        "sustainability_category": "Fuel", "amount_gbp": 10,
    }]).to_csv(synthetic / "transactions.csv", index=False)
    pd.DataFrame([{
        "customer_id": CID, "product_type": "Current Account", "product_status": "active",
        "start_date": "2020-01-01", "end_date": "",
    }]).to_csv(synthetic / "customer_products.csv", index=False)
    return path


def base_recommendation():
    return Recommendation(
        customer_id=CID, product_id="GP01", product_name="EV Finance", propensity=.73,
        threshold_screen={"threshold": .24, "above_threshold": True}, confidence=None,
        confidence_level="medium", reliability={"scope": "synthetic_validation_only"},
        status="POTENTIAL_OPPORTUNITY", applicable_exclusions=[], missing_or_conflicting=[],
        reason_codes=["EXISTING_PETROL_VEHICLE"], evidence={"vehicle_type": "petrol"},
        data_timestamp="2026-01-01", model_version="test-v1", impact=Impact(impact_status="UNAVAILABLE"),
        recommended_action="Review with a relationship team.",
    )


def presenter(store):
    service = Recommendations.__new__(Recommendations)
    service.store = store
    return service


def test_interaction_history_persists_across_restarts_and_source_refreshes(tmp_path, monkeypatch):
    import backend.store as store_module
    data = make_data_dir(tmp_path / "data")
    monkeypatch.setattr(store_module, "DATA", data)
    db_path = tmp_path / "greenlens.sqlite"
    first = Store(db_path)
    first.initialize()
    first.record_interaction(CID, "GP01", "dismiss", "Not now")
    original_count = first.interaction_history(CID)["total"]

    # An application restart with unchanged data is idempotent.
    restarted = Store(db_path)
    restarted.initialize()
    assert restarted.interaction_history(CID)["total"] == original_count == 1

    # A changed imported snapshot may refresh customer tables but keeps memory.
    features_path = data / "processed/customer_360.csv"
    features = pd.read_csv(features_path)
    features["homeowner"] = 0
    features.to_csv(features_path, index=False)
    refreshed = Store(db_path)
    refreshed.initialize()
    assert refreshed.customer(CID)["features"]["homeowner"] == 0
    assert refreshed.interaction_history(CID)["total"] == 1


def test_latest_action_controls_presentation_and_never_mutates_prediction_or_status(tmp_path, monkeypatch):
    import backend.store as store_module
    monkeypatch.setattr(store_module, "DATA", make_data_dir(tmp_path / "data"))
    store = Store(tmp_path / "db.sqlite")
    store.initialize()
    service = presenter(store)
    original = base_recommendation()

    store.record_interaction(CID, "GP01", "not_interested", "Not for me")
    suppressed = service._with_memory(CID, original)
    assert suppressed.presentation_status == "SUPPRESSED"

    store.record_interaction(CID, "GP01", "interested")
    interested = service._with_memory(CID, original)
    assert interested.presentation_status == "INTERESTED"
    assert interested.customer_memory["action"] == "interested"
    assert interested.propensity == original.propensity
    assert interested.status == original.status
    assert interested.financial_eligibility == original.financial_eligibility
    assert interested.confidence_level == original.confidence_level
    assert interested.threshold_screen == original.threshold_screen
    assert interested.impact == original.impact
    assert store.interaction_history(CID)["total"] == 2

    store.record_interaction(CID, "GP01", "clear")
    cleared = service._with_memory(CID, original)
    assert cleared.presentation_status == "STANDARD"
    assert "cleared" in cleared.presentation_note.lower()
    assert cleared.propensity == original.propensity and cleared.status == original.status


def test_dismiss_and_snooze_expiry_only_affect_presentation(tmp_path, monkeypatch):
    import backend.store as store_module
    monkeypatch.setattr(store_module, "DATA", make_data_dir(tmp_path / "data"))
    store = Store(tmp_path / "db.sqlite")
    store.initialize()
    service = presenter(store)
    original = base_recommendation()

    store.record_interaction(CID, "GP01", "dismiss")
    dismissed = service._with_memory(CID, original)
    assert dismissed.presentation_status == "DEPRIORITIZED"
    assert dismissed.presentation_priority < 100

    future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    store.record_interaction(CID, "GP01", "remind_later", snooze_until=future)
    snoozed = service._with_memory(CID, original)
    assert snoozed.presentation_status == "SNOOZED"
    assert snoozed.status == original.status and snoozed.propensity == original.propensity

    with store.connect() as db:
        db.execute("UPDATE customer_interactions SET snooze_until=? WHERE customer_id=? AND product_id=? AND action='remind_later'", ("2000-01-01T00:00:00Z", CID, "GP01"))
    expired = service._with_memory(CID, original)
    assert expired.presentation_status == "STANDARD"
    assert expired.presentation_priority == 100
    assert "passed" in expired.presentation_note


def test_store_rejects_invalid_customer_product_action_and_snooze(tmp_path, monkeypatch):
    import backend.store as store_module
    monkeypatch.setattr(store_module, "DATA", make_data_dir(tmp_path / "data"))
    store = Store(tmp_path / "db.sqlite")
    store.initialize()
    with pytest.raises(KeyError):
        store.record_interaction("unknown", "GP01", "dismiss")
    with pytest.raises(ValueError):
        store.record_interaction(CID, "GP99", "dismiss")
    with pytest.raises(ValueError):
        store.record_interaction(CID, "GP01", "bad-action")
    with pytest.raises(ValueError):
        store.record_interaction(CID, "GP01", "remind_later")
    with pytest.raises(ValueError):
        store.record_interaction(CID, "GP01", "remind_later", snooze_until="2000-01-01T00:00:00Z")


def test_feedback_api_validates_and_returns_updated_typed_recommendation(tmp_path, monkeypatch):
    import backend.app as app_module
    import backend.store as store_module

    monkeypatch.setattr(store_module, "DATA", make_data_dir(tmp_path / "data"))

    class SmallRecommendations:
        def __init__(self, store):
            self.store = store
            self.base = base_recommendation()
            self.present = presenter(store)

        def customer(self, cid):
            if not self.store.customer_exists(cid):
                raise KeyError(cid)
            return {"customer_id": cid, "opportunities": [self.present._with_memory(cid, self.base)]}

    monkeypatch.setattr(app_module, "Recommendations", SmallRecommendations)
    app = app_module.create_app(tmp_path / "api.sqlite")
    store = Store(tmp_path / "api.sqlite")
    store.initialize()
    app.state.store = store
    app.state.data_available = True
    app.state.service = SmallRecommendations(store)

    feedback_routes = [route for route in app.routes if getattr(route, "path", None) == "/customers/{customer_id}/feedback"]
    post = next(route.endpoint for route in feedback_routes if "POST" in route.methods)
    get = next(route.endpoint for route in feedback_routes if "GET" in route.methods)
    body = app_module.FeedbackRequest(product_id="GP01", action="dismiss")
    response = post(CID, body)
    payload = app_module.FeedbackResponse.model_validate(response)
    assert payload.recommendation.presentation_status == "DEPRIORITIZED"
    assert payload.recommendation.propensity == .73
    assert payload.recommendation.status == "POTENTIAL_OPPORTUNITY"
    history = app_module.CustomerInteractionPage.model_validate(get(CID, offset=0, limit=50))
    assert history.total == 1 and history.items[0].action == "dismiss"
    with pytest.raises(app_module.HTTPException) as unknown:
        post("unknown", body)
    assert unknown.value.status_code == 404
    from pydantic import ValidationError
    for invalid in [
        {"product_id": "GP99", "action": "dismiss"},
        {"product_id": "GP01", "action": "bogus"},
        {"product_id": "GP01", "action": "remind_later"},
    ]:
        with pytest.raises(ValidationError):
            app_module.FeedbackRequest(**invalid)
    clear = app_module.FeedbackRequest(product_id="GP01", action="clear")
    cleared = app_module.FeedbackResponse.model_validate(post(CID, clear))
    assert cleared.recommendation.presentation_status == "STANDARD"
