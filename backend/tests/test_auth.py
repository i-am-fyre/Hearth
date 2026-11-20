from datetime import datetime, timedelta, timezone

import jwt

from app.api.endpoints import auth as auth_endpoints
from app.core import security
from tests.conftest import register


def test_register_login_and_me(client):
    headers = register(client, "alex@example.com")
    r = client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "alex@example.com"


def test_duplicate_registration_is_rejected(client):
    register(client, "alex@example.com")
    r = client.post("/api/v1/auth/register", json={"email": "alex@example.com", "password": "other"})
    assert r.status_code == 400


def test_wrong_password_is_rejected(client):
    register(client, "alex@example.com", "right password")
    r = client.post("/api/v1/auth/login", data={"username": "alex@example.com", "password": "wrong password"})
    assert r.status_code == 400


def test_protected_routes_need_a_valid_token(client):
    register(client, "alex@example.com")
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_token_signed_with_shipped_placeholder_key_is_rejected(client):
    """Older configs shipped a public SECRET_KEY; tokens forged with it must not work."""
    register(client, "alex@example.com")
    forged = jwt.encode(
        {"sub": "alex@example.com", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "your-super-secret-key-change-it-in-production",
        algorithm="HS256",
    )
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


def test_expired_token_is_rejected(client):
    register(client, "alex@example.com")
    token = security.create_access_token("alex@example.com", expires_delta=timedelta(seconds=-1))
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_passwords_longer_than_bcrypt_limit_work(client):
    password = "a much longer passphrase than bcrypt will look at " * 4  # > 72 bytes
    headers = register(client, "long@example.com", password)
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200


def test_password_reset_flow(client, monkeypatch):
    register(client, "alex@example.com", "old password")

    sent = {}

    async def fake_send(email_to, token):
        sent["email"], sent["token"] = email_to, token

    monkeypatch.setattr(auth_endpoints, "send_password_reset_email", fake_send)

    r = client.post("/api/v1/auth/forgot-password", json={"email": "alex@example.com"})
    assert r.status_code == 200
    assert sent["email"] == "alex@example.com"

    r = client.post("/api/v1/auth/reset-password", json={"token": "not-the-token", "new_password": "x"})
    assert r.status_code == 400

    r = client.post("/api/v1/auth/reset-password", json={"token": sent["token"], "new_password": "new password"})
    assert r.status_code == 200

    # The token is single-use, the old password is gone, the new one works.
    r = client.post("/api/v1/auth/reset-password", json={"token": sent["token"], "new_password": "again"})
    assert r.status_code == 400
    login = lambda pw: client.post("/api/v1/auth/login", data={"username": "alex@example.com", "password": pw})
    assert login("old password").status_code == 400
    assert login("new password").status_code == 200


def test_forgot_password_for_unknown_email_looks_the_same(client, monkeypatch):
    async def fail_send(email_to, token):
        raise AssertionError("no email should be sent for unknown addresses")

    monkeypatch.setattr(auth_endpoints, "send_password_reset_email", fail_send)
    r = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert r.status_code == 200
