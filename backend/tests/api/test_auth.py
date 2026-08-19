def test_register_login_me_flow(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "password": "StrongPass123!", "full_name": "Alice"},
    )
    assert r.status_code == 201
    tokens = r.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200
    assert r.json()["email"] == "alice@example.com"
    assert r.json()["role"] == "investor"


def test_register_duplicate_email_conflicts(client):
    payload = {"email": "bob@example.com", "password": "StrongPass123!", "full_name": "Bob"}
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "conflict"


def test_login_wrong_password_is_401(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "carol@example.com", "password": "StrongPass123!", "full_name": "Carol"},
    )
    r = client.post("/api/v1/auth/login", json={"email": "carol@example.com", "password": "nope"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_me_without_token_is_401(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_refresh_returns_new_working_access_token(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "dave@example.com", "password": "StrongPass123!", "full_name": "Dave"},
    )
    refresh_token = r.json()["refresh_token"]

    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    new_access = r.json()["access_token"]

    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert r.status_code == 200


def test_change_password_then_login_with_new_password(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "erin@example.com", "password": "OldPass123!", "full_name": "Erin"},
    )
    access = r.json()["access_token"]

    r = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {access}"},
        json={"current_password": "OldPass123!", "new_password": "NewPass123!"},
    )
    assert r.status_code == 204

    r = client.post("/api/v1/auth/login", json={"email": "erin@example.com", "password": "OldPass123!"})
    assert r.status_code == 401

    r = client.post("/api/v1/auth/login", json={"email": "erin@example.com", "password": "NewPass123!"})
    assert r.status_code == 200


def test_change_password_wrong_current_is_401(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "frank@example.com", "password": "OldPass123!", "full_name": "Frank"},
    )
    access = r.json()["access_token"]

    r = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {access}"},
        json={"current_password": "totally wrong", "new_password": "NewPass123!"},
    )
    assert r.status_code == 401
