from __future__ import annotations

from nocturnix.assistant.exceptions import AssistantTaskStateError
from nocturnix.assistant.registry import AssistantToolRegistry
from nocturnix.assistant.repositories import AssistantTaskRepository, Identifier
from nocturnix.persistence.models import (
    AssistantPatchProposalRow,
    AssistantResultRow,
    AssistantTaskRow,
)


class AssistantTaskService:
    def __init__(
        self,
        repository: AssistantTaskRepository,
        registry: AssistantToolRegistry | None = None,
    ) -> None:
        self._repository = repository
        self._registry = registry

    def create_task(
        self,
        *,
        owner_user_id: Identifier,
        task_type: str,
        title: str,
        instructions: str,
        conversation_id: Identifier | None = None,
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

    def get_task(
        self,
        task_id: Identifier,
        owner_user_id: Identifier | None = None,
    ) -> AssistantTaskRow:
        return self._repository.get_task(task_id, owner_user_id)

    def list_tasks(
        self,
        *,
        owner_user_id: Identifier,
        conversation_id: Identifier | None = None,
        status: str | None = None,
        task_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AssistantTaskRow]:
        return self._repository.list_tasks(
            owner_user_id=owner_user_id,
            conversation_id=conversation_id,
            status=status,
            task_type=task_type,
            limit=limit,
            offset=offset,
        )

    def start_task(
        self,
        task_id: Identifier,
        *,
        owner_user_id: Identifier | None = None,
    ) -> AssistantTaskRow:
        task = self._repository.get_task(task_id, owner_user_id)

        self._require_status(
            task,
            allowed={"pending"},
            operation="start",
        )

        return self._repository.set_status(task_id, "running", owner_user_id=owner_user_id)

    def update_progress(
        self,
        task_id: Identifier,
        progress_percent: int,
        *,
        owner_user_id: Identifier | None = None,
    ) -> AssistantTaskRow:
        if not 0 <= progress_percent <= 100:
            raise ValueError("progress_percent must be between 0 and 100.")

        task = self._repository.get_task(task_id, owner_user_id)

        self._require_status(
            task,
            allowed={"running"},
            operation="update progress for",
        )

        return self._repository.set_progress(
            task_id,
            progress_percent,
            owner_user_id=owner_user_id,
        )

    def complete_task(
        self,
        task_id: Identifier,
        *,
        result_summary: str | None = None,
        owner_user_id: Identifier | None = None,
    ) -> AssistantTaskRow:
        task = self._repository.get_task(task_id, owner_user_id)

        self._require_status(
            task,
            allowed={"running"},
            operation="complete",
        )

        return self._repository.complete_task(
            task_id,
            result_summary=result_summary,
            owner_user_id=owner_user_id,
        )

    def fail_task(
        self,
        task_id: Identifier,
        *,
        error_message: str,
        owner_user_id: Identifier | None = None,
    ) -> AssistantTaskRow:
        task = self._repository.get_task(task_id, owner_user_id)

        self._require_status(
            task,
            allowed={"running"},
            operation="fail",
        )

        return self._repository.fail_task(
            task_id,
            error_message=error_message,
            owner_user_id=owner_user_id,
        )

    def cancel_task(
        self,
        task_id: Identifier,
        *,
        reason: str | None = None,
        owner_user_id: Identifier | None = None,
    ) -> AssistantTaskRow:
        task = self._repository.get_task(task_id, owner_user_id)

        self._require_status(
            task,
            allowed={"pending", "running"},
            operation="cancel",
        )

        return self._repository.cancel_task(
            task_id,
            reason=reason,
            owner_user_id=owner_user_id,
        )

    def add_result(
        self,
        *,
        task_id: Identifier,
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
        task_id: Identifier,
        *,
        owner_user_id: Identifier | None = None,
    ) -> list[AssistantResultRow]:
        return self._repository.list_results(task_id, owner_user_id=owner_user_id)

    def get_result(
        self,
        result_id: Identifier,
        owner_user_id: Identifier | None = None,
    ) -> AssistantResultRow:
        return self._repository.get_result(result_id, owner_user_id)

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

    def save_patch_proposal(
        self,
        *,
        owner_user_id: Identifier,
        task_id: Identifier,
        repository_root: str,
        target_file: str,
        instructions: str,
        unified_diff: str,
        original_sha256: str,
        proposed_sha256: str,
        conversation_id: Identifier | None = None,
        metadata_json: dict[str, object] | None = None,
    ) -> AssistantPatchProposalRow:
        return self._repository.add_patch_proposal(
            owner_user_id=owner_user_id,
            task_id=task_id,
            repository_root=repository_root,
            target_file=target_file,
            instructions=instructions,
            unified_diff=unified_diff,
            original_sha256=original_sha256,
            proposed_sha256=proposed_sha256,
            conversation_id=conversation_id,
            metadata_json=metadata_json,
        )

    def get_patch_proposal(
        self,
        proposal_id: Identifier,
        *,
        owner_user_id: Identifier,
    ) -> AssistantPatchProposalRow:
        return self._repository.get_patch_proposal(
            proposal_id,
            owner_user_id=owner_user_id,
        )

    def list_patch_proposals(
        self,
        *,
        owner_user_id: Identifier,
        task_id: Identifier | None = None,
        conversation_id: Identifier | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AssistantPatchProposalRow]:
        return self._repository.list_patch_proposals(
            owner_user_id=owner_user_id,
            task_id=task_id,
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
        )

    def mark_patch_proposal_applied(
        self,
        proposal_id: Identifier,
        *,
        owner_user_id: Identifier,
        applied_by_user_id: Identifier,
    ) -> AssistantPatchProposalRow:
        return self._repository.mark_patch_proposal_applied(
            proposal_id,
            owner_user_id=owner_user_id,
            applied_by_user_id=applied_by_user_id,
        )

    def mark_patch_proposal_failed(
        self,
        proposal_id: Identifier,
        *,
        owner_user_id: Identifier,
        failure_reason: str,
    ) -> AssistantPatchProposalRow:
        return self._repository.mark_patch_proposal_failed(
            proposal_id,
            owner_user_id=owner_user_id,
            failure_reason=failure_reason,
        )
