from __future__ import annotations

from sqlalchemy.orm import Session

from nocturnix.assistant.registry import AssistantToolRegistry
from nocturnix.assistant.repositories import AssistantTaskRepository
from nocturnix.assistant.service import AssistantTaskService


def build_assistant_service(
    session: Session,
    registry: AssistantToolRegistry,
) -> AssistantTaskService:
    repository = AssistantTaskRepository(session)
    return AssistantTaskService(repository, registry)
