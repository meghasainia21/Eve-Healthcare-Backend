def test_signup_success(client):
    r = client.post(
        "/auth/signup",
        json={"name": "Alice", "email": "alice@example.com", "password": "AlicePass123"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "alice@example.com"
    assert body["role"] == "USER"
    assert "password" not in body
    assert "password_hash" not in body


def test_signup_duplicate_email(client):
    payload = {"name": "Alice", "email": "alice@example.com", "password": "AlicePass123"}
    client.post("/auth/signup", json=payload)
    r = client.post("/auth/signup", json=payload)
    assert r.status_code == 409


def test_signup_invalid_payload(client):
    r = client.post("/auth/signup", json={"name": "Alice", "email": "not-an-email", "password": "x"})
    assert r.status_code == 422


def test_login_success(client):
    client.post(
        "/auth/signup",
        json={"name": "Bob", "email": "bob@example.com", "password": "BobPass123"},
    )
    r = client.post("/auth/login", json={"email": "bob@example.com", "password": "BobPass123"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "bob@example.com"


def test_login_wrong_password(client):
    client.post(
        "/auth/signup",
        json={"name": "Bob", "email": "bob@example.com", "password": "BobPass123"},
    )
    r = client.post("/auth/login", json={"email": "bob@example.com", "password": "WrongPass1"})
    assert r.status_code == 401


def test_login_unknown_email(client):
    r = client.post("/auth/login", json={"email": "ghost@example.com", "password": "whatever"})
    assert r.status_code == 401


def test_protected_route_without_token(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_protected_route_with_invalid_token(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    headers = auth_headers("carol@example.com", "CarolPass123")
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "carol@example.com"
