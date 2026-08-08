# Changelog

## Unreleased

### Added

- Integrated `/assistant` browser interface and owner-scoped assistant task/result APIs.
- OpenAI Responses API coding provider with safe error translation and persisted task lifecycle.
- Focused provider and web API tests that replace the provider with deterministic fakes.

### Security

- The coding assistant remains read-only and cannot edit files or execute commands.
- Live OpenAI access requires explicit development configuration and existing authentication/CSRF.
# Changelog

## [0.3.0] - 2026-07-30

### Added

- OpenAI API configuration support
- uv development environment
- Modern dependency synchronization
- Stable development environment

### Changed

- Standardized assistant identifiers
- Updated assistant repository interfaces
- Updated assistant service interfaces
- Updated assistant registry integration
- Standardized error handling
- Improved repository query filtering
- Updated assistant lifecycle management

### Fixed

- Assistant subsystem type inconsistencies
- Repository interface mismatches
- Registry typing conflicts
- Service implementation inconsistencies
- Repository filtering defects
- Test suite compatibility issues
- Mypy errors
- Pylance diagnostics
- Environment synchronization

### Testing

Successfully completed:

- 142 automated tests

Result:

```
142 passed in 34.05s
```

No failing tests remain.

### Infrastructure

Development environment migrated to:

- uv
- Python virtual environment
- OpenAI API integration
- synchronized dependency management



# 0.1.4
Completed:
- Integrated app launches by default
- Repair dashboard HTML endpoint
- Dashboard JSON endpoint
- Session authentication verified
- Dashboard empty-state verified
- 54 tests passing
- 87.85% coverage

## 0.1.3

- Added SQLAlchemy 2.x persistence, Alembic migrations, repository protocols, SQL repositories, durable approvals/audit/conversations/messages/repair intakes/preferences/mock metadata, dry-run retention cleanup, and expanded tests/documentation.

## 0.1.2

- Added clean FastAPI application factory, safe settings, mock identity, middleware, structured errors, API routes, in-memory repositories, mock providers, accessible local UI, PWA shell, tests, and documentation.

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

## Unreleased

- Added `NOCTURNIX_CODING_PROVIDER=mock|openai` for the browser coding assistant.
- Added a deterministic `nocturnix-mock` provider that exercises task, result, authentication, API, persistence, and browser flows without network calls or API credit usage.
- Cleaned the assistant task/result Alembic migration so it only creates and drops assistant tables and indexes.

## v0.1.5 - Repository awareness foundation

- Added authenticated, read-only repository status, file listing, filename/content search, and safe file read endpoints for the browser assistant.
- Added selected-file chat context loading with root confinement, ignore rules, extension allowlisting, size limits, and mock-mode attached-file reporting.
- Added a plain JavaScript repository panel to `/assistant` for search, preview, selection, and removal.
