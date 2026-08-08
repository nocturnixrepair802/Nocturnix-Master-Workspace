from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.assistant.patch_models import (
    PatchProposalError,
)
from nocturnix.assistant.patch_proposals import (
    propose_patch,
)
from nocturnix.config import Settings


def make_test_settings(
    tmp_path: Path,
) -> Settings:
    return Settings(
        database_url=(f"sqlite:///{tmp_path / 'assistant.db'}"),
        database_migration_mode="auto-test-only",
        auth_mode="development_header",
        allow_development_header_auth=True,
        coding_provider="mock",
        openai_enabled=False,
        external_providers_enabled=False,
        rate_limit_per_minute=500,
    )


def create_repository(
    tmp_path: Path,
) -> tuple[Path, Path]:
    repository_root = tmp_path / "repository"
    source_file = repository_root / "src" / "nocturnix" / "assistant" / "service.py"

    source_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    source_file.write_text(
        ("class AssistantTaskService:\n    def create_task(self) -> None:\n        pass\n"),
        encoding="utf-8",
    )

    return repository_root, source_file


def test_propose_patch_generates_unified_diff_without_writing(
    tmp_path: Path,
) -> None:
    repository_root, source_file = create_repository(tmp_path)

    original_content = source_file.read_text(encoding="utf-8")

    proposal = propose_patch(
        repository_root=repository_root,
        instruction=("Add a class docstring to AssistantTaskService."),
        selected_files=[
            "src/nocturnix/assistant/service.py",
        ],
        title="Document AssistantTaskService",
    )

    assert proposal.title == ("Document AssistantTaskService")
    assert proposal.generated_locally is True
    assert proposal.applied is False
    assert proposal.affected_files == ["src/nocturnix/assistant/service.py"]
    assert "--- a/src/nocturnix/assistant/service.py" in proposal.unified_diff
    assert "+++ b/src/nocturnix/assistant/service.py" in proposal.unified_diff
    assert '"""Coordinate AssistantTaskService behavior."""' in proposal.unified_diff

    assert source_file.read_text(encoding="utf-8") == original_content


def test_propose_patch_rejects_unsupported_instruction(
    tmp_path: Path,
) -> None:
    repository_root, _ = create_repository(tmp_path)

    with pytest.raises(
        PatchProposalError,
        match="Unsupported patch proposal",
    ):
        propose_patch(
            repository_root=repository_root,
            instruction="Refactor the entire project.",
            selected_files=[
                "src/nocturnix/assistant/service.py",
            ],
        )


def test_propose_patch_rejects_path_traversal(
    tmp_path: Path,
) -> None:
    repository_root, _ = create_repository(tmp_path)

    with pytest.raises(
        PatchProposalError,
        match="traversal",
    ):
        propose_patch(
            repository_root=repository_root,
            instruction=("Add a class docstring to AssistantTaskService."),
            selected_files=[
                "../outside.py",
            ],
        )


def test_propose_patch_rejects_env_file(
    tmp_path: Path,
) -> None:
    repository_root, _ = create_repository(tmp_path)

    env_file = repository_root / ".env"
    env_file.write_text(
        "OPENAI_API_KEY=secret",
        encoding="utf-8",
    )

    with pytest.raises(
        PatchProposalError,
        match="blocked",
    ):
        propose_patch(
            repository_root=repository_root,
            instruction=("Add a class docstring to AssistantTaskService."),
            selected_files=[
                ".env",
            ],
        )


def test_patch_proposal_endpoint_requires_authentication(
    tmp_path: Path,
) -> None:
    repository_root, _ = create_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        response = client.post(
            "/api/assistant/repository/propose-patch",
            json={
                "instruction": ("Add a class docstring to AssistantTaskService."),
                "selected_files": [
                    "src/nocturnix/assistant/service.py",
                ],
                "repository_root": str(repository_root),
            },
        )

    assert response.status_code == 401


def test_patch_proposal_endpoint_returns_read_only_diff(
    tmp_path: Path,
) -> None:
    repository_root, source_file = create_repository(tmp_path)

    original_content = source_file.read_text(encoding="utf-8")

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        response = client.post(
            "/api/assistant/repository/propose-patch",
            headers={
                "X-Nocturnix-Dev-User": ("local-developer"),
            },
            json={
                "instruction": ("Add a class docstring to AssistantTaskService."),
                "selected_files": [
                    "src/nocturnix/assistant/service.py",
                ],
                "title": ("Document AssistantTaskService"),
                "repository_root": str(repository_root),
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["title"] == ("Document AssistantTaskService")
    assert payload["generated_locally"] is True
    assert payload["applied"] is False
    assert payload["affected_files"] == ["src/nocturnix/assistant/service.py"]
    assert payload["unified_diff"]

    assert source_file.read_text(encoding="utf-8") == original_content
