from pathlib import Path

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.config import Settings
from nocturnix.persistence_models import (
    OAuthAuthorizationStateRow,
    PasswordResetChallengeRow,
    SessionRow,
    UserRow,
)
from nocturnix.security.auth import PasswordService, SecretStorage


def make_client(tmp_path: Path, **kw):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'auth.db'}",
        database_migration_mode="auto-test-only",
        allow_development_registration=True,
        allow_development_password_reset_delivery=True,
        secret_encryption_key=Fernet.generate_key().decode(),
        **kw,
    )
    return TestClient(create_app(settings))


def test_password_service_hash_verify_policy():
    p = PasswordService()
    h1 = p.hash("fictional long passphrase 1")
    h2 = p.hash("fictional long passphrase 1")
    assert h1 != h2 and p.verify("fictional long passphrase 1", h1) and not p.verify("wrong", h1)
    assert p.needs_rehash(h1) is False
    for bad in ["", "short", "password1234", "x" * 1025]:
        try:
            p.hash(bad)
            raise AssertionError("weak password accepted")
        except ValueError:
            pass


def register_login(c):
    r = c.post(
        "/api/v1/auth/register",
        json={
            "email": "Owner@Example.Test",
            "password": "fictional long passphrase 1",
            "display_name": "Owner",
        },
    )
    assert r.status_code == 200, r.text
    login = c.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.test", "password": "fictional long passphrase 1"},
    )
    assert login.status_code == 200, login.text
    return login.json()["csrf_token"]


def test_session_auth_csrf_logout_and_no_hashes(tmp_path):
    c = make_client(tmp_path)
    csrf = register_login(c)
    assert c.get("/api/v1/auth/me").json()["permissions"]
    assert c.post("/api/v1/auth/logout").status_code == 403
    assert c.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 200
    assert c.get("/api/v1/auth/me").status_code == 401
    text = c.get("/api/v1/audit", headers={"X-Nocturnix-Dev-User": "x"}).text
    assert "fictional long passphrase" not in text and "password_hash" not in text


def test_login_lockout_reset_oauth_and_secret_storage(tmp_path):
    c = make_client(tmp_path)
    csrf = register_login(c)
    for _ in range(5):
        c.post(
            "/api/v1/auth/login", json={"email": "owner@example.test", "password": "wrong password"}
        )
    assert (
        c.post(
            "/api/v1/auth/login",
            json={"email": "owner@example.test", "password": "fictional long passphrase 1"},
        ).status_code
        == 401
    )
    reset = c.post(
        "/api/v1/auth/password/reset/request", json={"email": "owner@example.test"}
    ).json()
    token = reset["development_reset_token"]
    assert token
    assert (
        c.post(
            "/api/v1/auth/password/reset/complete",
            json={"reset_token": token, "new_password": "another fictional passphrase"},
        ).status_code
        == 200
    )
    assert (
        c.post(
            "/api/v1/auth/password/reset/complete",
            json={"reset_token": token, "new_password": "another fictional passphrase"},
        ).status_code
        == 400
    )
    login = c.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.test", "password": "another fictional passphrase"},
    )
    csrf = login.json()["csrf_token"]
    auth = c.post(
        "/api/v1/oauth/mock_google/authorize",
        headers={"X-CSRF-Token": csrf},
        json={"redirect_uri": "http://127.0.0.1:8000/", "scopes": ["gmail.readonly"]},
    ).json()
    assert auth["state"] and auth["pkce_verifier"] and auth["pkce_challenge"]
    assert (
        c.get(
            "/api/v1/oauth/mock_google/callback",
            params={"state": auth["state"], "pkce_verifier": auth["pkce_verifier"]},
        ).status_code
        == 200
    )
    accts = c.get("/api/v1/provider-accounts").json()["items"]
    assert accts and "ciphertext" not in str(accts)
    assert (
        c.post(
            f"/api/v1/provider-accounts/{accts[0]['id']}/revoke", headers={"X-CSRF-Token": csrf}
        ).status_code
        == 200
    )
    container = c.app.state.container
    with container.session_factory() as s:
        assert (
            s.query(UserRow).count() == 1
            and s.query(SessionRow).count() >= 1
            and s.query(PasswordResetChallengeRow).count() == 1
            and s.query(OAuthAuthorizationStateRow).count() == 1
        )
        store = SecretStorage(s, container.settings)
        row = store.store(
            s.query(UserRow).first().id, "oauth_access_token", "fictional-secret-token"
        )
        assert (
            row.encrypted_payload != "fictional-secret-token"
            and store.retrieve(row) == "fictional-secret-token"
        )
        store.revoke(row)
        s.commit()
