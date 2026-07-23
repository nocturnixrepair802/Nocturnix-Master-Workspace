# Nocturnix AI Assistant

Version 0.1.2 provides a clean, locally runnable, development-only FastAPI foundation. All providers are mocked; the app does not connect to Gmail, Google Calendar, WordPress, Square, production AI providers, customer records, or live external systems.

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn nocturnix.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Public routes include `/`, `/docs`, `/api/v1/health`, and `/api/v1/config/public`. Protected development routes require `X-Nocturnix-Dev-User: dev-user-001`; this is not production authentication.

The v0.1.2 milestone intentionally uses in-memory development repositories. Durable SQL persistence is deferred to v0.1.3.
