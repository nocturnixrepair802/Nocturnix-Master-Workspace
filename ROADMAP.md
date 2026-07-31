# Roadmap

## Initial browser coding assistant

- [x] Mount a plain HTML/CSS/JavaScript assistant in the integrated FastAPI application.
- [x] Add Responses API provider abstraction and persistent assistant task/result orchestration.
- [x] Add owner-scoped retrieval, safe failures, configuration-only health, and focused fakes.
- [ ] Harden browser sign-in/CSRF onboarding and conversation history presentation.
- [ ] Complete deployment, monitoring, managed secrets, and formal security review before any
  production claim.

Repository mutation, terminal execution, autonomous Git, and external web research are deliberately
deferred beyond this read-only initial phase.

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


# Nocturnix AI Assistant v0.1.6 Memory, Planning & Autonomous Task Engine

Version 0.1.6 remains development-only and mock-only. It adds durable owner-scoped memories, conversation-summary storage, planning tasks, reminder readiness records, focus mode, dashboard/search APIs, and a natural-language command router for capture and retrieval. No repair-ticket platform, production AI provider, notification provider, deployment, or live integration is added.

# ROADMAP Update — July 30, 2026

## Milestone Completed

### Development Environment Stabilization

**Status:** ✅ Complete

This milestone establishes a stable, production-quality development environment and completes the backend stabilization phase of the Nocturnix AI Platform.

### Objectives Achieved

* Standardized assistant subsystem interfaces.
* Unified identifier handling throughout the assistant architecture.
* Repaired repository and service inconsistencies.
* Updated registry implementations and type definitions.
* Corrected repository query behavior.
* Updated the automated test suite.
* Eliminated remaining static analysis issues.
* Configured OpenAI API integration.
* Migrated the development workflow to `uv`.
* Established a synchronized Python virtual environment.

### Verification

All validation completed successfully.

| Validation  | Status   |
| ----------- | -------- |
| Unit Tests  | ✅ Passed |
| Ruff Format | ✅ Passed |
| Ruff Lint   | ✅ Passed |
| Mypy        | ✅ Passed |
| Pylance     | ✅ Clean  |

Current automated test results:

```
142 passed
```

---

# Project Phase Transition

The project is now moving from **Platform Stabilization** into **Application Assembly**.

This represents a significant shift in development priorities.

Previous focus:

* Repair
* Refactoring
* Static analysis
* Interface consistency
* Testing
* Reliability

New focus:

* User experience
* AI interaction
* Browser interface
* Deployment
* Product features

---

# Next Major Milestone

## Web Platform Foundation

### Goal

Expose the existing Nocturnix backend through a FastAPI-powered web application while preserving the current architecture.

### Planned Deliverables

* FastAPI application
* REST API
* Browser interface
* Health endpoint
* Chat endpoint
* Assistant integration
* API documentation
* Initial authentication framework

No existing backend services should be duplicated. The web application will reuse the existing assistant, pricing, persistence, and repository layers.

---

# AI Development Assistant (Phase 1)

The first user-facing capability will be an AI-powered development assistant capable of:

* Explaining source code
* Assisting with feature development
* Debugging runtime errors
* Diagnosing test failures
* Generating implementation suggestions
* Tracking conversations
* Supporting future project orchestration

Initially, repository modifications will remain user-controlled.

---

# Future Milestones

## Phase 2

* Project dashboard
* Conversation history
* User authentication
* Project management

## Phase 3

* Repair workflow integration
* Pricing engine interface
* Inventory integration
* Reporting

## Phase 4

* Customer portal
* Business dashboard
* Analytics
* Notifications

## Phase 5

* Private cloud deployment
* Production deployment
* Continuous integration
* Operational monitoring

---

# Current Overall Progress

| Area                    | Status        |
| ----------------------- | ------------- |
| Backend Architecture    | ✅ Complete    |
| Assistant Core          | ✅ Complete    |
| Persistence Layer       | ✅ Complete    |
| Testing Infrastructure  | ✅ Complete    |
| Development Environment | ✅ Complete    |
| OpenAI Integration      | ✅ Configured  |
| Web Platform            | 🚧 Not Started |
| Browser Interface       | 🚧 Not Started |
| Deployment              | 🚧 Not Started |

---

# Current Development Goal

The immediate objective is to evolve Nocturnix from a fully tested backend platform into a browser-accessible AI application by introducing a FastAPI web layer that reuses the existing backend architecture.

All future development should preserve the current green build and maintain complete automated test success.
