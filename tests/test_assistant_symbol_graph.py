from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.assistant.repository_models import RepositoryFileReference
from nocturnix.assistant.symbol_graph import (
    SymbolEdge,
    SymbolGraph,
    SymbolNode,
    build_project_symbol_graph,
    build_symbol_graph_from_files,
    parse_repository_context_text,
    symbol_graph_for_symbol,
)
from nocturnix.assistant.web_models import AssistantSymbolGraphRequest
from nocturnix.config import Settings


class FakeProvider:
    provider = "mock"
    model = "test-coding-model"

    def answer(self, message: str, context: str | None = None) -> str:
        return "OK"


def make_test_settings(tmp_path: Path, **overrides: dict[str, object]) -> Settings:
    values = {
        "database_url": f"sqlite:///{tmp_path / 'assistant.db'}",
        "database_migration_mode": "auto-test-only",
        "auth_mode": "development_header",
        "allow_development_header_auth": True,
        "coding_provider": "mock",
        "openai_enabled": False,
        "external_providers_enabled": False,
    }
    values.update(overrides)
    return Settings(**values)


def headers(user: str = "owner-one") -> dict[str, str]:
    return {"X-Nocturnix-Dev-User": user}


def test_symbol_graph_builds_module_class_function_method_and_edges(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    file_path = repository_root / "src" / "example.py"
    file_path.parent.mkdir(parents=True)
    file_path.write_text(
        "from fastapi import APIRouter\n"
        "from sqlalchemy import Column, Integer, String\n"
        "from nocturnix.services.business import BusinessService\n\n"
        "router = APIRouter()\n\n"
        "class RepairPricingRequest(BaseModel):\n"
        "    __tablename__ = 'repair_pricing_request'\n"
        "    id = Column(Integer, primary_key=True)\n"
        "    name: str = Column(String)\n\n"
        "class AssistantTaskService(BusinessService):\n"
        "    def process(self, request: RepairPricingRequest) -> None:\n"
        "        self.do_work()\n\n"
        "@router.get('/status')\n"
        "def status() -> str:\n"
        "    return 'ok'\n",
        encoding="utf-8",
    )

    graph = build_project_symbol_graph(repository_root)

    assert any(node.node_type == "module" and node.name == "example" for node in graph.nodes)
    assert any(
        node.node_type == "class" and node.name == "AssistantTaskService" for node in graph.nodes
    )
    assert any(
        node.node_type == "model" and node.name == "RepairPricingRequest" for node in graph.nodes
    )
    assert any(node.node_type == "route" and node.name == "status" for node in graph.nodes)
    assert any(edge.edge_type == "import" for edge in graph.edges)
    assert any(edge.edge_type == "inherits" for edge in graph.edges)
    assert any(edge.edge_type == "call" for edge in graph.edges)
    assert any(edge.edge_type == "annotation" for edge in graph.edges)
    assert any(edge.edge_type == "route_to" for edge in graph.edges)
    assert any(edge.edge_type == "uses_model" for edge in graph.edges)
    assert any(edge.edge_type == "uses_service" for edge in graph.edges)


def test_symbol_graph_deterministic_ordering(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    file_a = repository_root / "a.py"
    file_b = repository_root / "b.py"
    file_a.write_text("def a():\n    pass\n", encoding="utf-8")
    file_b.write_text("def b():\n    pass\n", encoding="utf-8")

    first = build_project_symbol_graph(repository_root)
    second = build_project_symbol_graph(repository_root)

    assert [node.qualified_name for node in first.nodes] == [
        node.qualified_name for node in second.nodes
    ]
    assert [edge.__dict__ for edge in first.edges] == [edge.__dict__ for edge in second.edges]


def test_symbol_graph_depth_and_limit(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    file_path = repository_root / "service.py"
    file_path.write_text(
        "class AService:\n"
        "    def run(self):\n"
        "        self.do()\n\n"
        "class BService:\n"
        "    def do(self):\n"
        "        pass\n",
        encoding="utf-8",
    )

    graph = build_project_symbol_graph(repository_root)
    subgraph = symbol_graph_for_symbol(graph, "service.AService", depth=1, limit=1)

    assert subgraph.root == "service.AService"
    assert len(subgraph.nodes) == 1
    assert len(subgraph.edges) == 0


def test_ignored_files_are_excluded(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    ignored_dir = repository_root / ".git"
    ignored_dir.mkdir()
    ignored_file = ignored_dir / "ignored.py"
    ignored_file.write_text("def hidden(): pass\n", encoding="utf-8")
    visible_file = repository_root / "visible.py"
    visible_file.write_text("def visible(): pass\n", encoding="utf-8")

    graph = build_project_symbol_graph(repository_root)

    assert not any(node.path.startswith(".git/") for node in graph.nodes)
    assert any(node.path == "visible.py" for node in graph.nodes)


def test_symbol_graph_handles_malformed_python(tmp_path: Path) -> None:
    file = RepositoryFileReference(path="broken.py", content="def bad(:\n    pass\n")
    graph = build_symbol_graph_from_files([file])

    assert graph.root is None
    assert len(graph.nodes) == 0
    assert len(graph.edges) == 0


def test_repository_symbol_graph_endpoints_require_auth(tmp_path: Path) -> None:
    settings = make_test_settings(tmp_path)
    app = create_app(settings)
    app.state.coding_provider = FakeProvider()

    with TestClient(app) as client:
        response = client.get(
            "/api/assistant/repository/symbols",
            params={"repository_root": str(tmp_path)},
        )
        assert response.status_code == 401


def test_repository_symbol_graph_endpoint_returns_unknown_symbol_404(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    file = repository_root / "x.py"
    file.write_text("def foo(): pass\n", encoding="utf-8")

    settings = make_test_settings(tmp_path)
    app = create_app(settings)
    app.state.coding_provider = FakeProvider()

    with TestClient(app) as client:
        response = client.post(
            "/api/assistant/repository/symbol-graph",
            headers=headers(),
            json={
                "repository_root": str(repository_root),
                "symbol": "Missing",
                "depth": 1,
                "limit": 10,
            },
        )

    assert response.status_code == 404


def test_mock_provider_architecture_response(tmp_path: Path) -> None:
    from nocturnix.assistant.mock_provider import MockCodingProvider
    from nocturnix.assistant.local_code_summary import summarize_repository_context_text

    content = (
        "File: src/example.py\nclass AssistantTaskService:\n    def run(self):\n        pass\n"
    )
    summary = summarize_repository_context_text(content)

    assert "deterministic local summary" in summary
    assert "AssistantTaskService" in summary


def test_symbol_graph_post_endpoint_returns_graph(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    file = repository_root / "y.py"
    file.write_text("def apple(): pass\n", encoding="utf-8")

    settings = make_test_settings(tmp_path)
    app = create_app(settings)
    app.state.coding_provider = FakeProvider()

    with TestClient(app) as client:
        response = client.post(
            "/api/assistant/repository/symbol-graph",
            headers=headers(),
            json={
                "repository_root": str(repository_root),
                "depth": 1,
                "limit": 10,
            },
        )

    assert response.status_code == 200
    assert response.json()["nodes"]
