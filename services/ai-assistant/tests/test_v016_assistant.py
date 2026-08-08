from pathlib import Path
from tempfile import gettempdir

from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.config import Settings

H = {"X-Nocturnix-Dev-User": "dev-user-001"}


def client() -> TestClient:
    db_path = Path(gettempdir()) / f"nocturnix_v016_test_{id(object())}.db"
    return TestClient(
        create_app(
            Settings(
                database_url=f"sqlite:///{db_path}",
                database_migration_mode="auto-test-only",
                auth_mode="development_header",
                allow_development_header_auth=True,
            )
        )
    )


def test_v016_memory_planning_reminder_dashboard_search_and_commands() -> None:
    c = client()
    memory = c.post(
        "/api/v1/memories",
        headers=H,
        json={
            "title": "Decision: use mock planning",
            "summary": "Keep v0.1.6 development-only",
            "body": "No external AI or live notification integrations.",
            "category": "decision",
            "tags": ["v016", "mock"],
            "pinned": True,
            "favorite": True,
        },
    )
    assert memory.status_code == 200
    memory_id = memory.json()["id"]
    assert c.get("/api/v1/memories", headers=H, params={"q": "planning"}).json()["items"]
    assert "v016" in c.get("/api/v1/memories/tags", headers=H).json()["items"]
    patched = c.put(
        f"/api/v1/memories/{memory_id}",
        headers=H,
        json={"archived": True, "priority": 5},
    ).json()
    assert patched["archived"] is True

    task = c.post(
        "/api/v1/planning/tasks",
        headers=H,
        json={
            "title": "Top 3 review",
            "description": "Pick owner priorities",
            "status": "today",
            "priority": 5,
            "time_estimate_minutes": 10,
            "project_id": "assistant-v016",
        },
    ).json()
    assert task["focus_score"] > 0
    assert c.get("/api/v1/planning/tasks", headers=H, params={"status": "today"}).json()["items"]

    reminder = c.post(
        "/api/v1/business-reminders",
        headers=H,
        json={"title": "Follow up", "body": "Mock notification readiness only"},
    ).json()
    assert reminder["notification_ready"] is True
    assert (
        c.post(f"/api/v1/business-reminders/{reminder['id']}/escalate", headers=H).json()[
            "escalation_level"
        ]
        == 1
    )
    assert (
        c.post(f"/api/v1/business-reminders/{reminder['id']}/complete", headers=H).json()["status"]
        == "completed"
    )

    focus = c.get("/api/v1/focus", headers=H).json()
    assert focus["top_3_tasks"] and focus["quick_win"]
    dashboard = c.get("/api/v1/dashboard", headers=H).json()
    assert dashboard["business_focus_score"] > 0
    assert "assistant-v016" in dashboard["projects"]
    assert c.get("/api/v1/search", headers=H, params={"q": "owner"}).json()["items"]

    command_memory = c.post(
        "/api/v1/assistant/commands",
        headers=H,
        json={"command": "remember this owner prefers top 3"},
    ).json()
    assert command_memory["source"] == "natural_command"
    command_task = c.post(
        "/api/v1/assistant/commands", headers=H, json={"command": "brain dump parking lot idea"}
    ).json()
    assert command_task["status"] == "deferred"
    assert c.delete(f"/api/v1/memories/{memory_id}", headers=H).json()["deleted"] is True
