# Roadmap

## Implemented in v0.1.2

- Clean FastAPI foundation, mock providers, in-memory approvals and audit events, repair intake, local knowledge search, local UI, and PWA foundation.

## Implemented in v0.1.3

- SQL-backed repositories, Alembic initial schema, durable approval/audit/conversation/message/repair/preference/mock metadata storage, retention dry-run foundation, and transaction-safe duplicate execution prevention.

## Recommended next milestone

- Production authentication and OAuth/token-storage design before any live provider integrations.

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
