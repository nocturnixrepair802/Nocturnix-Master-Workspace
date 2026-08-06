from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from nocturnix.assistant.repository_models import RepositoryFileReference


def summarize_repository_context_text(context_text: str) -> str:
    files = _parse_repository_context_text(context_text)
    return summarize_repository_files(files)


def summarize_repository_files(files: list[RepositoryFileReference]) -> str:
    if not files:
        return ""

    file_summaries = [summarize_file(file.path, file.content) for file in files]
    return (
        "This response is a deterministic local summary of attached repository files. "
        "No external model or network request was used."
        "\n\n" + "\n\n".join(file_summaries)
    )


def summarize_file(path: str, content: str) -> str:
    extension = Path(path).suffix.lower()
    if extension == ".py":
        return summarize_python_file(path, content)
    if extension in {".md", ".markdown"}:
        return summarize_markdown_file(path, content)
    if extension == ".json":
        return summarize_json_file(path, content)
    return summarize_generic_text_file(path, content)


def _parse_repository_context_text(
    context_text: str,
) -> list[RepositoryFileReference]:
    files: list[RepositoryFileReference] = []
    current_path: str | None = None
    current_lines: list[str] = []

    def append_current_file() -> None:
        if current_path is None:
            return

        files.append(
            RepositoryFileReference(
                path=current_path,
                content="\n".join(current_lines),
            )
        )

    for line in context_text.splitlines():
        if line.startswith("Project context"):
            break

        next_path: str | None = None

        if line.startswith("File: "):
            next_path = line[len("File: ") :].strip()
        elif line.startswith("--- ") and line.endswith(" ---") and len(line) > 8:
            next_path = line[4:-4].strip()

        if next_path is not None:
            append_current_file()
            current_path = next_path
            current_lines = []
            continue

        if current_path is not None:
            current_lines.append(line)

    append_current_file()

    return files


def summarize_python_file(path: str, content: str) -> str:
    line_count = len(content.splitlines())
    non_empty_lines = sum(1 for line in content.splitlines() if line.strip())
    try:
        module = ast.parse(content)
    except SyntaxError:
        return summarize_generic_text_file(
            path,
            content,
            hint="Could not parse as Python source due to syntax errors.",
        )

    module_docstring = ast.get_docstring(module)
    imports = _extract_imported_modules(module)
    classes = _extract_classes(module)
    functions = _extract_functions(module)
    responsibilities = _infer_responsibilities(classes, functions)

    lines = [f"File: {path}", "Type: Python source"]
    lines.append(f"Line count: {line_count}, non-empty lines: {non_empty_lines}")
    if module_docstring:
        first_line = module_docstring.strip().splitlines()[0]
        lines.append(f"Module docstring: {first_line}")
    if imports:
        lines.append(f"Imports: {', '.join(sorted(imports))}")
    if functions:
        lines.append("Top-level functions:")
        for function in functions:
            lines.append(_format_function_summary(function))
    if classes:
        lines.append("Classes:")
        for class_summary in classes:
            lines.extend(_format_class_summary(class_summary))
    if responsibilities:
        lines.append(
            "Responsibilities inferred from member names: " + ", ".join(sorted(responsibilities))
        )
    if not (imports or classes or functions or module_docstring):
        lines.append("No syntactic class, function, or import structure was detected.")
    return "\n".join(lines)


def summarize_markdown_file(path: str, content: str) -> str:
    line_count = len(content.splitlines())
    non_empty_lines = sum(1 for line in content.splitlines() if line.strip())
    headings = [
        match.group(1).strip() for match in re.finditer(r"^#{1,6}\s+(.*)", content, re.MULTILINE)
    ]

    lines = [
        f"File: {path}",
        "Type: Markdown",
        f"Line count: {line_count}, non-empty lines: {non_empty_lines}",
    ]
    if headings:
        lines.append("Headings:")
        lines.extend(f"- {heading}" for heading in headings[:10])
        if len(headings) > 10:
            lines.append(f"- and {len(headings) - 10} more headings")
    else:
        lines.append("No top-level headings were detected.")
    return "\n".join(lines)


def summarize_json_file(path: str, content: str) -> str:
    line_count = len(content.splitlines())
    non_empty_lines = sum(1 for line in content.splitlines() if line.strip())
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return summarize_generic_text_file(
            path,
            content,
            hint="Could not parse as JSON due to syntax errors.",
        )

    lines = [
        f"File: {path}",
        "Type: JSON",
        f"Line count: {line_count}, non-empty lines: {non_empty_lines}",
    ]
    if isinstance(parsed, dict):
        keys = sorted(parsed.keys())
        lines.append(f"Top-level keys: {', '.join(keys) if keys else 'none'}")
    else:
        lines.append(f"Top-level JSON structure: {type(parsed).__name__}")
    return "\n".join(lines)


def summarize_generic_text_file(path: str, content: str, hint: str | None = None) -> str:
    line_count = len(content.splitlines())
    non_empty_lines = sum(1 for line in content.splitlines() if line.strip())
    lines = [
        f"File: {path}",
        f"Line count: {line_count}, non-empty lines: {non_empty_lines}",
    ]
    if hint:
        lines.append(hint)
    return "\n".join(lines)


def _extract_imported_modules(module: ast.Module) -> list[str]:
    imports: set[str] = set()
    for node in module.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return sorted(imports)


def _extract_functions(module: ast.Module) -> list[ast.FunctionDef]:
    return [node for node in module.body if isinstance(node, ast.FunctionDef)]


class _ClassSummary:
    def __init__(
        self,
        name: str,
        bases: list[str],
        docstring: str | None,
        decorators: list[str],
        methods: list[ast.FunctionDef],
    ) -> None:
        self.name = name
        self.bases = bases
        self.docstring = docstring
        self.decorators = decorators
        self.methods = methods


def _extract_classes(module: ast.Module) -> list[_ClassSummary]:
    classes: list[_ClassSummary] = []
    for node in module.body:
        if isinstance(node, ast.ClassDef):
            bases = [name for base in node.bases if (name := _expr_name(base)) is not None]
            docstring = ast.get_docstring(node)
            decorators = [
                name
                for decorator in node.decorator_list
                if (name := _expr_name(decorator)) is not None
            ]
            methods = [child for child in node.body if isinstance(child, ast.FunctionDef)]
            classes.append(_ClassSummary(node.name, bases, docstring, decorators, methods))
    return classes


def _format_function_summary(function: ast.FunctionDef) -> str:
    name = function.name
    decorator_names = []
    for dec in function.decorator_list:
        dec_name = _expr_name(dec)
        if dec_name is not None:
            decorator_names.append(dec_name)
    if decorator_names:
        dec_list = f" [{' '.join(decorator_names)}]"
    else:
        dec_list = ""
    docstring = ast.get_docstring(function)
    doc_line = f" — {docstring.strip().splitlines()[0]}" if docstring else ""
    return f"- function {name}(){dec_list}{doc_line}"


def _format_class_summary(class_summary: _ClassSummary) -> list[str]:
    header = f"- class {class_summary.name}"
    if class_summary.bases:
        header += f"({', '.join(class_summary.bases)})"
    if class_summary.decorators:
        header += f" [{' '.join(class_summary.decorators)}]"
    result = [header]
    if class_summary.docstring:
        first_line = class_summary.docstring.strip().splitlines()[0]
        result.append(f"  doc: {first_line}")
    public_methods = [method for method in class_summary.methods if not method.name.startswith("_")]
    if public_methods:
        result.append("  public methods:")
        for method in public_methods:
            method_doc = ast.get_docstring(method)
            doc_line = f" — {method_doc.strip().splitlines()[0]}" if method_doc else ""
            result.append(f"  - {method.name}(){doc_line}")
    else:
        result.append("  public methods: none detected")
    return result


def _expr_name(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        value = _expr_name(node.value)
        if value:
            return f"{value}.{node.attr}"
        return node.attr
    if isinstance(node, ast.Call):
        return _expr_name(node.func)
    if isinstance(node, ast.Subscript):
        return _expr_name(node.value)
    if isinstance(node, ast.Constant):
        return str(node.value)
    return None


def _infer_responsibilities(
    classes: list[_ClassSummary],
    functions: list[ast.FunctionDef],
) -> set[str]:
    hints: set[str] = set()
    for function in functions:
        hints.update(_hint_from_name(function.name))
    for class_summary in classes:
        hints.update(_hint_from_name(class_summary.name))
        for method in class_summary.methods:
            hints.update(_hint_from_name(method.name))
    return hints


def _hint_from_name(name: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z][a-z]*|[0-9]+", name)
    if not tokens:
        return set()
    normalized = " ".join(token.lower() for token in tokens)
    return {normalized}
