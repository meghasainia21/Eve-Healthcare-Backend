def test_list_centers_empty(client):
    r = client.get("/diagnostic-centers")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["items"] == []


def test_list_centers(client, seeded_center_and_test):
    r = client.get("/diagnostic-centers")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Test Diagnostics"


def test_center_details_with_tests(client, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    r = client.get(f"/diagnostic-centers/{center.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Test Diagnostics"
    assert len(body["tests"]) == 1
    assert body["tests"][0]["test_name"] == "Sample Test"
    assert body["tests"][0]["price"] == "250.00"


def test_center_tests_endpoint(client, seeded_center_and_test):
    center, test, offering = seeded_center_and_test
    r = client.get(f"/diagnostic-centers/{center.id}/tests")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["test_id"] == test.id


def test_invalid_center_id(client):
    r = client.get("/diagnostic-centers/99999")
    assert r.status_code == 404


def test_invalid_center_tests_id(client):
    r = client.get("/diagnostic-centers/99999/tests")
    assert r.status_code == 404


def test_list_tests(client, seeded_center_and_test):
    r = client.get("/diagnostic-tests")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_create_center_requires_admin(client, auth_headers):
    headers = auth_headers()
    r = client.post(
        "/diagnostic-centers",
        json={"name": "New Center", "location": "Somewhere", "offerings": []},
        headers=headers,
    )
    assert r.status_code == 403


def test_create_center_as_admin(client, admin_headers):
    headers = admin_headers()
    r = client.post(
        "/diagnostic-tests",
        json={"name": "X-Ray Chest"},
        headers=headers,
    )
    assert r.status_code == 201
    test_id = r.json()["id"]

    r = client.post(
        "/diagnostic-centers",
        json={
            "name": "New Center",
            "location": "Somewhere",
            "offerings": [{"test_id": test_id, "price": "500.00"}],
        },
        headers=headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["tests"][0]["price"] == "500.00"


def test_create_test_requires_admin(client, auth_headers):
    headers = auth_headers()
    r = client.post("/diagnostic-tests", json={"name": "MRI"}, headers=headers)
    assert r.status_code == 403


def test_create_duplicate_test_name(client, admin_headers):
    headers = admin_headers()
    client.post("/diagnostic-tests", json={"name": "MRI Scan"}, headers=headers)
    r = client.post("/diagnostic-tests", json={"name": "MRI Scan"}, headers=headers)
    assert r.status_code == 409
