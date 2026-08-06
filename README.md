...entire README contents...

## Initial browser coding assistant

The integrated FastAPI application now serves a development-only coding assistant at
`http://127.0.0.1:8000/assistant`. Configure `OPENAI_API_KEY` and `OPENAI_MODEL`, then explicitly
enable the provider with `NOCTURNIX_OPENAI_ENABLED=true` and
`NOCTURNIX_EXTERNAL_PROVIDERS_ENABLED=true`. Apply migrations and start the existing app:

```powershell
uv run alembic upgrade head
uv run uvicorn nocturnix:create_app --factory --host 127.0.0.1 --port 8000
```

The browser uses the existing session/CSRF authentication or the explicitly enabled
development-header mode. It sends questions to the server; credentials never enter browser code.
This phase generates advice only: it cannot read selected files, edit the repository, execute shell
commands, use web research, or perform autonomous Git operations. Validate with `uv run ruff check
src tests`, `uv run python -m mypy src tests`, `uv run python -m pyright src tests`, and `uv run
pytest`.
# Development Update – July 30, 2026

## Current Project Status

The Nocturnix AI Platform has completed a major stabilization milestone.

The backend infrastructure is now considered stable for continued feature development.

### Completed

- Assistant subsystem fully repaired
- Repository and service interfaces standardized
- Identifier handling unified across assistant services
- Assistant registry typing corrected
- Repository filtering logic repaired
- Test suite updated and synchronized with implementation
- Static type checking errors resolved
- OpenAI API integration configured
- Development environment migrated to `uv`
- Virtual environment rebuilt and synchronized

### Verification

All automated verification completed successfully.

```
142 tests passed
```

Additional verification:

- Ruff formatting
- Ruff linting
- Mypy
- Pylance diagnostics

All are currently clean.

---

## Current Architecture

Current major components include:

- Assistant Engine
- Pricing Engine
- Persistence Layer
- Repository Layer
- Service Layer
- Validation
- Testing Framework

The next development phase will expose these services through a FastAPI web application rather than building duplicate functionality.

---

## Next Milestone

Development focus shifts from infrastructure repair to product assembly.

Planned additions:

- FastAPI web interface
- Browser-based AI assistant
- Authentication
- Project management
- AI coding assistant
- Existing assistant service integration
- Private online deployment

The objective is to transform Nocturnix from a backend platform into a usable browser-based AI application.

## Development coding provider

For zero-cost local browser-assistant testing, run the coding assistant with the deterministic mock provider:

```bash
NOCTURNIX_CODING_PROVIDER=mock
NOCTURNIX_AUTH_MODE=development_header
NOCTURNIX_ALLOW_DEVELOPMENT_HEADER_AUTH=true
```

Mock mode makes no external calls, consumes no API credit, and is intended only for development and UI testing. It does not provide real model intelligence, but it still exercises authentication, persistence, assistant tasks, assistant results, API routing, and browser rendering.

To use the real OpenAI coding provider instead, opt in explicitly:

```bash
NOCTURNIX_CODING_PROVIDER=openai
NOCTURNIX_OPENAI_ENABLED=true
NOCTURNIX_EXTERNAL_PROVIDERS_ENABLED=true
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5-mini
```

## Development repository awareness

The browser assistant exposes authenticated, read-only repository awareness for local development. Configure `NOCTURNIX_REPOSITORY_ROOT` to the project directory and use:

- `GET /api/assistant/repository/status`
- `GET /api/assistant/repository/files?prefix=src/nocturnix&extension=.py`
- `POST /api/assistant/repository/search`
- `GET /api/assistant/repository/file?path=src/nocturnix/assistant/service.py`

Only safe text formats are approved: `.py`, `.pyi`, `.md`, `.txt`, `.toml`, `.yaml`, `.yml`, `.json`, `.html`, `.css`, `.js`, `.ts`, `.tsx`, `.jsx`, and `.sql`. Ignored paths include Git internals, virtual environments, caches, coverage output, `node_modules`, build output, local databases, `.env` files, private keys, and backups. Paths are confined to the configured repository root; traversal, absolute paths, Windows drive letters, UNC paths, symlink escape, null bytes, binary files, and oversized files are rejected.

The `/assistant` page includes a repository panel for filename/content search, safe preview, and selected-file attachment. Selected files are loaded server-side through the same read-only validator and included as untrusted context for the assistant request. Mock mode lists attached file names without claiming semantic understanding, makes no external network request, and consumes no API credit. This is not semantic search and does not write, edit, execute shell commands, mutate Git, commit, push, or access arbitrary filesystem locations.
