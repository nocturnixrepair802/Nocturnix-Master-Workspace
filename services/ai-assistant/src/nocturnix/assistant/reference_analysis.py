from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

IGNORED_DIRECTORY_NAMES = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".pytest_cache",
    "dist",
    "build",
}

DEFAULT_REFERENCE_EXTENSIONS = [".py"]
MAX_EXCERPT_LENGTH = 240
REFERENCE_TYPE_ORDER = {
    "import": 0,
    "from-import": 1,
    "inheritance": 2,
    "decorator": 3,
    "annotation": 4,
    "call": 5,
    "attribute": 6,
    "name": 7,
    "text match": 8,
}


@dataclass(frozen=True)
class RepositoryReferenceItem:
    path: str
    line_number: int
    reference_type: str
    excerpt: str


def analyze_repository_references(
    repository_root: Path,
    symbol: str,
    extensions: list[str] | None = None,
    limit: int = 50,
) -> list[RepositoryReferenceItem]:
    repository_root = repository_root.resolve()
    symbol = symbol.strip()
    if not symbol:
        return []

    if not repository_root.exists() or not repository_root.is_dir():
        raise ValueError(
            f"Repository root {repository_root!s} does not exist or is not a directory."
        )

    normalized_extensions = _normalize_extensions(extensions)
    results: list[RepositoryReferenceItem] = []

    for path in sorted(repository_root.rglob("*")):
        if len(results) >= limit:
            break
        if not path.is_file():
            continue
        if _is_ignored(path, repository_root):
            continue
        if path.suffix.lower() not in normalized_extensions:
            continue

        file_results = _analyze_file_references(path, symbol, repository_root)
        if file_results:
            results.extend(file_results)

    return _sort_references(results)[:limit]


def _normalize_extensions(extensions: list[str] | None) -> list[str]:
    if extensions is None:
        return DEFAULT_REFERENCE_EXTENSIONS[:]

    normalized: list[str] = []
    for extension in extensions:
        candidate = extension.strip().lower()
        if not candidate:
            continue
        if not candidate.startswith("."):
            candidate = f".{candidate}"
        normalized.append(candidate)

    return normalized or DEFAULT_REFERENCE_EXTENSIONS[:]


def _is_ignored(path: Path, root: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return True
    for part in relative_parts:
        if part in IGNORED_DIRECTORY_NAMES or part.startswith("."):
            return True
    return False


def _analyze_file_references(
    path: Path,
    symbol: str,
    repository_root: Path,
) -> list[RepositoryReferenceItem]:
    content = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".py":
        return _analyze_python_references(path, content, symbol, repository_root)
    return _fallback_text_references(path, content, symbol, repository_root)


def _analyze_python_references(
    path: Path,
    content: str,
    symbol: str,
    repository_root: Path,
) -> list[RepositoryReferenceItem]:
    lines = content.splitlines()
    try:
        module = ast.parse(content)
    except SyntaxError:
        return _fallback_text_references(path, content, symbol, repository_root)

    references: list[RepositoryReferenceItem] = []
    seen: set[tuple[int, str, str]] = set()
    relative_path = path.relative_to(repository_root).as_posix()

    def add_reference(line_number: int, reference_type: str, excerpt: str) -> None:
        excerpt = excerpt.strip()
        if len(excerpt) > MAX_EXCERPT_LENGTH:
            excerpt = excerpt[:MAX_EXCERPT_LENGTH].rstrip() + "…"
        key = (line_number, reference_type, excerpt)
        if key in seen:
            return
        seen.add(key)
        references.append(
            RepositoryReferenceItem(
                path=relative_path,
                line_number=line_number,
                reference_type=reference_type,
                excerpt=excerpt,
            )
        )

    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname == symbol or alias.name.split(".")[0] == symbol:
                    add_reference(node.lineno, "import", _source_line(lines, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            for alias in node.names:
                if (
                    alias.name == symbol
                    or alias.asname == symbol
                    or module_name.split(".")[0] == symbol
                ):
                    add_reference(node.lineno, "from-import", _source_line(lines, node.lineno))
        elif isinstance(node, ast.ClassDef):
            if any(_expr_matches(symbol, base) for base in node.bases):
                add_reference(node.lineno, "inheritance", _source_line(lines, node.lineno))
            for decorator in node.decorator_list:
                if _expr_matches(symbol, decorator):
                    add_reference(node.lineno, "decorator", _source_line(lines, node.lineno))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if _expr_matches(symbol, decorator):
                    add_reference(node.lineno, "decorator", _source_line(lines, node.lineno))
            if node.returns and _annotation_matches(symbol, node.returns):
                add_reference(node.lineno, "annotation", _source_line(lines, node.lineno))
            for arg in node.args.args + node.args.kwonlyargs:
                if arg.annotation and _annotation_matches(symbol, arg.annotation):
                    add_reference(arg.lineno, "annotation", _source_line(lines, arg.lineno))
            if (
                node.args.vararg
                and node.args.vararg.annotation
                and _annotation_matches(symbol, node.args.vararg.annotation)
            ):
                add_reference(
                    node.args.vararg.lineno,
                    "annotation",
                    _source_line(lines, node.args.vararg.lineno),
                )
            if (
                node.args.kwarg
                and node.args.kwarg.annotation
                and _annotation_matches(symbol, node.args.kwarg.annotation)
            ):
                add_reference(
                    node.args.kwarg.lineno,
                    "annotation",
                    _source_line(lines, node.args.kwarg.lineno),
                )
        elif isinstance(node, ast.AnnAssign):
            if node.annotation and _annotation_matches(symbol, node.annotation):
                add_reference(node.lineno, "annotation", _source_line(lines, node.lineno))
        elif isinstance(node, ast.Call):
            if _expr_matches(symbol, node.func):
                add_reference(node.lineno, "call", _source_line(lines, node.lineno))
        elif isinstance(node, ast.Attribute):
            if node.attr == symbol:
                add_reference(node.lineno, "attribute", _source_line(lines, node.lineno))
        elif isinstance(node, ast.Name):
            if node.id == symbol:
                add_reference(node.lineno, "name", _source_line(lines, node.lineno))

    return references


def _sort_references(
    references: list[RepositoryReferenceItem],
) -> list[RepositoryReferenceItem]:
    return sorted(
        references,
        key=lambda item: (
            item.path,
            item.line_number,
            REFERENCE_TYPE_ORDER.get(item.reference_type, 99),
            item.excerpt,
        ),
    )


def _source_line(lines: list[str], line_number: int) -> str:
    if 1 <= line_number <= len(lines):
        return lines[line_number - 1].strip()
    return ""


def _expr_matches(symbol: str, node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id == symbol
    if isinstance(node, ast.Attribute):
        return node.attr == symbol or _expr_name(node) == symbol
    return False


def _annotation_matches(symbol: str, node: ast.AST) -> bool:
    if isinstance(node, (ast.Name, ast.Attribute)):
        return _expr_matches(symbol, node)
    if isinstance(node, ast.Subscript):
        return _annotation_matches(symbol, node.value) or _annotation_matches(symbol, node.slice)
    if isinstance(node, ast.Tuple):
        return any(_annotation_matches(symbol, element) for element in node.elts)
    if isinstance(node, ast.List):
        return any(_annotation_matches(symbol, element) for element in node.elts)
    if isinstance(node, ast.Call):
        if _annotation_matches(symbol, node.func):
            return True
        return any(_annotation_matches(symbol, arg) for arg in node.args)
    return False


def _expr_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        value_name = _expr_name(node.value)
        if value_name is None:
            return node.attr
        return f"{value_name}.{node.attr}"
    return None


def _fallback_text_references(
    path: Path,
    content: str,
    symbol: str,
    repository_root: Path,
) -> list[RepositoryReferenceItem]:
    pattern = re.compile(rf"\b{re.escape(symbol)}\b")
    lines = content.splitlines()
    relative_path = path.relative_to(repository_root).as_posix()
    references: list[RepositoryReferenceItem] = []
    seen: set[tuple[int, str, str]] = set()

    for line_number, line in enumerate(lines, start=1):
        if pattern.search(line):
            excerpt = line.strip()
            if len(excerpt) > MAX_EXCERPT_LENGTH:
                excerpt = excerpt[:MAX_EXCERPT_LENGTH].rstrip() + "…"
            key = (line_number, "text match", excerpt)
            if key in seen:
                continue
            seen.add(key)
            references.append(
                RepositoryReferenceItem(
                    path=relative_path,
                    line_number=line_number,
                    reference_type="text match",
                    excerpt=excerpt,
                )
            )
    return references
