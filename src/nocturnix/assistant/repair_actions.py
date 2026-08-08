from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from nocturnix.assistant.repair_action_models import (
    AssistantRepairActionApplyResponse,
    AssistantRepairActionProposal,
    AssistantRepairActionStatus,
    AssistantRepairActionType,
    AssistantRepairAddNoteProposalRequest,
)
from nocturnix.persistence.models import (
    AssistantRepairActionProposalRow,
)
from nocturnix.repair_models import (
    RepairNoteType,
    RepairTicketNoteCreateRequest,
)
from nocturnix.repair_services import (
    RepairDomainError,
    RepairService,
)


class AssistantRepairActionError(RuntimeError):
    """Raised when a repair action proposal cannot be processed safely."""


class AssistantRepairActionNotFoundError(AssistantRepairActionError):
    """Raised when a repair action proposal does not exist for the owner."""


class AssistantRepairActionStateError(AssistantRepairActionError):
    """Raised when a proposal is used from an invalid state."""


class AssistantRepairActionConfirmationError(AssistantRepairActionError):
    """Raised when execution is attempted without explicit confirmation."""


class AssistantRepairActionRepository(Protocol):
    def create(
        self,
        proposal: AssistantRepairActionProposal,
    ) -> AssistantRepairActionProposal: ...

    def get(
        self,
        proposal_id: str,
        *,
        owner_user_id: str,
    ) -> AssistantRepairActionProposal | None: ...

    def mark_applied(
        self,
        proposal_id: str,
        *,
        owner_user_id: str,
        applied_by_user_id: str,
        applied_at: datetime,
    ) -> AssistantRepairActionProposal: ...

    def mark_failed(
        self,
        proposal_id: str,
        *,
        owner_user_id: str,
        failure_reason: str,
    ) -> AssistantRepairActionProposal: ...


class InMemoryAssistantRepairActionRepository:
    """
    Temporary repository implementation used until durable SQL
    persistence is wired in the next integration step.

    Do not use this as the final production persistence layer.
    """

    def __init__(self) -> None:
        self._proposals: dict[
            str,
            AssistantRepairActionProposal,
        ] = {}

    def create(
        self,
        proposal: AssistantRepairActionProposal,
    ) -> AssistantRepairActionProposal:
        self._proposals[proposal.id] = proposal

        return proposal

    def get(
        self,
        proposal_id: str,
        *,
        owner_user_id: str,
    ) -> AssistantRepairActionProposal | None:
        proposal = self._proposals.get(proposal_id)

        if proposal is None:
            return None

        if proposal.owner_user_id != owner_user_id:
            return None

        return proposal

    def mark_applied(
        self,
        proposal_id: str,
        *,
        owner_user_id: str,
        applied_by_user_id: str,
        applied_at: datetime,
    ) -> AssistantRepairActionProposal:
        proposal = self.get(
            proposal_id,
            owner_user_id=owner_user_id,
        )

        if proposal is None:
            raise AssistantRepairActionNotFoundError("Repair action proposal not found.")

        updated = proposal.model_copy(
            update={
                "status": (AssistantRepairActionStatus.applied),
                "applied_at": applied_at,
                "applied_by_user_id": (applied_by_user_id),
                "failure_reason": None,
            }
        )

        self._proposals[proposal_id] = updated

        return updated

    def mark_failed(
        self,
        proposal_id: str,
        *,
        owner_user_id: str,
        failure_reason: str,
    ) -> AssistantRepairActionProposal:
        proposal = self.get(
            proposal_id,
            owner_user_id=owner_user_id,
        )

        if proposal is None:
            raise AssistantRepairActionNotFoundError("Repair action proposal not found.")

        updated = proposal.model_copy(
            update={
                "status": (AssistantRepairActionStatus.failed),
                "applied_at": None,
                "applied_by_user_id": None,
                "failure_reason": (failure_reason[:2000]),
            }
        )

        self._proposals[proposal_id] = updated

        return updated


class SqlAssistantRepairActionRepository:
    """Persist Assistant repair action proposals using SQLAlchemy."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def create(
        self,
        proposal: AssistantRepairActionProposal,
    ) -> AssistantRepairActionProposal:
        row = AssistantRepairActionProposalRow(
            id=proposal.id,
            owner_user_id=proposal.owner_user_id,
            created_by_user_id=(proposal.created_by_user_id),
            action_type=(proposal.action_type.value),
            status=proposal.status.value,
            ticket_id=proposal.ticket_id,
            note_type=proposal.note_type.value,
            body=proposal.body,
            customer_visible=(proposal.customer_visible),
            created_at=proposal.created_at,
            applied_at=proposal.applied_at,
            applied_by_user_id=(proposal.applied_by_user_id),
            failure_reason=(proposal.failure_reason),
        )

        try:
            self._session.add(row)
            self._session.commit()
            self._session.refresh(row)
        except Exception:
            self._session.rollback()
            raise

        return self._to_proposal(row)

    def get(
        self,
        proposal_id: str,
        *,
        owner_user_id: str,
    ) -> AssistantRepairActionProposal | None:
        statement = select(AssistantRepairActionProposalRow).where(
            AssistantRepairActionProposalRow.id == proposal_id,
            AssistantRepairActionProposalRow.owner_user_id == owner_user_id,
        )

        row = self._session.scalar(statement)

        if row is None:
            return None

        return self._to_proposal(row)

    def mark_applied(
        self,
        proposal_id: str,
        *,
        owner_user_id: str,
        applied_by_user_id: str,
        applied_at: datetime,
    ) -> AssistantRepairActionProposal:
        row = self._get_row(
            proposal_id,
            owner_user_id=owner_user_id,
        )

        if row.status != (AssistantRepairActionStatus.pending.value):
            raise AssistantRepairActionStateError(
                f"Repair action proposal "
                f"{row.id!r} cannot be "
                f"applied while its status "
                f"is {row.status!r}."
            )

        row.status = AssistantRepairActionStatus.applied.value

        row.applied_at = applied_at
        row.applied_by_user_id = applied_by_user_id
        row.failure_reason = None

        try:
            self._session.commit()
            self._session.refresh(row)
        except Exception:
            self._session.rollback()
            raise

        return self._to_proposal(row)

    def mark_failed(
        self,
        proposal_id: str,
        *,
        owner_user_id: str,
        failure_reason: str,
    ) -> AssistantRepairActionProposal:
        row = self._get_row(
            proposal_id,
            owner_user_id=owner_user_id,
        )

        if row.status != (AssistantRepairActionStatus.pending.value):
            raise AssistantRepairActionStateError(
                f"Repair action proposal {row.id!r} cannot fail while its status is {row.status!r}."
            )

        row.status = AssistantRepairActionStatus.failed.value

        row.applied_at = None
        row.applied_by_user_id = None

        row.failure_reason = failure_reason[:2000]

        try:
            self._session.commit()
            self._session.refresh(row)
        except Exception:
            self._session.rollback()
            raise

        return self._to_proposal(row)

    def _get_row(
        self,
        proposal_id: str,
        *,
        owner_user_id: str,
    ) -> AssistantRepairActionProposalRow:
        statement = select(AssistantRepairActionProposalRow).where(
            AssistantRepairActionProposalRow.id == proposal_id,
            AssistantRepairActionProposalRow.owner_user_id == owner_user_id,
        )

        row = self._session.scalar(statement)

        if row is None:
            raise AssistantRepairActionNotFoundError("Repair action proposal not found.")

        return row

    @staticmethod
    def _to_proposal(
        row: AssistantRepairActionProposalRow,
    ) -> AssistantRepairActionProposal:
        return AssistantRepairActionProposal(
            id=row.id,
            owner_user_id=row.owner_user_id,
            created_by_user_id=(row.created_by_user_id),
            action_type=(AssistantRepairActionType(row.action_type)),
            status=(AssistantRepairActionStatus(row.status)),
            ticket_id=row.ticket_id,
            note_type=RepairNoteType(row.note_type),
            body=row.body,
            customer_visible=(row.customer_visible),
            created_at=row.created_at,
            applied_at=row.applied_at,
            applied_by_user_id=(row.applied_by_user_id),
            failure_reason=(row.failure_reason),
        )


class AssistantRepairActionService:
    """
    Create and apply explicitly confirmed repair-domain action proposals.

    The service does not write repair-domain data while creating a
    proposal. All repair writes go through RepairService and only happen
    during apply().
    """

    def __init__(
        self,
        repair_service: RepairService,
        repository: AssistantRepairActionRepository,
    ) -> None:
        self._repair_service = repair_service
        self._repository = repository

    def propose_add_ticket_note(
        self,
        *,
        owner_user_id: str,
        created_by_user_id: str,
        request: AssistantRepairAddNoteProposalRequest,
    ) -> AssistantRepairActionProposal:
        # Validate ownership/existence through the Repair domain.
        # This is intentionally read-only.
        self._repair_service.get_ticket(
            owner_user_id,
            request.ticket_id,
        )

        # Reuse the Repair domain request model so proposal validation
        # stays consistent with the actual write operation.
        validated_note = RepairTicketNoteCreateRequest(
            note_type=request.note_type,
            body=request.body,
            customer_visible=(request.customer_visible),
        )

        proposal = AssistantRepairActionProposal(
            id=(f"repair_action_{uuid4().hex[:20]}"),
            owner_user_id=owner_user_id,
            created_by_user_id=(created_by_user_id),
            action_type=(AssistantRepairActionType.add_ticket_note),
            status=(AssistantRepairActionStatus.pending),
            ticket_id=request.ticket_id,
            note_type=validated_note.note_type,
            body=validated_note.body,
            customer_visible=(validated_note.customer_visible),
            created_at=datetime.now(UTC),
            applied_at=None,
            applied_by_user_id=None,
            failure_reason=None,
        )

        return self._repository.create(proposal)

    def get_proposal(
        self,
        proposal_id: str,
        *,
        owner_user_id: str,
    ) -> AssistantRepairActionProposal:
        proposal = self._repository.get(
            proposal_id,
            owner_user_id=owner_user_id,
        )

        if proposal is None:
            raise AssistantRepairActionNotFoundError("Repair action proposal not found.")

        return proposal

    def apply(
        self,
        proposal_id: str,
        *,
        owner_user_id: str,
        applied_by_user_id: str,
        confirm: bool,
    ) -> AssistantRepairActionApplyResponse:
        if not confirm:
            raise AssistantRepairActionConfirmationError(
                "Repair action application requires explicit confirmation."
            )

        proposal = self.get_proposal(
            proposal_id,
            owner_user_id=owner_user_id,
        )

        if proposal.status != AssistantRepairActionStatus.pending:
            raise AssistantRepairActionStateError(
                f"Repair action proposal "
                f"{proposal.id!r} cannot be "
                f"applied while its status is "
                f"{proposal.status.value!r}."
            )

        if proposal.action_type != AssistantRepairActionType.add_ticket_note:
            raise AssistantRepairActionError("Unsupported repair action type.")

        note_request = RepairTicketNoteCreateRequest(
            note_type=proposal.note_type,
            body=proposal.body,
            customer_visible=(proposal.customer_visible),
        )

        try:
            note = self._repair_service.create_ticket_note(
                owner_user_id,
                proposal.ticket_id,
                applied_by_user_id,
                note_request,
            )

        except RepairDomainError as exc:
            self._mark_failed(
                proposal,
                owner_user_id=owner_user_id,
                reason=str(exc),
            )

            raise AssistantRepairActionError(str(exc)) from exc

        except Exception as exc:
            self._mark_failed(
                proposal,
                owner_user_id=owner_user_id,
                reason=str(exc),
            )

            raise

        applied_at = datetime.now(UTC)

        updated = self._repository.mark_applied(
            proposal.id,
            owner_user_id=owner_user_id,
            applied_by_user_id=(applied_by_user_id),
            applied_at=applied_at,
        )

        if updated.applied_at is None:
            raise AssistantRepairActionError(
                "Repair action proposal was applied without an applied_at timestamp."
            )

        if updated.applied_by_user_id is None:
            raise AssistantRepairActionError(
                "Repair action proposal was applied without an applying user."
            )

        return AssistantRepairActionApplyResponse(
            proposal_id=updated.id,
            action_type=updated.action_type,
            status=updated.status,
            ticket_id=updated.ticket_id,
            applied_at=updated.applied_at,
            applied_by_user_id=(updated.applied_by_user_id),
            created_note_id=note.id,
            failure_reason=(updated.failure_reason),
        )

    def _mark_failed(
        self,
        proposal: AssistantRepairActionProposal,
        *,
        owner_user_id: str,
        reason: str,
    ) -> None:
        try:
            self._repository.mark_failed(
                proposal.id,
                owner_user_id=owner_user_id,
                failure_reason=reason,
            )
        except (
            AssistantRepairActionError,
            ValueError,
        ):
            pass
