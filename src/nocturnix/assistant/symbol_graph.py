from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from nocturnix.assistant.repository_models import RepositoryFileReference

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
DEFAULT_SYMBOL_EXTENSIONS = [".py"]
HTTP_METHODS = {
    "get",
    "post",
    "put",
    "delete",
    "patch",
    "head",
    "options",
}


@dataclass(frozen=True)
class SymbolNode:
    name: str
    qualified_name: str
    path: str
    line_number: int
    node_type: str


@dataclass(frozen=True)
class SymbolEdge:
    source: str
    target: str
    edge_type: str
    path: str
    line_number: int


@dataclass(frozen=True)
class SymbolGraph:
    root: str | None
    nodes: list[SymbolNode]
    edges: list[SymbolEdge]


def build_project_symbol_graph(
    repository_root: Path,
    extensions: list[str] | None = None,
    max_nodes: int = 500,
    max_edges: int = 1000,
) -> SymbolGraph:
    repository_root = repository_root.resolve()
    if not repository_root.exists() or not repository_root.is_dir():
        raise ValueError(
            f"Repository root {repository_root!s} does not exist or is not a directory."
        )

    normalized_extensions = _normalize_extensions(extensions)
    files: list[RepositoryFileReference] = []
    for path in sorted(repository_root.rglob("*")):
        if not path.is_file():
            continue
        if _is_ignored(path, repository_root):
            continue
        if path.suffix.lower() not in normalized_extensions:
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        relative_path = path.relative_to(repository_root).as_posix()
        files.append(
            RepositoryFileReference(
                path=relative_path,
                content=content,
            )
        )

    return build_symbol_graph_from_files(
        files,
        repository_root=repository_root,
        extensions=extensions,
        max_nodes=max_nodes,
        max_edges=max_edges,
    )


def build_symbol_graph_from_files(
    files: list[RepositoryFileReference],
    repository_root: Path | None = None,
    extensions: list[str] | None = None,
    max_nodes: int = 500,
    max_edges: int = 1000,
) -> SymbolGraph:
    if repository_root is None:
        repository_root = Path(".")

    normalized_extensions = _normalize_extensions(extensions)
    filtered_files = [
        file for file in files if Path(file.path).suffix.lower() in normalized_extensions
    ]
    parsed_files: dict[str, ast.Module] = {}
    valid_files: list[RepositoryFileReference] = []
    for file in filtered_files:
        parsed = _parse_source(file.content)
        if parsed is None:
            continue
        parsed_files[file.path] = parsed
        valid_files.append(file)

    nodes: list[SymbolNode] = []
    edges: list[SymbolEdge] = []
    module_names: dict[str, RepositoryFileReference] = {}

    for file in valid_files:
        module_name = _module_name(file.path)
        module_node = SymbolNode(
            name=module_name.split(".")[-1],
            qualified_name=module_name,
            path=file.path,
            line_number=1,
            node_type="module",
        )
        nodes.append(module_node)
        module_names[module_name] = file

    # Collect symbols and raw relationships from parsed modules.
    raw_edges: list[tuple[str, str, str, str, int]] = []
    symbol_index: dict[str, SymbolNode] = {node.qualified_name: node for node in nodes}
    simple_name_index: dict[str, list[str]] = {}

    for file in valid_files:
        module_name = _module_name(file.path)
        parsed = parsed_files[file.path]

        collector = _ModuleSymbolCollector(module_name, file.path)
        collector.visit(parsed)
        nodes.extend(collector.nodes)
        raw_edges.extend(collector.raw_edges)
        for node in collector.nodes:
            simple_name_index.setdefault(node.name, []).append(node.qualified_name)
            symbol_index[node.qualified_name] = node

    # Resolve raw edges into concrete SymbolEdge objects.
    for edge_type, source, target_name, path, line_number in raw_edges:
        target = _resolve_target(target_name, symbol_index, simple_name_index)
        edges.append(
            SymbolEdge(
                source=source,
                target=target,
                edge_type=edge_type,
                path=path,
                line_number=line_number,
            )
        )

    # Add inferred relationship edges for known node types.
    for edge in list(edges):
        if edge.edge_type in {"call", "annotation", "route_to", "import", "inherits"}:
            target_node = symbol_index.get(edge.target)
            source_node = symbol_index.get(edge.source)
            target_name = edge.target

            if target_node is not None and source_node is not None:
                if target_node.node_type == "model":
                    edges.append(_inferred_edge(edge, "uses_model"))
            if source_node is not None and source_node.node_type in {
                "class",
                "route",
                "function",
                "method",
            }:
                if target_name.endswith("Repository"):
                    edges.append(_inferred_edge(edge, "uses_repository"))
                if target_name.endswith("Service"):
                    edges.append(_inferred_edge(edge, "uses_service"))
            if (
                edge.edge_type == "call"
                and source_node is not None
                and source_node.node_type == "route"
            ):
                edges.append(_inferred_edge(edge, "route_to"))

    nodes = _sort_nodes(nodes)[:max_nodes]
    allowed_node_names = {node.qualified_name for node in nodes}
    edges = [
        edge
        for edge in _sort_edges(edges)
        if edge.source in allowed_node_names
        and (
            edge.target in allowed_node_names
            or edge.edge_type
            in {
                "import",
                "inherits",
                "call",
                "annotation",
                "route_to",
                "uses_model",
                "uses_service",
                "uses_repository",
            }
        )
    ][:max_edges]

    return SymbolGraph(root=None, nodes=nodes, edges=edges)


def symbol_graph_for_symbol(
    graph: SymbolGraph,
    symbol: str,
    depth: int = 1,
    limit: int = 100,
) -> SymbolGraph:
    root_node = _resolve_symbol_node(graph, symbol)
    if root_node is None:
        raise KeyError(f"Symbol {symbol!r} not found in graph.")

    if depth < 0:
        depth = 0
    max_nodes = max(1, limit)
    included: set[str] = {root_node.qualified_name}
    frontier: list[str] = [root_node.qualified_name]
    next_frontier: list[str] = []
    current_depth = 0

    outgoing = _build_adjacency(graph.edges)
    incoming = _build_adjacency(graph.edges, reverse=True)

    while frontier and current_depth < depth and len(included) < max_nodes:
        next_frontier.clear()
        for source in frontier:
            for neighbor in outgoing.get(source, []):
                if neighbor not in included and len(included) < max_nodes:
                    included.add(neighbor)
                    next_frontier.append(neighbor)
            for neighbor in incoming.get(source, []):
                if neighbor not in included and len(included) < max_nodes:
                    included.add(neighbor)
                    next_frontier.append(neighbor)
        frontier, next_frontier = next_frontier, []
        current_depth += 1

    selected_nodes = [node for node in graph.nodes if node.qualified_name in included]
    selected_edges = [
        edge for edge in graph.edges if edge.source in included and edge.target in included
    ]
    return SymbolGraph(
        root=root_node.qualified_name,
        nodes=_sort_nodes(selected_nodes),
        edges=_sort_edges(selected_edges),
    )


def parse_repository_context_text(context_text: str) -> list[RepositoryFileReference]:
    files: list[RepositoryFileReference] = []
    current_path: str | None = None
    current_lines: list[str] = []

    for line in context_text.splitlines():
        if line.startswith("Project context"):
            break
        if line.startswith("File: "):
            if current_path is not None:
                files.append(
                    RepositoryFileReference(
                        path=current_path,
                        content="\n".join(current_lines),
                    )
                )
            current_path = line[len("File: ") :].strip()
            current_lines = []
        elif current_path is not None:
            current_lines.append(line)

    if current_path is not None:
        files.append(
            RepositoryFileReference(
                path=current_path,
                content="\n".join(current_lines),
            )
        )

    return files


def find_symbol_candidates(graph: SymbolGraph, symbol: str) -> list[SymbolNode]:
    if not symbol:
        return []
    candidates = [
        node for node in graph.nodes if node.qualified_name == symbol or node.name == symbol
    ]
    return candidates


def _normalize_extensions(extensions: list[str] | None) -> list[str]:
    if extensions is None:
        return DEFAULT_SYMBOL_EXTENSIONS[:]
    normalized: list[str] = []
    for extension in extensions:
        candidate = extension.strip().lower()
        if not candidate:
            continue
        if not candidate.startswith("."):
            candidate = f".{candidate}"
        normalized.append(candidate)
    return normalized or DEFAULT_SYMBOL_EXTENSIONS[:]


def _is_ignored(path: Path, root: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return True
    for part in relative_parts:
        if part in IGNORED_DIRECTORY_NAMES or part.startswith("."):
            return True
    return False


def _module_name(path: str) -> str:
    normalized = Path(path)
    if normalized.name == "__init__.py":
        module = normalized.parent
    else:
        module = normalized.with_suffix("")
    module_parts = [part for part in module.parts if part]
    return ".".join(module_parts)


def _parse_source(source: str) -> ast.Module | None:
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


class _ModuleSymbolCollector(ast.NodeVisitor):
    def __init__(self, module_name: str, path: str) -> None:
        self.module_name = module_name
        self.path = path
        self.nodes: list[SymbolNode] = []
        self.raw_edges: list[tuple[str, str, str, str, int]] = []
        self.current_class: str | None = None
        self.current_function: str | None = None

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            target_name = alias.name
            self.raw_edges.append(("import", self.module_name, target_name, self.path, node.lineno))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module_name = node.module or ""
        if module_name:
            self.raw_edges.append(("import", self.module_name, module_name, self.path, node.lineno))
        for alias in node.names:
            target_name = alias.name
            if module_name:
                target_name = f"{module_name}.{target_name}"
            self.raw_edges.append(("import", self.module_name, target_name, self.path, node.lineno))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualified_name = f"{self.module_name}.{node.name}"
        node_type = "model" if _is_sqlalchemy_model(node) else "class"
        self.nodes.append(
            SymbolNode(
                name=node.name,
                qualified_name=qualified_name,
                path=self.path,
                line_number=node.lineno,
                node_type=node_type,
            )
        )
        self.raw_edges.append(("defines", self.module_name, qualified_name, self.path, node.lineno))
        for base in node.bases:
            base_name = _expr_name(base)
            if base_name:
                self.raw_edges.append(
                    ("inherits", qualified_name, base_name, self.path, node.lineno)
                )
        previous_class = self.current_class
        self.current_class = qualified_name
        self.generic_visit(node)
        self.current_class = previous_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if self.current_class is not None:
            qualified_name = f"{self.current_class}.{node.name}"
            node_type = "route" if _is_fastapi_route(node) else "method"
            self.raw_edges.append(
                ("defines", self.current_class, qualified_name, self.path, node.lineno)
            )
        else:
            qualified_name = f"{self.module_name}.{node.name}"
            node_type = "route" if _is_fastapi_route(node) else "function"
            self.raw_edges.append(
                ("defines", self.module_name, qualified_name, self.path, node.lineno)
            )

        self.nodes.append(
            SymbolNode(
                name=node.name,
                qualified_name=qualified_name,
                path=self.path,
                line_number=node.lineno,
                node_type=node_type,
            )
        )

        self._collect_annotations(node, qualified_name)

        previous_function = self.current_function
        self.current_function = qualified_name
        self.generic_visit(node)
        self.current_function = previous_function

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        target_node = self.current_class or self.module_name
        self._collect_annotation(node.annotation, target_node, node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self.current_function is not None:
            target_name = _expr_name(node.func)
            if target_name:
                self.raw_edges.append(
                    ("call", self.current_function, target_name, self.path, node.lineno)
                )
                if _is_service_name(target_name):
                    self.raw_edges.append(
                        (
                            "route_to",
                            self.current_function,
                            target_name,
                            self.path,
                            node.lineno,
                        )
                    )
        self.generic_visit(node)

    def _collect_annotations(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, source: str
    ) -> None:
        if node.returns is not None:
            self._collect_annotation(node.returns, source, node.lineno)
        for arg in node.args.args + node.args.kwonlyargs:
            if arg.annotation is not None:
                self._collect_annotation(arg.annotation, source, arg.lineno)
        if node.args.vararg is not None and node.args.vararg.annotation is not None:
            self._collect_annotation(node.args.vararg.annotation, source, node.args.vararg.lineno)
        if node.args.kwarg is not None and node.args.kwarg.annotation is not None:
            self._collect_annotation(node.args.kwarg.annotation, source, node.args.kwarg.lineno)

    def _collect_annotation(
        self, annotation: ast.AST | None, source: str, line_number: int
    ) -> None:
        if annotation is None:
            return
        names = _annotation_names(annotation)
        for name in sorted(names):
            self.raw_edges.append(("annotation", source, name, self.path, line_number))


def _resolve_target(
    target_name: str,
    symbol_index: dict[str, SymbolNode],
    simple_name_index: dict[str, list[str]],
) -> str:
    if target_name in symbol_index:
        return target_name
    candidates = simple_name_index.get(target_name, [])
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        return sorted(candidates)[0]
    return target_name


def _inferred_edge(edge: SymbolEdge, edge_type: str) -> SymbolEdge:
    return SymbolEdge(
        source=edge.source,
        target=edge.target,
        edge_type=edge_type,
        path=edge.path,
        line_number=edge.line_number,
    )


def _sort_nodes(nodes: Iterable[SymbolNode]) -> list[SymbolNode]:
    return sorted(
        nodes,
        key=lambda node: (
            node.path,
            node.node_type,
            node.qualified_name,
        ),
    )


def _sort_edges(edges: Iterable[SymbolEdge]) -> list[SymbolEdge]:
    return sorted(
        edges,
        key=lambda edge: (
            edge.path,
            edge.line_number,
            edge.edge_type,
            edge.source,
            edge.target,
        ),
    )


def _resolve_symbol_node(graph: SymbolGraph, symbol: str) -> SymbolNode | None:
    exact = next((node for node in graph.nodes if node.qualified_name == symbol), None)
    if exact is not None:
        return exact
    candidates = [node for node in graph.nodes if node.name == symbol]
    if len(candidates) == 1:
        return candidates[0]
    return None


def _build_adjacency(edges: list[SymbolEdge], reverse: bool = False) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        key = edge.target if reverse else edge.source
        value = edge.source if reverse else edge.target
        if key not in adjacency:
            adjacency[key] = set()
        adjacency[key].add(value)
    return adjacency


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
    if isinstance(node, ast.Subscript):
        return _expr_name(node.value)
    if isinstance(node, ast.Call):
        return _expr_name(node.func)
    return None


def _annotation_names(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, ast.Attribute):
        return {_expr_name(node)} if _expr_name(node) is not None else set()
    if isinstance(node, ast.Subscript):
        names = _annotation_names(node.value)
        if isinstance(node.slice, ast.AST):
            names |= _annotation_names(node.slice)
        return names
    if isinstance(node, ast.Tuple) or isinstance(node, ast.List):
        names: set[str] = set()
        for element in node.elts:
            names |= _annotation_names(element)
        return names
    if isinstance(node, ast.Constant):
        return set()
    if isinstance(node, ast.Call):
        return _annotation_names(node.func)
    return set()


def _is_fastapi_route(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call):
            name = _expr_name(decorator.func)
            if name is not None:
                parts = name.split(".")
                if parts[-1] in HTTP_METHODS and len(parts) >= 2:
                    return True
        elif isinstance(decorator, ast.Attribute):
            if decorator.attr in HTTP_METHODS:
                return True
        elif isinstance(decorator, ast.Name):
            if decorator.id in HTTP_METHODS:
                return True
    return False


def _is_sqlalchemy_model(node: ast.ClassDef) -> bool:
    if any(_expr_name(base) and _expr_name(base).endswith("Base") for base in node.bases):
        return True
    for child in node.body:
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if isinstance(target, ast.Name) and target.id == "__tablename__":
                    return True
            if isinstance(child.value, ast.Call) and _expr_name(child.value.func) == "Column":
                return True
        if isinstance(child, ast.AnnAssign) and _expr_name(child.annotation) == "Column":
            return True
    return False


def _is_service_name(name: str) -> bool:
    return name.endswith("Service")


def is_architecture_question(message: str) -> bool:
    normalized = message.lower()
    return any(
        keyword in normalized
        for keyword in [
            "depends on",
            "architecture around",
            "routes use",
            "models are used",
            "what depends on",
            "show the architecture",
            "which models",
            "depends on",
        ]
    )


def extract_symbol_from_message(message: str, graph: SymbolGraph) -> str | None:
    names = re.findall(r"[A-Z][A-Za-z0-9_]*(?:\.[A-Z][A-Za-z0-9_]*)*", message)
    if not names:
        return None
    qualified = {node.qualified_name for node in graph.nodes}
    for candidate in names:
        if candidate in qualified:
            return candidate
    simple = {node.name: node.qualified_name for node in graph.nodes}
    for candidate in names:
        if candidate in simple:
            return simple[candidate]
    return names[-1] if names else None


def build_graph_summary(message: str, context_text: str) -> str:
    files = parse_repository_context_text(context_text)
    graph = build_symbol_graph_from_files(files)
    if not graph.nodes:
        return (
            "This response is a deterministic local architecture summary. "
            "No external model or network request was used. "
            "No parseable repository symbols were found in the attached files."
        )

    symbol = extract_symbol_from_message(message, graph)
    if not symbol:
        return (
            "This response is a deterministic local architecture summary. "
            "No external model or network request was used. "
            "No specific symbol could be identified from the question. "
            "Available symbols include: "
            + ", ".join(sorted({node.name for node in graph.nodes}))
            + "."
        )

    try:
        focused = symbol_graph_for_symbol(graph, symbol, depth=1, limit=100)
    except KeyError:
        return (
            "This response is a deterministic local architecture summary. "
            "No external model or network request was used. "
            f"The requested symbol {symbol!r} was not found in the local graph."
        )

    direct_dependencies = sorted(
        {edge.target for edge in focused.edges if edge.source == focused.root}
    )
    direct_dependents = sorted(
        {edge.source for edge in focused.edges if edge.target == focused.root}
    )
    related_files = sorted({node.path for node in focused.nodes})
    lines = [
        "This response is a deterministic local architecture summary. No external model or network request was used.",
        f"Root symbol: {focused.root}",
        f"Related files: {', '.join(related_files) if related_files else 'none'}",
        f"Direct dependencies: {', '.join(direct_dependencies) if direct_dependencies else 'none'}",
        f"Direct dependents: {', '.join(direct_dependents) if direct_dependents else 'none'}",
        "Edges:",
    ]
    for edge in focused.edges:
        lines.append(
            f"- {edge.source} --[{edge.edge_type}]--> {edge.target} "
            f"({edge.path}:{edge.line_number})"
        )
    return "\n".join(lines)
