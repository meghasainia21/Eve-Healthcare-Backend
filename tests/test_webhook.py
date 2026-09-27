import threading

from tests.conftest import future_iso


def _create_pending_booking(client, headers, center, test):
    r = client.post(
        "/bookings",
        json={"center_id": center.id, "test_id": test.id, "appointment_at": future_iso()},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


def test_successful_webhook_confirms_booking(client, auth_headers, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    booking = _create_pending_booking(client, headers, center, test)

    payload = {
        "event_id": "evt_1",
        "provider_payment_id": "pay_1",
        "booking_id": booking["id"],
        "status": "SUCCESS",
    }
    r = client.post("/payments/webhook", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["received"] is True
    assert body["duplicate"] is False

    r = client.get(f"/bookings/{booking['id']}", headers=headers)
    assert r.json()["status"] == "CONFIRMED"


def test_failed_webhook_fails_booking(client, auth_headers, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    booking = _create_pending_booking(client, headers, center, test)

    payload = {
        "event_id": "evt_2",
        "provider_payment_id": "pay_2",
        "booking_id": booking["id"],
        "status": "FAILED",
    }
    r = client.post("/payments/webhook", json=payload)
    assert r.status_code == 200

    r = client.get(f"/bookings/{booking['id']}", headers=headers)
    assert r.json()["status"] == "FAILED"


def test_duplicate_webhook_event_is_idempotent(client, auth_headers, seeded_center_and_test, db_session):
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    booking = _create_pending_booking(client, headers, center, test)

    payload = {
        "event_id": "evt_dup",
        "provider_payment_id": "pay_dup",
        "booking_id": booking["id"],
        "status": "SUCCESS",
    }

    r1 = client.post("/payments/webhook", json=payload)
    assert r1.status_code == 200
    assert r1.json()["duplicate"] is False

    # Same event delivered again (and again) - must be a safe no-op.
    for _ in range(3):
        r = client.post("/payments/webhook", json=payload)
        assert r.status_code == 200
        assert r.json()["duplicate"] is True

    from app.models.payment import Payment, WebhookEvent

    assert db_session.query(Payment).filter(Payment.booking_id == booking["id"]).count() == 1
    assert db_session.query(WebhookEvent).filter(WebhookEvent.event_id == "evt_dup").count() == 1

    r = client.get(f"/bookings/{booking['id']}", headers=headers)
    assert r.json()["status"] == "CONFIRMED"


def test_webhook_same_event_sent_many_times_does_not_corrupt_state(
    client, auth_headers, seeded_center_and_test, db_session
):
    """Send the identical event 10 times; booking must end up CONFIRMED
    exactly once, with exactly one payment row."""
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    booking = _create_pending_booking(client, headers, center, test)

    payload = {
        "event_id": "evt_repeat",
        "provider_payment_id": "pay_repeat",
        "booking_id": booking["id"],
        "status": "SUCCESS",
    }

    for _ in range(10):
        client.post("/payments/webhook", json=payload)

    from app.models.booking import BookingStatus
    from app.models.payment import Payment

    payments = db_session.query(Payment).filter(Payment.booking_id == booking["id"]).all()
    assert len(payments) == 1

    r = client.get(f"/bookings/{booking['id']}", headers=headers)
    assert r.json()["status"] == BookingStatus.CONFIRMED.value


def test_webhook_unknown_booking(client):
    payload = {
        "event_id": "evt_unknown_booking",
        "provider_payment_id": "pay_x",
        "booking_id": 999999,
        "status": "SUCCESS",
    }
    r = client.post("/payments/webhook", json=payload)
    assert r.status_code == 404


def test_webhook_invalid_payload(client):
    r = client.post("/payments/webhook", json={"event_id": "evt_bad"})
    assert r.status_code == 422


def test_webhook_does_not_override_already_resolved_booking(
    client, auth_headers, seeded_center_and_test, db_session
):
    """A late-arriving/duplicate-in-spirit event for a booking that has
    already reached a final state must not flip it back."""
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    booking = _create_pending_booking(client, headers, center, test)

    # Confirm the booking via the direct payment endpoint first.
    r = client.post(
        "/payments",
        json={"booking_id": booking["id"], "simulate_status": "SUCCESS"},
        headers=headers,
    )
    assert r.json()["status"] == "SUCCESS"

    # Now a webhook for the *same booking* with a different event_id (e.g. a
    # stray/duplicate notification from the provider) arrives claiming FAILED.
    payload = {
        "event_id": "evt_late",
        "provider_payment_id": "pay_late",
        "booking_id": booking["id"],
        "status": "FAILED",
    }
    r = client.post("/payments/webhook", json=payload)
    assert r.status_code == 200
    assert r.json()["duplicate"] is False  # it's a genuinely new event...

    # ...but the booking, already CONFIRMED, must be left untouched.
    r = client.get(f"/bookings/{booking['id']}", headers=headers)
    assert r.json()["status"] == "CONFIRMED"


def test_concurrent_identical_webhooks_result_in_single_payment(
    client, auth_headers, seeded_center_and_test, db_session
):
    """Fire the same webhook event concurrently from multiple threads and
    confirm the unique constraint on event_id prevents any duplicate
    processing, even under a race."""
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    booking = _create_pending_booking(client, headers, center, test)

    payload = {
        "event_id": "evt_concurrent",
        "provider_payment_id": "pay_concurrent",
        "booking_id": booking["id"],
        "status": "SUCCESS",
    }

    results = []

    def _fire():
        r = client.post("/payments/webhook", json=payload)
        results.append(r.status_code)

    threads = [threading.Thread(target=_fire) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(code == 200 for code in results)

    from app.models.payment import Payment

    assert db_session.query(Payment).filter(Payment.booking_id == booking["id"]).count() == 1
