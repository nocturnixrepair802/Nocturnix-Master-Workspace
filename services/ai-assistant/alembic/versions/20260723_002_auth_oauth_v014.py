"""authentication and OAuth security foundation for v0.1.4

Revision ID: 20260723_002
Revises: 20260723_001
Create Date: 2026-07-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260723_002"
down_revision: str | None = "20260723_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("login_identifier", sa.String(254), nullable=False),
        sa.Column("normalized_login_identifier", sa.String(254), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("account_status", sa.String(30), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_successful_login_at", sa.DateTime(timezone=True)),
        sa.Column("last_failed_login_at", sa.DateTime(timezone=True)),
        sa.Column("failed_login_count", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("password_changed_at", sa.DateTime(timezone=True)),
        sa.Column("disabled_at", sa.DateTime(timezone=True)),
        sa.Column("deletion_requested_at", sa.DateTime(timezone=True)),
        sa.Column("security_version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("normalized_login_identifier"),
    )
    op.create_index(
        "ix_users_normalized_login_identifier", "users", ["normalized_login_identifier"]
    )
    op.create_index("ix_users_account_status", "users", ["account_status"])
    op.create_table(
        "roles",
        sa.Column("name", sa.String(80), primary_key=True),
        sa.Column("description", sa.String(200), nullable=False),
    )
    op.create_table(
        "permissions",
        sa.Column("name", sa.String(120), primary_key=True),
        sa.Column("description", sa.String(240), nullable=False),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("role_name", sa.String(80), sa.ForeignKey("roles.name"), primary_key=True),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_name", sa.String(80), sa.ForeignKey("roles.name"), primary_key=True),
        sa.Column(
            "permission_name", sa.String(120), sa.ForeignKey("permissions.name"), primary_key=True
        ),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_token_hash", sa.String(64), nullable=False),
        sa.Column("csrf_token_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("revocation_reason", sa.String(120)),
        sa.Column("user_agent", sa.String(200)),
        sa.Column("security_version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("session_token_hash"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_session_token_hash", "sessions", ["session_token_hash"])
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"])
    op.create_table(
        "password_reset_challenges",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reset_token_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("invalidated_at", sa.DateTime(timezone=True)),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.UniqueConstraint("reset_token_hash"),
    )
    op.create_index(
        "ix_password_reset_challenges_user_id", "password_reset_challenges", ["user_id"]
    )
    op.create_index(
        "ix_password_reset_challenges_reset_token_hash",
        "password_reset_challenges",
        ["reset_token_hash"],
    )
    op.create_index(
        "ix_password_reset_challenges_expires_at", "password_reset_challenges", ["expires_at"]
    )
    op.create_table(
        "provider_accounts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider_name", sa.String(80), nullable=False),
        sa.Column("provider_subject_identifier", sa.String(200), nullable=False),
        sa.Column("display_label", sa.String(160), nullable=False),
        sa.Column("normalized_provider_email", sa.String(254)),
        sa.Column("requested_scopes", sa.JSON(), nullable=False),
        sa.Column("granted_scopes", sa.JSON(), nullable=False),
        sa.Column("consent_at", sa.DateTime(timezone=True)),
        sa.Column("linked_at", sa.DateTime(timezone=True)),
        sa.Column("last_refresh_at", sa.DateTime(timezone=True)),
        sa.Column("token_expires_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("disabled_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("safe_provider_metadata", sa.JSON(), nullable=False),
        sa.UniqueConstraint("provider_name", "provider_subject_identifier"),
    )
    op.create_index("ix_provider_accounts_owner_user_id", "provider_accounts", ["owner_user_id"])
    op.create_index("ix_provider_accounts_provider_name", "provider_accounts", ["provider_name"])
    op.create_index("ix_provider_accounts_status", "provider_accounts", ["status"])
    op.create_table(
        "encrypted_secret_records",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider_account_id", sa.String(64), sa.ForeignKey("provider_accounts.id")),
        sa.Column("secret_type", sa.String(80), nullable=False),
        sa.Column("encrypted_payload", sa.Text(), nullable=False),
        sa.Column("encryption_algorithm", sa.String(80), nullable=False),
        sa.Column("key_version", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rotated_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_encrypted_secret_records_owner_user_id", "encrypted_secret_records", ["owner_user_id"]
    )
    op.create_index(
        "ix_encrypted_secret_records_provider_account_id",
        "encrypted_secret_records",
        ["provider_account_id"],
    )
    op.create_table(
        "oauth_authorization_states",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("state_token_hash", sa.String(64), nullable=False),
        sa.Column("pkce_verifier_protected", sa.String(128), nullable=False),
        sa.Column("pkce_challenge", sa.String(128), nullable=False),
        sa.Column("redirect_uri", sa.String(500), nullable=False),
        sa.Column("requested_scopes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("failure_at", sa.DateTime(timezone=True)),
        sa.Column("failure_reason", sa.String(200)),
        sa.Column("correlation_id", sa.String(120), nullable=False),
        sa.UniqueConstraint("state_token_hash"),
    )
    op.create_index(
        "ix_oauth_authorization_states_owner_user_id",
        "oauth_authorization_states",
        ["owner_user_id"],
    )
    op.create_index(
        "ix_oauth_authorization_states_state_token_hash",
        "oauth_authorization_states",
        ["state_token_hash"],
    )
    op.create_index(
        "ix_oauth_authorization_states_expires_at", "oauth_authorization_states", ["expires_at"]
    )


def downgrade() -> None:
    raise NotImplementedError(
        "Destructive schema downgrade is intentionally not implemented for v0.1.4."
    )
