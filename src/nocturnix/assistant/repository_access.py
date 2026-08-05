from __future__ import annotations

from pathlib import Path

from nocturnix.assistant.repository_models import (
    RepositoryAccessRequest,
    RepositoryContext,
    RepositoryFileReference,
)


class RepositoryAccessError(RuntimeError):
    pass


def _resolve_repository_path(root: Path, file_path: str) -> Path:
    candidate = root.joinpath(file_path)
    resolved = candidate.resolve(strict=False)
    if root not in resolved.parents and resolved != root:
        raise RepositoryAccessError(
            f"Repository file path {file_path!r} is outside repository root {root!s}."
        )
    return resolved


def load_repository_context(
    request: RepositoryAccessRequest,
) -> RepositoryContext:
    root = Path(request.repository_root)
    if not root.exists():
        raise RepositoryAccessError(f"Repository root {request.repository_root!r} does not exist.")
    if not root.is_dir():
        raise RepositoryAccessError(
            f"Repository root {request.repository_root!r} is not a directory."
        )

    resolved_root = root.resolve()

    if len(request.selected_files) > request.max_file_count:
        raise RepositoryAccessError(
            f"Cannot load more than {request.max_file_count} repository files."
        )

    files: list[RepositoryFileReference] = []

    for raw_path in request.selected_files:
        resolved_path = _resolve_repository_path(resolved_root, raw_path)

        if not resolved_path.exists():
            raise RepositoryAccessError(
                f"Repository file {raw_path!r} does not exist under {resolved_root!s}."
            )
        if not resolved_path.is_file():
            raise RepositoryAccessError(f"Repository path {raw_path!r} is not a file.")

        content = resolved_path.read_text(encoding="utf-8", errors="replace")
        if len(content) > request.max_file_content_length:
            content = content[: request.max_file_content_length]

        relative_path = resolved_path.relative_to(resolved_root).as_posix()
        files.append(
            RepositoryFileReference(
                path=relative_path,
                content=content,
            )
        )

    return RepositoryContext(
        repository_root=str(resolved_root),
        files=files,
    )


def build_repository_context_text(context: RepositoryContext) -> str:
    if not context.files:
        return ""

    snippets: list[str] = []
    for file in context.files:
        snippets.append(f"File: {file.path}\n{file.content}")
    return "\n\n".join(snippets)
