# Nocturnix Documentation

## Implemented

Nocturnix v0.1.2 uses the canonical `src/nocturnix/` FastAPI package and single UI directory `src/nocturnix/static/`. It implements health, public config, status, chat, knowledge search, repair intake, approvals, audit, mock email, mock calendar, OpenAPI, and a lightweight accessible local UI.

## Mocked and disabled

AI, email, calendar, approval execution, and knowledge behavior are mock/local only. Gmail, Google Calendar, WordPress, Square, production AI providers, production authentication, notifications, real customer systems, and durable SQL persistence are disabled and planned for later milestones where applicable.

## Security and privacy

Protected endpoints require the development-only `X-Nocturnix-Dev-User` header. Owner-scoped approvals and audit records prevent cross-user access. Audit metadata is redacted before in-memory storage. Responses do not expose secrets, stack traces, raw environment variables, system prompts, or live provider credentials.

## Testing

Run `ruff format --check .`, `ruff check .`, `mypy src tests`, `pytest`, `bandit -c pyproject.toml -r src`, `pip-audit`, TOML validation, and conflict-marker scan. Tests do not call live or paid providers.
