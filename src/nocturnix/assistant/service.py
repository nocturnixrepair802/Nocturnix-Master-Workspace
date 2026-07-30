from __future__ import annotations

from nocturnix.assistant.exceptions import AssistantTaskStateError
from nocturnix.assistant.registry import AssistantToolRegistry
from nocturnix.assistant.repositories import AssistantTaskRepository
from nocturnix.persistence.models import AssistantResultRow, AssistantTaskRow


class AssistantTaskService:
    def __init__(
        self,
        repository: AssistantTaskRepository,
        registry: AssistantToolRegistry,
    ) -> None:
        self._repository = repository
        self._registry = registry

    def create_task(
        self,
        *,
        owner_user_id: str,
        task_type: str,
        title: str,
        instructions: str,
        conversation_id: str | None = None,
        input_data: dict[str, object] | None = None,
    ) -> AssistantTaskRow:
        return self._repository.create_task(
            owner_user_id=owner_user_id,
            conversation_id=conversation_id,
            task_type=task_type,
            title=title,
            instructions=instructions,
            input_data=input_data,
        )

    def get_task(self, task_id: str) -> AssistantTaskRow:
        return self._repository.get_task(task_id)

    def list_tasks(
        self,
        *,
        owner_user_id: str | None = None,
        conversation_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AssistantTaskRow]:
        return self._repository.list_tasks(
            owner_user_id=owner_user_id,
            conversation_id=conversation_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    def start_task(self, task_id: str) -> AssistantTaskRow:
        task = self._repository.get_task(task_id)

        self._require_status(
            task,
            allowed={"pending"},
            operation="start",
        )

        return self._repository.set_status(task_id, "running")

    def update_progress(
        self,
        task_id: str,
        progress_percent: int,
    ) -> AssistantTaskRow:
        if not 0 <= progress_percent <= 100:
            raise ValueError("progress_percent must be between 0 and 100.")

        task = self._repository.get_task(task_id)

        self._require_status(
            task,
            allowed={"running"},
            operation="update progress for",
        )

        return self._repository.set_progress(
            task_id,
            progress_percent,
        )

    def complete_task(
        self,
        task_id: str,
        *,
        result_summary: str | None = None,
    ) -> AssistantTaskRow:
        task = self._repository.get_task(task_id)

        self._require_status(
            task,
            allowed={"running"},
            operation="complete",
        )

        return self._repository.complete_task(
            task_id,
            result_summary=result_summary,
        )

    def fail_task(
        self,
        task_id: str,
        *,
        error_message: str,
    ) -> AssistantTaskRow:
        task = self._repository.get_task(task_id)

        self._require_status(
            task,
            allowed={"running"},
            operation="fail",
        )

        return self._repository.fail_task(
            task_id,
            error_message=error_message,
        )

    def cancel_task(
        self,
        task_id: str,
        *,
        reason: str | None = None,
    ) -> AssistantTaskRow:
        task = self._repository.get_task(task_id)

        self._require_status(
            task,
            allowed={"pending", "running"},
            operation="cancel",
        )

        return self._repository.cancel_task(
            task_id,
            reason=reason,
        )

    def add_result(
        self,
        *,
        task_id: str,
        result_type: str,
        title: str,
        summary: str = "",
        content: dict[str, object] | None = None,
        file_path: str | None = None,
        media_type: str | None = None,
    ) -> AssistantResultRow:
        task = self._repository.get_task(task_id)

        self._require_status(
            task,
            allowed={"running", "completed"},
            operation="add a result to",
        )

        return self._repository.add_result(
            owner_user_id=task.owner_user_id,
            task_id=task.id,
            result_type=result_type,
            title=title,
            summary=summary,
            content=content,
            file_path=file_path,
            media_type=media_type,
        )

    def list_results(
        self,
        task_id: str,
    ) -> list[AssistantResultRow]:
        return self._repository.list_results(task_id)

    @staticmethod
    def _require_status(
        task: AssistantTaskRow,
        *,
        allowed: set[str],
        operation: str,
    ) -> None:
        if task.status in allowed:
            return

        allowed_text = ", ".join(sorted(allowed))

        raise AssistantTaskStateError(
            f"Cannot {operation} assistant task {task.id!r} "
            f"while its status is {task.status!r}. "
            f"Allowed status values: {allowed_text}."
        )
