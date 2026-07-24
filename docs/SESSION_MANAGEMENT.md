
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
