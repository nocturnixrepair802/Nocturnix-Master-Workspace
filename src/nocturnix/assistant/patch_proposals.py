from __future__ import annotations

import ast
import difflib
import re
from hashlib import sha256
from pathlib import Path

from nocturnix.assistant.patch_models import (
    PatchProposalError,
    PatchProposalResult,
)
from nocturnix.assistant.repository_access import (
    RepositoryAccessError,
    load_repository_context,
)
from nocturnix.assistant.repository_models import RepositoryAccessRequest

MAX_PATCH_FILE_BYTES = 262_144

BLOCKED_FILE_NAMES = {
    ".env",
    ".coverage",
}

BLOCKED_SUFFIXES = {
    ".bak",
    ".db",
    ".key",
    ".pem",
    ".sqlite",
    ".sqlite3",
}

BLOCKED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    "node_modules",
}

CLASS_DOCSTRING_PATTERN = re.compile(
    r"add\s+(?:a\s+)?class\s+docstring\s+to\s+"
    r"(?P<class_name>[A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)


def propose_patch(
    *,
    repository_root: Path,
    instruction: str,
    selected_files: list[str],
    title: str | None = None,
) -> PatchProposalResult:
    normalized_instruction = instruction.strip()

    if not normalized_instruction:
        raise PatchProposalError("Patch proposal instruction must not be blank.")

    if len(selected_files) != 1:
        raise PatchProposalError(
            "The initial patch proposal implementation requires exactly one selected file."
        )

    class_match = CLASS_DOCSTRING_PATTERN.fullmatch(normalized_instruction.rstrip("."))

    if class_match is None:
        raise PatchProposalError(
            "Unsupported patch proposal. The initial implementation "
            "only supports adding a missing class docstring."
        )

    class_name = class_match.group("class_name")
    selected_path = selected_files[0]
    resolved_root = repository_root.resolve()

    if not resolved_root.exists() or not resolved_root.is_dir():
        raise PatchProposalError("The configured repository root does not exist.")

    resolved_file = _validate_selected_file(
        resolved_root,
        selected_path,
    )

    try:
        repository_context = load_repository_context(
            RepositoryAccessRequest(
                repository_root=str(resolved_root),
                selected_files=[selected_path],
                max_file_count=1,
                max_file_content_length=MAX_PATCH_FILE_BYTES,
            )
        )
    except RepositoryAccessError as exc:
        raise PatchProposalError(str(exc)) from exc

    if len(repository_context.files) != 1:
        raise PatchProposalError("The selected repository file could not be loaded.")

    file_reference = repository_context.files[0]
    original_content = file_reference.content

    try:
        parsed_module = ast.parse(
            original_content,
            filename=file_reference.path,
        )
    except SyntaxError as exc:
        raise PatchProposalError(
            "The selected Python file contains invalid syntax and cannot be patched safely."
        ) from exc

    target_class = _find_class(
        parsed_module,
        class_name,
    )

    if target_class is None:
        raise PatchProposalError(f"Class {class_name!r} was not found in {file_reference.path!r}.")

    if ast.get_docstring(target_class, clean=False) is not None:
        raise PatchProposalError(f"Class {class_name!r} already has a docstring.")

    modified_content = _insert_class_docstring(
        original_content,
        target_class,
        class_name,
    )

    original_sha256 = sha256(original_content.encode("utf-8")).hexdigest()

    proposed_sha256 = sha256(modified_content.encode("utf-8")).hexdigest()

    unified_diff = _build_unified_diff(
        file_reference.path,
        original_content,
        modified_content,
    )

    if not unified_diff:
        raise PatchProposalError("The requested patch would not change the selected file.")

    current_content = resolved_file.read_bytes().decode("utf-8")

    if current_content != original_content:
        raise PatchProposalError("The selected file changed while the proposal was generated.")

    proposal_title = (
        title.strip() if title is not None and title.strip() else f"Document {class_name}"
    )

    return PatchProposalResult(
        title=proposal_title,
        summary=(f"Adds a missing class docstring to {class_name}."),
        affected_files=[file_reference.path],
        unified_diff=unified_diff,
        original_sha256=original_sha256,
        proposed_sha256=proposed_sha256,
        warnings=[
            "This proposal was generated locally.",
            "The proposed patch has not been applied.",
        ],
    )


def _validate_selected_file(
    repository_root: Path,
    selected_path: str,
) -> Path:
    normalized_path = selected_path.strip()

    if not normalized_path:
        raise PatchProposalError("Selected file path must not be blank.")

    if "\x00" in normalized_path:
        raise PatchProposalError("Selected file path contains an invalid null byte.")

    if "\\" in normalized_path:
        raise PatchProposalError("Selected file paths must use forward slashes.")

    candidate_path = Path(normalized_path)

    if candidate_path.is_absolute():
        raise PatchProposalError("Absolute selected file paths are not allowed.")

    if ".." in candidate_path.parts:
        raise PatchProposalError("Repository path traversal is not allowed.")

    lowered_parts = {part.lower() for part in candidate_path.parts}

    if lowered_parts.intersection(BLOCKED_PARTS):
        raise PatchProposalError("The selected file is inside a blocked repository path.")

    lowered_name = candidate_path.name.lower()

    if (
        lowered_name in BLOCKED_FILE_NAMES
        or lowered_name.startswith(".env.")
        or candidate_path.suffix.lower() in BLOCKED_SUFFIXES
    ):
        raise PatchProposalError("The selected file type is blocked from patch proposals.")

    if candidate_path.suffix.lower() != ".py":
        raise PatchProposalError(
            "The initial patch proposal implementation supports Python files only."
        )

    resolved_file = (repository_root / candidate_path).resolve(strict=False)

    if resolved_file != repository_root and repository_root not in resolved_file.parents:
        raise PatchProposalError("The selected file is outside the repository root.")

    if not resolved_file.exists():
        raise PatchProposalError("The selected repository file does not exist.")

    if not resolved_file.is_file():
        raise PatchProposalError("The selected repository path is not a file.")

    if resolved_file.stat().st_size > MAX_PATCH_FILE_BYTES:
        raise PatchProposalError("The selected repository file is too large.")

    raw_content = resolved_file.read_bytes()

    if b"\x00" in raw_content:
        raise PatchProposalError("Binary repository files cannot be used for patch proposals.")

    try:
        raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PatchProposalError("The selected file is not valid UTF-8 text.") from exc

    return resolved_file


def _find_class(
    module: ast.Module,
    class_name: str,
) -> ast.ClassDef | None:
    for node in ast.walk(module):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node

    return None


def _insert_class_docstring(
    source: str,
    target_class: ast.ClassDef,
    class_name: str,
) -> str:
    source_lines = source.splitlines(keepends=True)

    if not target_class.body:
        raise PatchProposalError(f"Class {class_name!r} has no parseable body.")

    first_statement = target_class.body[0]
    insertion_index = first_statement.lineno - 1
    indentation = " " * first_statement.col_offset
    newline = "\r\n" if "\r\n" in source else "\n"

    docstring_line = f'{indentation}"""Coordinate {class_name} behavior."""{newline}'

    source_lines.insert(
        insertion_index,
        docstring_line,
    )

    return "".join(source_lines)


def _build_unified_diff(
    relative_path: str,
    original_content: str,
    modified_content: str,
) -> str:
    original_lines = original_content.splitlines(keepends=True)
    modified_lines = modified_content.splitlines(keepends=True)

    diff_lines = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{relative_path}",
        tofile=f"b/{relative_path}",
        lineterm="",
    )

    return "\n".join(diff_lines)
