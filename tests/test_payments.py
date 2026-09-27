from tests.conftest import future_iso


def _create_pending_booking(client, headers, center, test):
    r = client.post(
        "/bookings",
        json={"center_id": center.id, "test_id": test.id, "appointment_at": future_iso()},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


def test_successful_payment_confirms_booking(client, auth_headers, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    booking = _create_pending_booking(client, headers, center, test)

    r = client.post(
        "/payments", json={"booking_id": booking["id"], "simulate_status": "SUCCESS"}, headers=headers
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "SUCCESS"
    assert body["amount"] == "250.00"

    r = client.get(f"/bookings/{booking['id']}", headers=headers)
    assert r.json()["status"] == "CONFIRMED"


def test_failed_payment_fails_booking(client, auth_headers, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    booking = _create_pending_booking(client, headers, center, test)

    r = client.post(
        "/payments", json={"booking_id": booking["id"], "simulate_status": "FAILED"}, headers=headers
    )
    assert r.status_code == 201
    assert r.json()["status"] == "FAILED"

    r = client.get(f"/bookings/{booking['id']}", headers=headers)
    assert r.json()["status"] == "FAILED"


def test_payment_invalid_booking(client, auth_headers):
    headers = auth_headers()
    r = client.post("/payments", json={"booking_id": 99999}, headers=headers)
    assert r.status_code == 404


def test_payment_ownership_enforced(client, auth_headers, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    owner_headers = auth_headers("owner@example.com", "OwnerPass123")
    booking = _create_pending_booking(client, owner_headers, center, test)

    other_headers = auth_headers("other@example.com", "OtherPass123")
    r = client.post("/payments", json={"booking_id": booking["id"]}, headers=other_headers)
    assert r.status_code == 403


def test_duplicate_payment_attempt_rejected(client, auth_headers, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    booking = _create_pending_booking(client, headers, center, test)

    r1 = client.post(
        "/payments", json={"booking_id": booking["id"], "simulate_status": "SUCCESS"}, headers=headers
    )
    assert r1.status_code == 201

    r2 = client.post("/payments", json={"booking_id": booking["id"]}, headers=headers)
    assert r2.status_code == 400


def test_payment_amount_is_server_determined(client, auth_headers, seeded_center_and_test):
    """Even if a client tried to smuggle an amount into the payment
    request, PaymentCreate has no such field - the amount always comes
    from the booking record."""
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    booking = _create_pending_booking(client, headers, center, test)

    r = client.post(
        "/payments",
        json={"booking_id": booking["id"], "amount": "1.00", "simulate_status": "SUCCESS"},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["amount"] == booking["amount"] == "250.00"


def test_get_payment_ownership(client, auth_headers, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    owner_headers = auth_headers("owner@example.com", "OwnerPass123")
    booking = _create_pending_booking(client, owner_headers, center, test)
    r = client.post(
        "/payments", json={"booking_id": booking["id"], "simulate_status": "SUCCESS"}, headers=owner_headers
    )
    payment_id = r.json()["id"]

    r = client.get(f"/payments/{payment_id}", headers=owner_headers)
    assert r.status_code == 200

    other_headers = auth_headers("other@example.com", "OtherPass123")
    r = client.get(f"/payments/{payment_id}", headers=other_headers)
    assert r.status_code == 403


def test_get_invalid_payment_id(client, auth_headers):
    headers = auth_headers()
    r = client.get("/payments/99999", headers=headers)
    assert r.status_code == 404
