from datetime import UTC, datetime, timedelta

from nocturnix.db import Base, create_database_engine, create_session_factory, session_scope
from nocturnix.persistence.models import ReminderRow
from nocturnix.services.business import (
    BusinessService,
    InAppMockNotificationProvider,
    make_id,
    now_utc,
)


def test_business_focus_briefing_waiting_and_mock_delivery(tmp_path):
    engine = create_database_engine(f"sqlite:///{tmp_path / 'v015.db'}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with session_scope(factory) as session:
        service = BusinessService(session)
        overdue = service.create_task(
            "owner",
            {
                "title": "Call customer",
                "category": "repair",
                "related_repair_id": "r1",
                "priority": "high",
                "due_at": datetime.now(UTC) - timedelta(hours=1),
                "estimated_effort_minutes": 10,
                "next_action": "Call",
            },
        )
        quick = service.create_task(
            "owner",
            {
                "title": "Order label",
                "priority": "normal",
                "estimated_effort_minutes": 5,
                "next_action": "Print",
            },
        )
        waiting = service.create_task(
            "owner",
            {
                "title": "Supplier reply",
                "status": "waiting",
                "waiting_on_type": "supplier",
                "due_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC) - timedelta(days=4),
            },
        )
        service.create_task("owner", {"title": "Too long", "estimated_effort_minutes": 120})
        service.create_task("owner", {"title": "Another", "priority": "low"})
        focus = service.focus_now("owner")
        assert len(focus["items"]) == 3
        assert focus["items"][0]["task"]["id"] == overdue["id"]
        assert any("quick" in reason for reason in focus["items"][1]["explanations"])
        waiting_payload = service.waiting_on("owner")
        assert waiting_payload["items"][0]["id"] == waiting["id"]
        assert waiting_payload["follow_up_today"]
        briefing = service.briefing("owner")
        assert briefing["focus_items"] and briefing["quick_win"]
        eod = service.end_of_day("owner")
        assert eod["unfinished_tasks"] and "reschedule" in eod["recovery_choices"]
        assert service.complete("owner", quick["id"])["status"] == "completed"
        assert (
            service.snooze("owner", overdue["id"], now_utc() + timedelta(minutes=30))["status"]
            == "deferred"
        )
        assert (
            service.reschedule("owner", overdue["id"], now_utc() + timedelta(days=1))["status"]
            == "planned"
        )
        reminder = ReminderRow(
            id=make_id("rem"),
            owner_user_id="owner",
            reminder_type="scheduled",
            scheduled_at=now_utc(),
            status="scheduled",
            priority="normal",
            delivery_channel="in_app_mock",
            title="password token supplier",
            created_at=now_utc(),
        )
        session.add(reminder)
        session.flush()
        event = InAppMockNotificationProvider().deliver(session, reminder)
        assert event.safe_summary == "[REDACTED REMINDER]"
