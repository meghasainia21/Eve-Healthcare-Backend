from tests.conftest import future_iso, past_iso


def test_create_booking_success(client, auth_headers, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    r = client.post(
        "/bookings",
        json={"center_id": center.id, "test_id": test.id, "appointment_at": future_iso()},
        headers=headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "PENDING"
    # Amount must come from the server-side offering, never the client.
    assert body["amount"] == "250.00"


def test_create_booking_unauthenticated(client, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    r = client.post(
        "/bookings",
        json={"center_id": center.id, "test_id": test.id, "appointment_at": future_iso()},
    )
    assert r.status_code == 401


def test_create_booking_test_not_offered_by_center(client, auth_headers, seeded_center_and_test, db_session):
    from app.models.diagnostic_test import DiagnosticTest

    center, test, offering = seeded_center_and_test
    other_test = DiagnosticTest(name="Unrelated Test")
    db_session.add(other_test)
    db_session.commit()

    headers = auth_headers()
    r = client.post(
        "/bookings",
        json={"center_id": center.id, "test_id": other_test.id, "appointment_at": future_iso()},
        headers=headers,
    )
    assert r.status_code == 400


def test_create_booking_invalid_center(client, auth_headers, seeded_center_and_test):
    _, test, _ = seeded_center_and_test
    headers = auth_headers()
    r = client.post(
        "/bookings",
        json={"center_id": 99999, "test_id": test.id, "appointment_at": future_iso()},
        headers=headers,
    )
    assert r.status_code == 404


def test_create_booking_invalid_test(client, auth_headers, seeded_center_and_test):
    center, _, _ = seeded_center_and_test
    headers = auth_headers()
    r = client.post(
        "/bookings",
        json={"center_id": center.id, "test_id": 99999, "appointment_at": future_iso()},
        headers=headers,
    )
    assert r.status_code == 404


def test_create_booking_past_appointment(client, auth_headers, seeded_center_and_test):
    center, test, _ = seeded_center_and_test
    headers = auth_headers()
    r = client.post(
        "/bookings",
        json={"center_id": center.id, "test_id": test.id, "appointment_at": past_iso()},
        headers=headers,
    )
    assert r.status_code == 400


def test_client_cannot_set_amount(client, auth_headers, seeded_center_and_test):
    """The BookingCreate schema has no `amount` field - a client-supplied
    amount must simply be ignored (or rejected as an unknown field)."""
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    r = client.post(
        "/bookings",
        json={
            "center_id": center.id,
            "test_id": test.id,
            "appointment_at": future_iso(),
            "amount": "1.00",
        },
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["amount"] == "250.00"


def test_booking_ownership_enforced(client, auth_headers, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    owner_headers = auth_headers("owner@example.com", "OwnerPass123")
    r = client.post(
        "/bookings",
        json={"center_id": center.id, "test_id": test.id, "appointment_at": future_iso()},
        headers=owner_headers,
    )
    booking_id = r.json()["id"]

    other_headers = auth_headers("other@example.com", "OtherPass123")
    r = client.get(f"/bookings/{booking_id}", headers=other_headers)
    assert r.status_code == 403

    r = client.post(f"/bookings/{booking_id}/cancel", headers=other_headers)
    assert r.status_code == 403


def test_cancel_booking(client, auth_headers, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    r = client.post(
        "/bookings",
        json={"center_id": center.id, "test_id": test.id, "appointment_at": future_iso()},
        headers=headers,
    )
    booking_id = r.json()["id"]

    r = client.post(f"/bookings/{booking_id}/cancel", headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELLED"

    # Cancelling again should fail cleanly.
    r = client.post(f"/bookings/{booking_id}/cancel", headers=headers)
    assert r.status_code == 400


def test_cancel_invalid_booking_id(client, auth_headers):
    headers = auth_headers()
    r = client.post("/bookings/99999/cancel", headers=headers)
    assert r.status_code == 404


def test_list_bookings_pagination(client, auth_headers, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    headers = auth_headers()
    for _ in range(3):
        client.post(
            "/bookings",
            json={"center_id": center.id, "test_id": test.id, "appointment_at": future_iso()},
            headers=headers,
        )

    r = client.get("/bookings?skip=0&limit=2", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
