# Data Dictionary

- `UserIdentity`: development-only mock user resolved from `X-Nocturnix-Dev-User`.
- `ApprovalRecord`: owner-scoped action proposal with risk, status, expiration, content hash, action-integrity hash, timestamps, execution result, failure reason, and version.
- `AuditEvent`: owner-scoped redacted append-oriented event record persisted in SQL.
- `ConversationRecord`: owner-scoped chat conversation with mode, status, escalation, and retention expiration.
- `ChatMessageRecord`: ordered visible user/assistant message; hidden system instructions are not stored.
- `RepairIntakeRecord`: validated repair request with workflow status, safety escalation, timestamps, and retention expiration.
- `UserPreferences`: safe convenience preferences that cannot disable authentication, approvals, auditing, privacy, or security controls.
- `KnowledgeSource`: local placeholder Markdown source with stable source ID and excerpt.
- `MockEmailMessage` and `MockCalendarEvent`: fictional mock metadata only; no Gmail or Google Calendar connection.

# Nocturnix AI Assistant v0.1.3 Durable Persistence

Version 0.1.3 keeps Nocturnix development-only and mock-only while replacing normal application in-memory persistence with SQL-backed repositories. SQLite is the only enabled local provider for this milestone; Gmail, Google Calendar, WordPress, Square, production AI providers, notifications, real customer systems, and paid/live calls remain disabled.

## Architecture

The canonical package remains `src/nocturnix/` and the only UI remains `src/nocturnix/static/`. FastAPI routes depend on request-scoped services. Services depend on repository protocols, not raw SQL. SQLAlchemy persistence models live separately from Pydantic request/response/domain models, and Alembic owns schema creation.

## Database settings

Safe local defaults:

```text
DATABASE_URL=sqlite:///./data/nocturnix_assistant.db
DATABASE_ECHO=false
DATABASE_MIGRATION_MODE=manual
DATA_RETENTION_DAYS=30
AUDIT_RETENTION_DAYS=365
CONVERSATION_RETENTION_DAYS=30
REPAIR_INTAKE_RETENTION_DAYS=90
```

The app reports only provider/readiness/revision metadata from `/api/v1/status`; it does not return full database URLs, credentials, absolute database paths, secrets, or environment dumps. Local database files under `data/` plus `*.db`, `*.sqlite`, and `*.sqlite3` are ignored by Git.

## Migrations

Migrations are explicit and non-destructive by policy. Run from the repository root:

```bash
alembic -x database_url=sqlite:///./data/nocturnix_assistant.db upgrade head
alembic current
```

PowerShell example:

```powershell
$env:NOCTURNIX_DATABASE_URL = "sqlite:///./data/nocturnix_assistant.db"
alembic upgrade head
alembic current
```

Downgrade is intentionally not implemented for v0.1.3 because dropping the initial durable schema would be destructive. Back up the SQLite database file before migration experiments. PostgreSQL support is deferred, but repository boundaries and SQLAlchemy models avoid route rewrites later.

## Persisted records

The initial schema stores approvals and execution state, append-oriented audit events, conversations, ordered chat messages, repair intakes, safe user preferences, and mock email/calendar metadata. Chat persistence stores visible user/assistant content and safe source/tool summaries only; hidden system instructions are never persisted.

## Transaction strategy

Each API request opens a short SQLAlchemy session scope that commits on success, rolls back on failure, and closes the session. Approval execution uses a conditional SQL update that can claim only pending, unexpired, not-yet-started approvals owned by the caller. This prevents duplicate execution without relying on an in-memory lock.

## Approval and audit protections

Owner isolation, expiration checks, rejection checks, duplicate-execution prevention, content hashing, action-integrity hashing, mock-only execution, and audit records are preserved. Audit metadata is redacted before repository writes for keys such as tokens, passwords, secrets, cards, SSNs, IMEIs, serial numbers, and auth codes.

## Retention foundation

Retention cleanup is explicit and dry-run by default at `POST /api/v1/retention/cleanup`. It reports candidate counts, records cleanup activity in the audit log, preserves pending approvals and audit integrity, and performs no physical deletion while policy decisions are unresolved.

## Testing

Tests use isolated temporary SQLite databases with explicit test-only migration mode. Run:

```bash
ruff format --check .
ruff check .
mypy src tests
pytest
bandit -c pyproject.toml -r src
pip-audit
```

## Future OAuth/token milestone

Real OAuth/token storage must be a separate security milestone with encrypted token storage, rotation, least-privilege scopes, revocation, audit trails, operational key management, and production authentication before any live provider connection is considered.

# Nocturnix AI Assistant v0.1.4 Authentication and OAuth Security Foundation

Version 0.1.4 remains development-only and mock-only. It adds durable user accounts, Argon2 password hashing through `pwdlib`, server-side opaque sessions, CSRF checks for cookie-authenticated state changes, role-based permissions, password reset records with development-only mock delivery, encrypted secret-storage abstractions using authenticated encryption, provider-account metadata, and mock-only OAuth state/PKCE preparation. No Gmail, Google Calendar, WordPress, Square, production AI provider, email, SMS, or live OAuth network call is made.

## Implemented

- Durable `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `sessions`, `password_reset_challenges`, `provider_accounts`, `encrypted_secret_records`, and `oauth_authorization_states` tables.
- `session`, `development_header`, and `disabled` authentication modes. `development_header` requires explicit development opt-in and is rejected in production-like settings.
- RBAC roles: owner, administrator, operator, and viewer. Permissions are explicit and checked centrally.
- Mock OAuth provider identifier: `mock_google`; redirect URIs are allowlisted and PKCE/state records are single-use and short-lived.
- Local encrypted secret records are for development only and require `NOCTURNIX_SECRET_ENCRYPTION_KEY` when enabled; this is not production key management.

## Permission matrix

| Permission | Owner | Administrator | Operator | Viewer |
| --- | --- | --- | --- | --- |
| assistant.chat | yes | yes | yes | yes |
| repair_intake.create/read | yes | yes | yes | no |
| approvals.create/read/decide | yes | yes | yes | read only |
| audit.read | yes | yes | no | yes |
| preferences.read/update | yes | yes | read only | read only |
| email_mock.read/calendar_mock.read | yes | yes | yes | yes |
| provider_accounts.read/manage | yes | yes | read only | read only |
| security_sessions.read/revoke | yes | yes | no | no |
| users.read/manage | yes | read only | no | no |

## Development limitations and owner decisions

Local HTTP cannot provide the same transport protection as production TLS. Registration and reset-token mock delivery are disabled unless explicitly enabled. Distributed rate limiting, production cookie settings, real OAuth client registration, external secret management, verified redirect domains, consent copy, Gmail read-only scope approval, incident response processes, and administrator bootstrap policy remain owner decisions before v0.2.0.

## Threat model summary

Threats considered include credential theft, password database compromise, session theft/fixation, CSRF, brute force, account enumeration, privilege escalation, cross-user access, OAuth state theft, authorization-code interception, PKCE bypass, redirect abuse, scope escalation, token theft, key compromise, secret logging, audit leakage, malicious documents, prompt-injection approval bypass attempts, compromised developer machines, and SQLite disclosure. Mitigations include adaptive hashing, opaque hashed sessions, CSRF tokens, generic auth failures, account lockout, deny-by-default RBAC, owner-scoped queries, hashed OAuth state, PKCE, redirect allowlisting, disabled live providers, encrypted secret abstraction, audit redaction, and preserved approval controls. Remaining limitations require production TLS, distributed throttling, managed KMS/HSM, hardened deployment, monitoring, backups, and formal security review.
