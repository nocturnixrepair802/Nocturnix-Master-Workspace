from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from nocturnix.config import Settings
from nocturnix.models import UserIdentity
from nocturnix.persistence.models import (
    EncryptedSecretRecordRow,
    OAuthAuthorizationStateRow,
    PasswordResetChallengeRow,
    PermissionRow,
    ProviderAccountRow,
    RolePermissionRow,
    RoleRow,
    SessionRow,
    UserRoleRow,
    UserRow,
)

GENERIC_AUTH_ERROR = "Invalid credentials or account unavailable."
ALL_PERMISSIONS = {
    "assistant.chat",
    "repair_intake.create",
    "repair_intake.read",
    "approvals.create",
    "approvals.read",
    "approvals.decide",
    "audit.read",
    "preferences.read",
    "preferences.update",
    "email_mock.read",
    "calendar_mock.read",
    "provider_accounts.read",
    "provider_accounts.manage",
    "security_sessions.read",
    "security_sessions.revoke",
    "users.read",
    "users.manage",
    "business_tasks.manage",
    "reminders.manage",
    "repair_context.read",
    "repair_context.manage",
    "codex_tasks.manage",
    "memories.read",
    "memories.manage",
    "planning.read",
    "planning.manage",
    "dashboard.read",
    "search.read",
}
ROLE_PERMISSIONS = {
    "owner": sorted(ALL_PERMISSIONS),
    "administrator": sorted(ALL_PERMISSIONS - {"users.manage"}),
    "operator": sorted(
        {
            "assistant.chat",
            "repair_intake.create",
            "repair_intake.read",
            "approvals.create",
            "approvals.read",
            "approvals.decide",
            "preferences.read",
            "email_mock.read",
            "calendar_mock.read",
            "provider_accounts.read",
        }
    ),
    "viewer": sorted(
        {
            "assistant.chat",
            "approvals.read",
            "audit.read",
            "preferences.read",
            "email_mock.read",
            "calendar_mock.read",
            "provider_accounts.read",
        }
    ),
}


def now_utc() -> datetime:
    return datetime.now(UTC)


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def token_urlsafe(n: int = 32) -> str:
    return secrets.token_urlsafe(n)


def normalize_login(login: str) -> str:
    return login.strip().casefold()


class PasswordService:
    def __init__(self) -> None:
        self.hasher = PasswordHash.recommended()

    def validate(self, password: str) -> None:
        if not password:
            raise ValueError("password is required")
        if len(password) < 12:
            raise ValueError("password must be at least 12 characters")
        if len(password) > 1024:
            raise ValueError("password is too long")
        if password.casefold() in {
            "password1234",
            "password12345",
            "testpassword",
            "letmeinletmein",
            "nocturnix123",
        }:
            raise ValueError("password is too common")

    def hash(self, password: str) -> str:
        self.validate(password)
        return self.hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        return bool(password_hash) and self.hasher.verify(password, password_hash)

    def needs_rehash(self, password_hash: str) -> bool:
        return False


class AuditWriter:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        owner: str,
        category: str,
        action: str,
        result: str = "success",
        metadata: dict[str, object] | None = None,
    ) -> None:
        from nocturnix.persistence.models import AuditEventRow

        banned = {
            "password",
            "password_hash",
            "token",
            "session_token",
            "reset_token",
            "state",
            "code",
            "verifier",
            "secret",
            "key",
            "ciphertext",
        }
        safe = {
            k: ("[REDACTED]" if any(b in k.lower() for b in banned) else v)
            for k, v in (metadata or {}).items()
        }
        self.session.add(
            AuditEventRow(
                id=f"audit_{uuid4().hex[:12]}",
                created_at=now_utc(),
                owner_user_id=owner,
                category=category,
                event_type=action,
                action=action,
                result=result,
                metadata_json=safe,
                source_component="security",
            )
        )


class AuthorizationService:
    def __init__(self, session: Session):
        self.session = session

    def seed(self) -> None:
        for p in ALL_PERMISSIONS:
            self.session.merge(PermissionRow(name=p, description=p))
        for r, perms in ROLE_PERMISSIONS.items():
            self.session.merge(RoleRow(name=r, description=f"Development {r} role"))
            for p in perms:
                self.session.merge(RolePermissionRow(role_name=r, permission_name=p))
        self.session.flush()

    def assign_role(self, user_id: str, role: str) -> None:
        self.seed()
        self.session.merge(UserRoleRow(user_id=user_id, role_name=role))
        AuditWriter(self.session).record(
            user_id, "security", "role_assigned", metadata={"role": role}
        )

    def permissions_for_user(self, user_id: str) -> set[str]:
        rows = self.session.execute(
            select(RolePermissionRow.permission_name)
            .join(UserRoleRow, UserRoleRow.role_name == RolePermissionRow.role_name)
            .where(UserRoleRow.user_id == user_id)
        ).all()
        return {r[0] for r in rows}

    def require(self, user: UserIdentity, permission: str) -> None:
        if user.auth_mode == "development_header":
            return
        if permission not in self.permissions_for_user(user.user_id):
            AuditWriter(self.session).record(
                user.user_id, "security", "permission_denied", "denied", {"permission": permission}
            )
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="permission denied")


class AuthService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.passwords = PasswordService()
        self.audit = AuditWriter(session)

    def create_user(
        self, login: str, password: str, display_name: str, role: str = "owner"
    ) -> UserRow:
        pw_hash = self.passwords.hash(password)
        norm = normalize_login(login)
        now = now_utc()
        user = UserRow(
            id=f"usr_{uuid4().hex[:12]}",
            login_identifier=login.strip(),
            normalized_login_identifier=norm,
            display_name=display_name.strip() or norm,
            password_hash=pw_hash,
            account_status="active",
            email_verified=False,
            created_at=now,
            updated_at=now,
            password_changed_at=now,
            security_version=1,
            failed_login_count=0,
        )
        self.session.add(user)
        self.session.flush()
        AuthorizationService(self.session).assign_role(user.id, role)
        self.audit.record(user.id, "security", "account_created")
        return user

    def login(self, login: str, password: str, ua: str | None = None) -> tuple[UserRow, str, str]:
        norm = normalize_login(login)
        user = self.session.scalar(
            select(UserRow).where(UserRow.normalized_login_identifier == norm)
        )
        now = now_utc()
        locked_until = (
            user.locked_until.replace(tzinfo=UTC)
            if user and user.locked_until and user.locked_until.tzinfo is None
            else (user.locked_until if user else None)
        )
        locked_active = bool(locked_until and locked_until > now)
        if user and user.account_status == "locked" and not locked_active:
            user.account_status = "active"
            user.locked_until = None
        if (
            not user
            or user.account_status not in {"active", "pending"}
            or locked_active
            or not self.passwords.verify(password, user.password_hash)
        ):
            if user:
                user.failed_login_count += 1
                user.last_failed_login_at = now
                if user.failed_login_count >= self.settings.login_max_attempts:
                    user.locked_until = now + timedelta(minutes=self.settings.login_lockout_minutes)
                    user.account_status = "locked"
                    self.audit.record(user.id, "security", "account_locked", "denied")
                self.audit.record(user.id, "security", "login_failed", "denied")
                self.session.commit()
            raise ValueError(GENERIC_AUTH_ERROR)
        user.failed_login_count = 0
        user.locked_until = None
        user.account_status = "active"
        user.last_successful_login_at = now
        user.updated_at = now
        raw = token_urlsafe(48)
        csrf = token_urlsafe(32)
        sid = f"sess_{uuid4().hex[:12]}"
        self.session.add(
            SessionRow(
                id=sid,
                user_id=user.id,
                session_token_hash=stable_hash(raw),
                csrf_token_hash=stable_hash(csrf),
                created_at=now,
                last_seen_at=now,
                expires_at=now + timedelta(minutes=self.settings.session_idle_minutes),
                absolute_expires_at=now + timedelta(hours=self.settings.session_absolute_hours),
                user_agent=ua[:200] if ua else None,
                security_version=user.security_version,
            )
        )
        self.audit.record(user.id, "security", "login_success")
        self.audit.record(user.id, "security", "session_created", metadata={"session_id": sid})
        return user, raw, csrf

    def user_for_token(self, raw: str) -> tuple[UserRow, SessionRow] | None:
        s = self.session.scalar(
            select(SessionRow).where(SessionRow.session_token_hash == stable_hash(raw))
        )
        now = now_utc()
        expires_at = (
            s.expires_at.replace(tzinfo=UTC)
            if s and s.expires_at.tzinfo is None
            else (s.expires_at if s else now)
        )
        absolute_expires_at = (
            s.absolute_expires_at.replace(tzinfo=UTC)
            if s and s.absolute_expires_at.tzinfo is None
            else (s.absolute_expires_at if s else now)
        )
        if not s or s.revoked_at or expires_at <= now or absolute_expires_at <= now:
            return None
        u = self.session.get(UserRow, s.user_id)
        if (
            not u
            or u.account_status not in {"active", "pending"}
            or u.security_version != s.security_version
        ):
            return None
        s.last_seen_at = now
        s.expires_at = now + timedelta(minutes=self.settings.session_idle_minutes)
        return u, s

    def revoke(self, session_id: str, user_id: str, reason: str = "logout") -> bool:
        s = self.session.get(SessionRow, session_id)
        if not s or s.user_id != user_id:
            return False
        s.revoked_at = now_utc()
        s.revocation_reason = reason
        self.audit.record(
            user_id,
            "security",
            "session_revoked",
            metadata={"session_id": session_id, "reason": reason},
        )
        return True

    def revoke_all(self, user_id: str, reason: str = "revoked_all") -> int:
        n = 0
        for s in self.session.scalars(
            select(SessionRow).where(SessionRow.user_id == user_id, SessionRow.revoked_at.is_(None))
        ):
            s.revoked_at = now_utc()
            s.revocation_reason = reason
            n += 1
        self.audit.record(
            user_id, "security", "sessions_revoked", metadata={"count": n, "reason": reason}
        )
        return n

    def change_password(self, user: UserRow, current: str, new: str) -> None:
        if not self.passwords.verify(current, user.password_hash):
            raise ValueError(GENERIC_AUTH_ERROR)
        user.password_hash = self.passwords.hash(new)
        user.password_changed_at = now_utc()
        user.security_version += 1
        self.revoke_all(user.id, "password_change")
        self.audit.record(user.id, "security", "password_changed")


class PasswordResetService:
    def __init__(self, session: Session, settings: Settings):
        self.session = session
        self.settings = settings
        self.audit = AuditWriter(session)

    def request(self, login: str) -> dict[str, object]:
        user = self.session.scalar(
            select(UserRow).where(UserRow.normalized_login_identifier == normalize_login(login))
        )
        token = None
        if user:
            for row in self.session.scalars(
                select(PasswordResetChallengeRow).where(
                    PasswordResetChallengeRow.user_id == user.id,
                    PasswordResetChallengeRow.consumed_at.is_(None),
                )
            ):
                row.invalidated_at = now_utc()
            token = token_urlsafe(40)
            now = now_utc()
            self.session.add(
                PasswordResetChallengeRow(
                    id=f"reset_{uuid4().hex[:12]}",
                    user_id=user.id,
                    reset_token_hash=stable_hash(token),
                    created_at=now,
                    expires_at=now + timedelta(minutes=self.settings.password_reset_minutes),
                    attempt_count=0,
                )
            )
            self.audit.record(user.id, "security", "password_reset_requested")
        return {
            "message": "If the account is available, a development reset challenge was prepared.",
            "mock_delivery_available": self.settings.allow_development_password_reset_delivery,
            "development_reset_token": token
            if self.settings.allow_development_password_reset_delivery
            else None,
        }

    def complete(self, token: str, new_password: str) -> None:
        row = self.session.scalar(
            select(PasswordResetChallengeRow).where(
                PasswordResetChallengeRow.reset_token_hash == stable_hash(token)
            )
        )
        expires_at = (
            row.expires_at.replace(tzinfo=UTC)
            if row and row.expires_at.tzinfo is None
            else (row.expires_at if row else now_utc())
        )
        if not row or row.consumed_at or row.invalidated_at or expires_at <= now_utc():
            raise ValueError("invalid or expired reset challenge")
        user = self.session.get(UserRow, row.user_id)
        assert user is not None
        user.password_hash = PasswordService().hash(new_password)
        user.account_status = "active"
        user.failed_login_count = 0
        user.locked_until = None
        user.password_changed_at = now_utc()
        user.security_version += 1
        row.consumed_at = now_utc()
        AuthService(self.session, self.settings).revoke_all(user.id, "password_reset")
        self.audit.record(user.id, "security", "password_reset_completed")


class SecretStorage:
    def __init__(self, session: Session, settings: Settings):
        if settings.secret_storage_enabled and not settings.secret_encryption_key:
            raise ValueError("secret encryption key required")
        self.session = session
        self.settings = settings
        self.fernet = (
            Fernet(settings.secret_encryption_key.encode())
            if settings.secret_encryption_key
            else None
        )

    def store(
        self,
        owner_id: str,
        secret_type: str,
        plaintext: str,
        provider_account_id: str | None = None,
    ) -> EncryptedSecretRecordRow:
        if not self.fernet:
            raise ValueError("secret storage disabled")
        now = now_utc()
        cipher = self.fernet.encrypt(plaintext.encode()).decode()
        row = EncryptedSecretRecordRow(
            id=f"sec_{uuid4().hex[:12]}",
            owner_user_id=owner_id,
            provider_account_id=provider_account_id,
            secret_type=secret_type,
            encrypted_payload=cipher,
            encryption_algorithm="fernet",
            key_version=self.settings.secret_key_version,
            created_at=now,
            updated_at=now,
        )
        self.session.add(row)
        self.session.flush()
        AuditWriter(self.session).record(
            owner_id,
            "security",
            "secret_created",
            metadata={"secret_id": row.id, "secret_type": secret_type},
        )
        return row

    def retrieve(self, row: EncryptedSecretRecordRow) -> str:
        if not self.fernet or row.revoked_at:
            raise ValueError("secret unavailable")
        try:
            return self.fernet.decrypt(row.encrypted_payload.encode()).decode()
        except InvalidToken as exc:
            raise ValueError("secret decrypt failed") from exc

    def revoke(self, row: EncryptedSecretRecordRow) -> None:
        row.revoked_at = now_utc()
        AuditWriter(self.session).record(
            row.owner_user_id, "security", "secret_revoked", metadata={"secret_id": row.id}
        )


class OAuthService:
    def __init__(self, session: Session, settings: Settings):
        self.session = session
        self.settings = settings
        self.audit = AuditWriter(session)

    def start(
        self, user_id: str, provider: str, redirect_uri: str, scopes: list[str]
    ) -> dict[str, object]:
        if not self.settings.mock_oauth_enabled or provider != "mock_google":
            raise ValueError("provider unavailable")
        if redirect_uri not in self.settings.allowed_redirect_uris:
            raise ValueError("redirect URI not allowed")
        raw_state = token_urlsafe(32)
        verifier = token_urlsafe(48)
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        now = now_utc()
        self.session.add(
            OAuthAuthorizationStateRow(
                id=f"oauth_{uuid4().hex[:12]}",
                owner_user_id=user_id,
                provider=provider,
                state_token_hash=stable_hash(raw_state),
                pkce_verifier_protected=stable_hash(verifier),
                pkce_challenge=challenge,
                redirect_uri=redirect_uri,
                requested_scopes=scopes,
                created_at=now,
                expires_at=now + timedelta(minutes=self.settings.oauth_state_minutes),
                correlation_id=f"corr_{uuid4().hex[:12]}",
            )
        )
        self.audit.record(
            user_id,
            "security",
            "oauth_authorize_started",
            metadata={"provider": provider, "scopes": scopes},
        )
        return {
            "mock": True,
            "provider": provider,
            "state": raw_state,
            "pkce_verifier": verifier,
            "pkce_challenge": challenge,
            "authorization_url": "mock://oauth/authorize",
        }

    def callback(
        self, user_id: str, provider: str, state: str, verifier: str, error: str | None = None
    ) -> ProviderAccountRow:
        row = self.session.scalar(
            select(OAuthAuthorizationStateRow).where(
                OAuthAuthorizationStateRow.state_token_hash == stable_hash(state),
                OAuthAuthorizationStateRow.provider == provider,
            )
        )
        if (
            error
            or not row
            or row.owner_user_id != user_id
            or row.consumed_at
            or (
                row.expires_at.replace(tzinfo=UTC)
                if row.expires_at.tzinfo is None
                else row.expires_at
            )
            <= now_utc()
            or not hmac.compare_digest(row.pkce_verifier_protected, stable_hash(verifier))
        ):
            if row:
                row.failure_at = now_utc()
                row.failure_reason = "callback validation failed"
                self.audit.record(
                    user_id, "security", "oauth_callback_failed", "denied", {"provider": provider}
                )
            raise ValueError("OAuth callback validation failed")
        row.consumed_at = now_utc()
        acct = ProviderAccountRow(
            id=f"pa_{uuid4().hex[:12]}",
            owner_user_id=user_id,
            provider_name=provider,
            provider_subject_identifier=f"mock-subject-{user_id}",
            display_label="Mock Google Account",
            normalized_provider_email="mock-user@example.test",
            requested_scopes=row.requested_scopes,
            granted_scopes=row.requested_scopes,
            consent_at=now_utc(),
            linked_at=now_utc(),
            status="active",
            safe_provider_metadata={"mock": True},
        )
        self.session.add(acct)
        self.session.flush()
        self.audit.record(
            user_id,
            "security",
            "provider_account_linked",
            metadata={"provider": provider, "provider_account_id": acct.id},
        )
        return acct

    def revoke(self, user_id: str, account_id: str) -> bool:
        acct = self.session.get(ProviderAccountRow, account_id)
        if not acct or acct.owner_user_id != user_id:
            return False
        acct.status = "revoked"
        acct.revoked_at = now_utc()
        self.audit.record(
            user_id,
            "security",
            "provider_account_revoked",
            metadata={"provider_account_id": account_id},
        )
        return True
