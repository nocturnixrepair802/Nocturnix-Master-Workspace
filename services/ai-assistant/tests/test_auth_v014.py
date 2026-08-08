from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.config import Settings
from nocturnix.persistence.models import (
    OAuthAuthorizationStateRow,
    PasswordResetChallengeRow,
    SessionRow,
    UserRow,
)
from nocturnix.security.auth import PasswordService, SecretStorage


def make_client(
    tmp_path: Path,
    **overrides: Any,
) -> TestClient:
    """
    Create an isolated session-authentication application.

    Every provider and authentication setting that could otherwise be loaded
    from the developer's root .env is explicitly overridden here.
    """
    values: dict[str, Any] = {
        "database_url": f"sqlite:///{tmp_path / 'auth.db'}",
        "database_migration_mode": "auto-test-only",
        "auth_mode": "session",
        "allow_development_header_auth": False,
        "allow_development_registration": True,
        "allow_development_password_reset_delivery": True,
        "secret_encryption_key": Fernet.generate_key().decode(),
        "coding_provider": "mock",
        "openai_enabled": False,
        "external_providers_enabled": False,
        "openai_api_key": "",
        "rate_limit_per_minute": 500,
    }
    values.update(overrides)

    settings = Settings(**values)

    return TestClient(create_app(settings))


def test_password_service_hash_verify_policy() -> None:
    password_service = PasswordService()

    first_hash = password_service.hash("fictional long passphrase 1")
    second_hash = password_service.hash("fictional long passphrase 1")

    assert first_hash != second_hash
    assert password_service.verify(
        "fictional long passphrase 1",
        first_hash,
    )
    assert not password_service.verify(
        "wrong",
        first_hash,
    )
    assert password_service.needs_rehash(first_hash) is False

    invalid_passwords = [
        "",
        "short",
        "password1234",
        "x" * 1025,
    ]

    for password in invalid_passwords:
        try:
            password_service.hash(password)
        except ValueError:
            continue

        raise AssertionError("weak password accepted")


def register_login(
    client: TestClient,
) -> str:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "Owner@Example.Test",
            "password": "fictional long passphrase 1",
            "display_name": "Owner",
        },
    )

    assert register_response.status_code == 200, register_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "owner@example.test",
            "password": "fictional long passphrase 1",
        },
    )

    assert login_response.status_code == 200, login_response.text

    csrf_token = login_response.json()["csrf_token"]

    assert isinstance(csrf_token, str)
    assert csrf_token

    return csrf_token


def test_session_auth_csrf_logout_and_no_hashes(
    tmp_path: Path,
) -> None:
    with make_client(tmp_path) as client:
        csrf_token = register_login(client)

        current_user_response = client.get("/api/v1/auth/me")

        assert current_user_response.status_code == 200
        assert current_user_response.json()["permissions"]

        logout_without_csrf = client.post("/api/v1/auth/logout")

        assert logout_without_csrf.status_code == 403

        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={
                "X-CSRF-Token": csrf_token,
            },
        )

        assert logout_response.status_code == 200
        assert client.get("/api/v1/auth/me").status_code == 401

        audit_text = client.get(
            "/api/v1/audit",
            headers={
                "X-Nocturnix-Dev-User": "x",
            },
        ).text

        assert "fictional long passphrase" not in audit_text
        assert "password_hash" not in audit_text


def test_login_lockout_reset_oauth_and_secret_storage(
    tmp_path: Path,
) -> None:
    with make_client(tmp_path) as client:
        csrf_token = register_login(client)

        for _ in range(5):
            client.post(
                "/api/v1/auth/login",
                json={
                    "email": "owner@example.test",
                    "password": "wrong password",
                },
            )

        locked_login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "owner@example.test",
                "password": "fictional long passphrase 1",
            },
        )

        assert locked_login_response.status_code == 401

        reset_request_response = client.post(
            "/api/v1/auth/password/reset/request",
            json={
                "email": "owner@example.test",
            },
        )

        assert reset_request_response.status_code == 200

        reset_token = reset_request_response.json()["development_reset_token"]

        assert isinstance(reset_token, str)
        assert reset_token

        reset_complete_response = client.post(
            "/api/v1/auth/password/reset/complete",
            json={
                "reset_token": reset_token,
                "new_password": ("another fictional passphrase"),
            },
        )

        assert reset_complete_response.status_code == 200

        reused_reset_response = client.post(
            "/api/v1/auth/password/reset/complete",
            json={
                "reset_token": reset_token,
                "new_password": ("another fictional passphrase"),
            },
        )

        assert reused_reset_response.status_code == 400

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "owner@example.test",
                "password": ("another fictional passphrase"),
            },
        )

        assert login_response.status_code == 200

        csrf_token = login_response.json()["csrf_token"]

        oauth_authorize_response = client.post(
            "/api/v1/oauth/mock_google/authorize",
            headers={
                "X-CSRF-Token": csrf_token,
            },
            json={
                "redirect_uri": ("http://127.0.0.1:8000/"),
                "scopes": [
                    "gmail.readonly",
                ],
            },
        )

        assert oauth_authorize_response.status_code == 200

        oauth_authorization = oauth_authorize_response.json()

        assert oauth_authorization["state"]
        assert oauth_authorization["pkce_verifier"]
        assert oauth_authorization["pkce_challenge"]

        callback_response = client.get(
            "/api/v1/oauth/mock_google/callback",
            params={
                "state": oauth_authorization["state"],
                "pkce_verifier": (oauth_authorization["pkce_verifier"]),
            },
        )

        assert callback_response.status_code == 200

        provider_accounts_response = client.get("/api/v1/provider-accounts")

        assert provider_accounts_response.status_code == 200

        provider_accounts = provider_accounts_response.json()["items"]

        assert provider_accounts
        assert "ciphertext" not in str(provider_accounts)

        revoke_response = client.post(
            (f"/api/v1/provider-accounts/{provider_accounts[0]['id']}/revoke"),
            headers={
                "X-CSRF-Token": csrf_token,
            },
        )

        assert revoke_response.status_code == 200

        app = cast(FastAPI, client.app)
        container = app.state.container

        with container.session_factory() as session:
            assert session.query(UserRow).count() == 1
            assert session.query(SessionRow).count() >= 1
            assert session.query(PasswordResetChallengeRow).count() == 1
            assert session.query(OAuthAuthorizationStateRow).count() == 1

            secret_storage = SecretStorage(
                session,
                container.settings,
            )

            user = session.query(UserRow).first()

            assert user is not None

            stored_secret = secret_storage.store(
                user.id,
                "oauth_access_token",
                "fictional-secret-token",
            )

            assert stored_secret.encrypted_payload != "fictional-secret-token"
            assert secret_storage.retrieve(stored_secret) == "fictional-secret-token"

            secret_storage.revoke(stored_secret)
            session.commit()
