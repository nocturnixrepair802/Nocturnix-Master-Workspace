from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from nocturnix.assistant.openai_provider import (
    CodingAssistantProvider,
    CodingProviderError,
)
from nocturnix.assistant.repositories import AssistantTaskRepository
from nocturnix.assistant.repository_access import RepositoryAccessService
from nocturnix.assistant.service import AssistantTaskService
from nocturnix.assistant.web_models import (
    AssistantChatRequest,
    AssistantChatResponse,
)
from nocturnix.persistence.models import ConversationRow


class CodingAssistantService:
    def __init__(
        self,
        session: Session,
        provider: CodingAssistantProvider,
        conversation_retention_days: int = 30,
        repository: RepositoryAccessService | None = None,
    ) -> None:
        self._session = session
        self._provider = provider
        self._conversation_retention_days = conversation_retention_days
        self._repository = repository
        self.tasks = AssistantTaskService(AssistantTaskRepository(session))

    def chat(
        self,
        owner_user_id: str,
        request: AssistantChatRequest,
    ) -> AssistantChatResponse:
        conversation_id = self._conversation(
            owner_user_id,
            request.conversation_id,
        )

        repository_context = request.project_context
        attached_files: list[str] = []

        if request.selected_files:
            if self._repository is None:
                raise ValueError("Repository access is not configured.")

            loaded_context, attached_files = self._repository.load_context(request.selected_files)

            repository_context = "\n\n".join(
                part
                for part in [
                    request.project_context,
                    loaded_context,
                ]
                if part
            )

        task = self.tasks.create_task(
            owner_user_id=owner_user_id,
            conversation_id=conversation_id,
            task_type=request.task_type,
            title=request.message[:120],
            instructions=request.message,
            input_data={
                "has_project_context": bool(request.project_context),
                "selected_files": attached_files,
            },
        )

        self.tasks.start_task(
            task.id,
            owner_user_id=owner_user_id,
        )

        try:
            answer = self._provider.answer(
                request.message,
                repository_context,
            )
        except CodingProviderError:
            self.tasks.fail_task(
                task.id,
                error_message=("AI provider request failed safely."),
                owner_user_id=owner_user_id,
            )
            raise

        result = self.tasks.add_result(
            task_id=task.id,
            result_type="text",
            title="Assistant response",
            summary=answer[:240],
            content={"text": answer},
            media_type="text/markdown",
        )

        completed = self.tasks.complete_task(
            task.id,
            result_summary=("Coding assistance response generated."),
            owner_user_id=owner_user_id,
        )

        if completed.completed_at is None:
            raise RuntimeError("completed task has no completion timestamp")

        return AssistantChatResponse(
            task_id=completed.id,
            conversation_id=conversation_id,
            status=completed.status,
            answer=answer,
            result_id=result.id,
            model=self._provider.model,
            completed_at=completed.completed_at,
        )

    def _conversation(
        self,
        owner_user_id: str,
        requested_id: str | None,
    ) -> str:
        conversation_id = requested_id or str(uuid4())

        existing = self._session.scalar(
            select(ConversationRow).where(ConversationRow.id == conversation_id)
        )

        if existing is not None and existing.owner_user_id != owner_user_id:
            raise ConversationAccessError("Conversation not found.")

        if existing is None:
            now = datetime.now(UTC)

            self._session.add(
                ConversationRow(
                    id=conversation_id,
                    owner_user_id=owner_user_id,
                    mode="coding_assistance",
                    status="active",
                    escalation_state="none",
                    created_at=now,
                    updated_at=now,
                    retention_expires_at=(now + timedelta(days=self._conversation_retention_days)),
                )
            )

            self._session.commit()

        return conversation_id


class ConversationAccessError(RuntimeError):
    pass
