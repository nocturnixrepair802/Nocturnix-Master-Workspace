from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from nocturnix.assistant.exceptions import AssistantTaskNotFoundError
from nocturnix.persistence.models import AssistantResultRow, AssistantTaskRow


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AssistantTaskRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_task(
        self,
        *,
        owner_user_id: str,
        task_type: str,
        title: str,
        instructions: str,
        conversation_id: str | None = None,
        input_data: dict[str, object] | None = None,
        status: str = "pending",
    ) -> AssistantTaskRow:
        now = _utc_now()

        task = AssistantTaskRow(
            id=str(uuid4()),
            owner_user_id=owner_user_id,
            conversation_id=conversation_id,
            task_type=task_type,
            title=title,
            instructions=instructions,
            status=status,
            progress_percent=0,
            input_data=input_data or {},
            result_summary=None,
            error_message=None,
            created_at=now,
            started_at=None,
            completed_at=None,
            updated_at=now,
        )

        self._session.add(task)
        self._session.commit()
        self._session.refresh(task)

        return task

    def get_task(self, task_id: str) -> AssistantTaskRow:
        task = self._session.get(AssistantTaskRow, task_id)

        if task is None:
            raise AssistantTaskNotFoundError(f"Assistant task {task_id!r} was not found.")

        return task

    def list_tasks(
        self,
        *,
        owner_user_id: str | None = None,
        conversation_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AssistantTaskRow]:
        statement: Select[tuple[AssistantTaskRow]] = select(AssistantTaskRow)

        if owner_user_id is not None:
            statement = statement.where(AssistantTaskRow.owner_user_id == owner_user_id)

        if conversation_id is not None:
            statement = statement.where(AssistantTaskRow.conversation_id == conversation_id)

        if status is not None:
            statement = statement.where(AssistantTaskRow.status == status)

        statement = (
            statement.order_by(AssistantTaskRow.created_at.desc()).offset(offset).limit(limit)
        )

        return list(self._session.scalars(statement).all())

    def set_status(
        self,
        task_id: str,
        status: str,
    ) -> AssistantTaskRow:
        task = self.get_task(task_id)
        now = _utc_now()

        task.status = status
        task.updated_at = now

        if status == "running" and task.started_at is None:
            task.started_at = now

        if status in {"completed", "failed", "cancelled"}:
            task.completed_at = now

        self._session.commit()
        self._session.refresh(task)

        return task

    def set_progress(
        self,
        task_id: str,
        progress_percent: int,
    ) -> AssistantTaskRow:
        if not 0 <= progress_percent <= 100:
            raise ValueError("progress_percent must be between 0 and 100.")

        task = self.get_task(task_id)

        task.progress_percent = progress_percent
        task.updated_at = _utc_now()

        self._session.commit()
        self._session.refresh(task)

        return task

    def complete_task(
        self,
        task_id: str,
        *,
        result_summary: str | None = None,
    ) -> AssistantTaskRow:
        task = self.get_task(task_id)
        now = _utc_now()

        task.status = "completed"
        task.progress_percent = 100
        task.result_summary = result_summary
        task.error_message = None
        task.completed_at = now
        task.updated_at = now

        self._session.commit()
        self._session.refresh(task)

        return task

    def fail_task(
        self,
        task_id: str,
        *,
        error_message: str,
    ) -> AssistantTaskRow:
        task = self.get_task(task_id)
        now = _utc_now()

        task.status = "failed"
        task.error_message = error_message
        task.completed_at = now
        task.updated_at = now

        self._session.commit()
        self._session.refresh(task)

        return task

    def cancel_task(
        self,
        task_id: str,
        *,
        reason: str | None = None,
    ) -> AssistantTaskRow:
        task = self.get_task(task_id)
        now = _utc_now()

        task.status = "cancelled"
        task.error_message = reason
        task.completed_at = now
        task.updated_at = now

        self._session.commit()
        self._session.refresh(task)

        return task

    def add_result(
        self,
        *,
        owner_user_id: str,
        task_id: str,
        result_type: str,
        title: str,
        summary: str = "",
        content: dict[str, object] | None = None,
        file_path: str | None = None,
        media_type: str | None = None,
    ) -> AssistantResultRow:
        self.get_task(task_id)

        result = AssistantResultRow(
            id=str(uuid4()),
            owner_user_id=owner_user_id,
            task_id=task_id,
            result_type=result_type,
            title=title,
            summary=summary,
            content=content or {},
            file_path=file_path,
            media_type=media_type,
            created_at=_utc_now(),
        )

        self._session.add(result)
        self._session.commit()
        self._session.refresh(result)

        return result

    def get_result(self, result_id: str) -> AssistantResultRow | None:
        return self._session.get(AssistantResultRow, result_id)

    def list_results(
        self,
        task_id: str,
    ) -> list[AssistantResultRow]:
        self.get_task(task_id)

        statement = (
            select(AssistantResultRow)
            .where(AssistantResultRow.task_id == task_id)
            .order_by(AssistantResultRow.created_at.asc())
        )

        return list(self._session.scalars(statement).all())
