# Customer memory

## Purpose and boundaries

Customer memory stores explicit feedback about a synthetic customer's product recommendation. It lets the demo remember exploration, interest, dismissal, reminder, and opt-out actions after a page refresh or backend restart. This is a presentation feature only: it does not alter model predictions, propensity, confidence/reliability, use-case screening, financial eligibility, or impact calculations.

The backend remains the source of truth. `backend.store.Store` persists interaction events in SQLite; `backend.recommendations.Recommendations` reads the latest event for each customer/product pair and adds presentation fields to the existing recommendation response. The recommendation is reassembled from the saved model output and screening rules as before. No ML artifacts are changed.

## Database

`customer_interactions` is an additive SQLite table with:

| Column | Meaning |
| --- | --- |
| `id` | Increasing event identifier; breaks timestamp ties deterministically |
| `customer_id` | Existing synthetic customer identifier |
| `product_id` | One of GP01, GP02, GP03, GP04 |
| `action` | Validated feedback action |
| `reason` | Optional customer-provided short reason (up to 500 characters) |
| `created_at` | UTC timestamp for the saved event |
| `snooze_until` | UTC timestamp for a reminder, otherwise null |

An index supports fetching the latest event by customer and product. Initialization uses `CREATE TABLE IF NOT EXISTS`, before its existing snapshot-hash early return, so the migration also runs for an existing database. Refreshing imported customer snapshots does not drop this table. The application does not delete or recreate the SQLite database on startup.

## Feedback actions and presentation

The latest event for the customer/product pair controls presentation:

| Action | Presentation behavior |
| --- | --- |
| `explore` | Adds an explored indicator and modestly raises display priority |
| `interested` | Adds an interest indicator and follow-up note; normal product screening still applies |
| `dismiss` | Keeps the opportunity visible lower in the list |
| `remind_later` | Lowers its display priority until `snooze_until`; it returns to standard priority after expiry |
| `not_interested` | Hides it from the main opportunity list and places it in a reversible “Paused by your feedback” section |
| `clear` | Records an explicit reset event; the recommendation returns to standard presentation |

These actions do not change the raw `status` (use-case screening), `propensity`, threshold screen, `confidence_level`, `reliability`, `impact`, or model version. Clearing is scoped to one customer and one product; the UI offers “Undo or clear preference.” The feedback history remains available as an event log.

A reminder is a snooze/display preference only. This prototype does not send a notification, email, or future task to a relationship manager.

`presentation_status`, `presentation_priority`, `presentation_note`, and `customer_memory` are separate response fields. `recommendation_status` is preserved in the existing `status` field.

## API

### Save or update feedback

`POST /customers/{customer_id}/feedback`

```json
{
  "product_id": "GP01",
  "action": "remind_later",
  "reason": "Please ask me next month",
  "snooze_until": "2026-11-15T09:00:00Z"
}
```

The response contains the stored interaction, the newly personalized recommendation, and a message. `snooze_until` is required and must be a future timezone-aware timestamp for `remind_later`; it is rejected for other actions. Product IDs and actions are validated, and an unknown customer returns 404. Invalid request values return 422.

To update a preference, post another action for the same customer/product. The most recent event takes effect. To reset its presentation, post `{"product_id":"GP01","action":"clear"}`.

### Read history

`GET /customers/{customer_id}/feedback?offset=0&limit=50`

Returns the customer's saved events, newest first, with pagination. Invalid customers return 404.

## Privacy and access limitations

The prototype stores only product preference, optional short reason, timestamps, and the synthetic customer key. It does not store account credentials, transaction details, or free-form profiling. A reason may still contain personal information; the UI should encourage short, non-sensitive text if text entry is added. No reason text box is currently exposed by the UI.

The current hackathon API has no authentication or customer-to-session authorization. Its customer picker and data are synthetic demo profiles only. Do not connect this feedback endpoint to real customer data until authentication, authorization, retention/deletion policy, audit controls, and abuse protections are implemented. Interaction records currently have no automatic expiry; a production retention period and deletion workflow must be defined.

There is no bulk database reset endpoint. For repeatable demos, use the per-product “Undo or clear preference” control, which appends a `clear` event. The demo remains limited to the synthetic customer selected in the UI. Test suites use a temporary SQLite file and do not touch the normal application database.

## Demonstration

1. Start the backend and frontend using the repository's normal run instructions and open a synthetic customer.
2. Note the GP01 propensity, raw screening status, and impact status.
3. Choose **Dismiss**. The card moves lower and reports the preference; the displayed propensity and screening badge remain the same.
4. Refresh the page or restart the backend. The dismissal remains because it is stored in SQLite.
5. Choose **Interested** to replace the current presentation state. The opportunity returns with an interest indicator.
6. Choose **Undo or clear preference**. The normal presentation returns. The event history remains available through the feedback GET endpoint.
7. Choose **Not interested** to see it move out of the main list into the reversible paused section. Clear it there to restore normal presentation.
8. To demonstrate a snooze, select a future date and choose **Set reminder**. After its timestamp has passed, it automatically returns to standard priority on the next recommendation read.

## Tests

`tests/test_customer_memory.py` covers persistence across Store initialization and source refresh, latest-event behavior, clear/update actions, snooze expiry, validation, typed feedback endpoint handler behavior, and preservation of propensity, screening status, and impact. `frontend/tests/CustomerMemory.test.jsx` exercises user controls, refresh-driven suppression/deprioritization, undo, and reminder payloads.
