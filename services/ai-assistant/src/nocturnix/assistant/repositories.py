from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from nocturnix.assistant.exceptions import (
    AssistantResultNotFoundError,
    AssistantTaskNotFoundError,
)
from nocturnix.persistence.models import (
    AssistantPatchProposalFileRow,
    AssistantPatchProposalRow,
    AssistantResultRow,
    AssistantTaskRow,
)

Identifier = UUID | str


def normalize_id(value: Identifier) -> str:
    return str(value)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AssistantTaskRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_task(
        self,
        *,
        owner_user_id: Identifier,
        task_type: str,
        title: str,
        instructions: str,
        conversation_id: Identifier | None = None,
        input_data: dict[str, object] | None = None,
        status: str = "pending",
    ) -> AssistantTaskRow:
        now = _utc_now()
        owner_id = normalize_id(owner_user_id)
        conversation_key = normalize_id(conversation_id) if conversation_id is not None else None

        task = AssistantTaskRow(
            id=str(uuid4()),
            owner_user_id=owner_id,
            conversation_id=conversation_key,
            task_type=str(task_type),
            title=title,
            instructions=instructions,
            status=str(status),
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

    def get_task(
        self,
        task_id: Identifier,
        owner_user_id: Identifier | None = None,
    ) -> AssistantTaskRow:
        task_key = normalize_id(task_id)

        statement = select(AssistantTaskRow).where(AssistantTaskRow.id == task_key)

        if owner_user_id is not None:
            statement = statement.where(
                AssistantTaskRow.owner_user_id == normalize_id(owner_user_id)
            )

        task = self._session.scalar(statement)

        if task is None:
            raise AssistantTaskNotFoundError(f"Assistant task {task_id!r} was not found.")

        return task

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
        owner_id = normalize_id(owner_user_id)

        statement: Select[tuple[AssistantTaskRow]] = select(AssistantTaskRow).where(
            AssistantTaskRow.owner_user_id == owner_id
        )

        if conversation_id is not None:
            statement = statement.where(
                AssistantTaskRow.conversation_id == normalize_id(conversation_id)
            )

        if status is not None:
            normalized_status = status.strip().lower()
            statement = statement.where(AssistantTaskRow.status == normalized_status)

        if task_type is not None:
            normalized_task_type = task_type.strip()
            statement = statement.where(AssistantTaskRow.task_type == normalized_task_type)

        statement = (
            statement.order_by(
                AssistantTaskRow.created_at.desc(),
                AssistantTaskRow.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return list(self._session.scalars(statement).all())

    def set_status(
        self,
        task_id: Identifier,
        status: str,
        *,
        owner_user_id: Identifier | None = None,
    ) -> AssistantTaskRow:
        task = self.get_task(
            task_id,
            owner_user_id,
        )

        now = _utc_now()
        normalized_status = status.strip().lower()

        task.status = normalized_status
        task.updated_at = now

        if normalized_status == "running" and task.started_at is None:
            task.started_at = now

        if normalized_status in {
            "completed",
            "failed",
            "cancelled",
        }:
            task.completed_at = now

        self._session.commit()
        self._session.refresh(task)

        return task

    def set_progress(
        self,
        task_id: Identifier,
        progress_percent: int,
        *,
        owner_user_id: Identifier | None = None,
    ) -> AssistantTaskRow:
        if not 0 <= progress_percent <= 100:
            raise ValueError("progress_percent must be between 0 and 100.")

        task = self.get_task(
            task_id,
            owner_user_id,
        )

        task.progress_percent = progress_percent
        task.updated_at = _utc_now()

        self._session.commit()
        self._session.refresh(task)

        return task

    def complete_task(
        self,
        task_id: Identifier,
        *,
        result_summary: str | None = None,
        owner_user_id: Identifier | None = None,
    ) -> AssistantTaskRow:
        task = self.get_task(
            task_id,
            owner_user_id,
        )

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
        task_id: Identifier,
        *,
        error_message: str,
        owner_user_id: Identifier | None = None,
    ) -> AssistantTaskRow:
        task = self.get_task(
            task_id,
            owner_user_id,
        )

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
        task_id: Identifier,
        *,
        reason: str | None = None,
        owner_user_id: Identifier | None = None,
    ) -> AssistantTaskRow:
        task = self.get_task(
            task_id,
            owner_user_id,
        )

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
        owner_user_id: Identifier,
        task_id: Identifier,
        result_type: str,
        title: str,
        summary: str = "",
        content: dict[str, object] | None = None,
        file_path: str | None = None,
        media_type: str | None = None,
    ) -> AssistantResultRow:
        owner_id = normalize_id(owner_user_id)
        task_key = normalize_id(task_id)

        self.get_task(
            task_key,
            owner_id,
        )

        result = AssistantResultRow(
            id=str(uuid4()),
            owner_user_id=owner_id,
            task_id=task_key,
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

    def get_result(
        self,
        result_id: Identifier,
        owner_user_id: Identifier | None = None,
    ) -> AssistantResultRow:
        result_key = normalize_id(result_id)

        statement = select(AssistantResultRow).where(AssistantResultRow.id == result_key)

        if owner_user_id is not None:
            statement = statement.where(
                AssistantResultRow.owner_user_id == normalize_id(owner_user_id)
            )

        result = self._session.scalar(statement)

        if result is None:
            raise AssistantResultNotFoundError(f"Assistant result {result_id!r} was not found.")

        return result

    def list_results(
        self,
        task_id: Identifier,
        *,
        owner_user_id: Identifier | None = None,
    ) -> list[AssistantResultRow]:
        task_key = normalize_id(task_id)

        self.get_task(
            task_key,
            owner_user_id,
        )

        statement = select(AssistantResultRow).where(AssistantResultRow.task_id == task_key)

        if owner_user_id is not None:
            statement = statement.where(
                AssistantResultRow.owner_user_id == normalize_id(owner_user_id)
            )

        statement = statement.order_by(AssistantResultRow.created_at.asc())

        return list(self._session.scalars(statement).all())

    def add_patch_proposal(
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
        file_changes: list[dict[str, str]] | None = None,
    ) -> AssistantPatchProposalRow:
        owner_id = normalize_id(owner_user_id)
        task_key = normalize_id(task_id)

        task = self.get_task(
            task_key,
            owner_id,
        )

        conversation_key = (
            normalize_id(conversation_id) if conversation_id is not None else task.conversation_id
        )

        now = _utc_now()

        proposal = AssistantPatchProposalRow(
            id=str(uuid4()),
            owner_user_id=owner_id,
            task_id=task_key,
            conversation_id=conversation_key,
            repository_root=repository_root,
            target_file=target_file,
            instructions=instructions,
            unified_diff=unified_diff,
            original_sha256=original_sha256,
            proposed_sha256=proposed_sha256,
            metadata_json=metadata_json or {},
            status="pending",
            applied_at=None,
            applied_by_user_id=None,
            failure_reason=None,
            created_at=now,
        )

        self._session.add(proposal)

        normalized_changes = file_changes or [
            {
                "path": target_file,
                "unified_diff": unified_diff,
                "original_sha256": original_sha256,
                "proposed_sha256": proposed_sha256,
            }
        ]

        for ordinal, change in enumerate(normalized_changes):
            file_change = AssistantPatchProposalFileRow(
                id=str(uuid4()),
                proposal_id=proposal.id,
                ordinal=ordinal,
                path=change["path"],
                unified_diff=change["unified_diff"],
                original_sha256=change["original_sha256"],
                proposed_sha256=change["proposed_sha256"],
                created_at=now,
            )

            self._session.add(file_change)

        self._session.commit()
        self._session.refresh(proposal)

        return proposal

    def get_patch_proposal(
        self,
        proposal_id: Identifier,
        *,
        owner_user_id: Identifier | None = None,
    ) -> AssistantPatchProposalRow:
        proposal_key = normalize_id(proposal_id)

        statement = select(AssistantPatchProposalRow).where(
            AssistantPatchProposalRow.id == proposal_key
        )

        if owner_user_id is not None:
            statement = statement.where(
                AssistantPatchProposalRow.owner_user_id == normalize_id(owner_user_id)
            )

        proposal = self._session.scalar(statement)

        if proposal is None:
            raise LookupError(f"Assistant patch proposal {proposal_id!r} was not found.")

        return proposal

    def list_patch_proposal_files(
        self,
        proposal_id: Identifier,
        *,
        owner_user_id: Identifier | None = None,
    ) -> list[AssistantPatchProposalFileRow]:
        proposal = self.get_patch_proposal(
            proposal_id,
            owner_user_id=owner_user_id,
        )

        statement = (
            select(AssistantPatchProposalFileRow)
            .where(AssistantPatchProposalFileRow.proposal_id == proposal.id)
            .order_by(AssistantPatchProposalFileRow.ordinal.asc())
        )

        return list(self._session.scalars(statement).all())

    def list_patch_proposals(
        self,
        *,
        owner_user_id: Identifier,
        task_id: Identifier | None = None,
        conversation_id: Identifier | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AssistantPatchProposalRow]:
        owner_id = normalize_id(owner_user_id)

        statement: Select[tuple[AssistantPatchProposalRow]] = select(
            AssistantPatchProposalRow
        ).where(AssistantPatchProposalRow.owner_user_id == owner_id)

        if task_id is not None:
            statement = statement.where(AssistantPatchProposalRow.task_id == normalize_id(task_id))

        if conversation_id is not None:
            statement = statement.where(
                AssistantPatchProposalRow.conversation_id == normalize_id(conversation_id)
            )

        statement = (
            statement.order_by(
                AssistantPatchProposalRow.created_at.desc(),
                AssistantPatchProposalRow.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return list(self._session.scalars(statement).all())

    def mark_patch_proposal_applied(
        self,
        proposal_id: Identifier,
        *,
        owner_user_id: Identifier,
        applied_by_user_id: Identifier,
    ) -> AssistantPatchProposalRow:
        proposal = self.get_patch_proposal(
            proposal_id,
            owner_user_id=owner_user_id,
        )

        if proposal.status != "pending":
            raise ValueError(
                f"Patch proposal {proposal.id!r} "
                f"cannot be applied while its status "
                f"is {proposal.status!r}."
            )

        proposal.status = "applied"
        proposal.applied_at = _utc_now()
        proposal.applied_by_user_id = normalize_id(applied_by_user_id)
        proposal.failure_reason = None

        self._session.commit()
        self._session.refresh(proposal)

        return proposal

    def mark_patch_proposal_failed(
        self,
        proposal_id: Identifier,
        *,
        owner_user_id: Identifier,
        failure_reason: str,
    ) -> AssistantPatchProposalRow:
        proposal = self.get_patch_proposal(
            proposal_id,
            owner_user_id=owner_user_id,
        )

        if proposal.status != "pending":
            raise ValueError(
                f"Patch proposal {proposal.id!r} "
                f"cannot fail while its status "
                f"is {proposal.status!r}."
            )

        proposal.status = "failed"
        proposal.applied_at = None
        proposal.applied_by_user_id = None
        proposal.failure_reason = failure_reason

        self._session.commit()
        self._session.refresh(proposal)

        return proposal
