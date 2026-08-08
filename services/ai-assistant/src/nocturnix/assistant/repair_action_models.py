from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from nocturnix.repair_models import RepairNoteType


class AssistantRepairActionType(StrEnum):
    add_ticket_note = "add_ticket_note"


class AssistantRepairActionStatus(StrEnum):
    pending = "pending"
    applied = "applied"
    failed = "failed"


class AssistantRepairAddNoteProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticket_id: str = Field(
        min_length=1,
        max_length=64,
    )
    note_type: RepairNoteType = RepairNoteType.internal
    body: str = Field(
        min_length=1,
        max_length=5000,
    )
    customer_visible: bool = False

    @field_validator("ticket_id")
    @classmethod
    def normalize_ticket_id(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError("ticket_id must not be blank")

        return normalized

    @field_validator("body")
    @classmethod
    def normalize_body(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError("body must not be blank")

        return normalized

    @model_validator(mode="after")
    def validate_visibility(
        self,
    ) -> AssistantRepairAddNoteProposalRequest:
        if self.note_type == RepairNoteType.internal and self.customer_visible:
            raise ValueError("internal notes cannot be customer visible")

        return self


class AssistantRepairActionApplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: bool = False


class AssistantRepairActionProposal(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: str
    owner_user_id: str
    created_by_user_id: str

    action_type: AssistantRepairActionType
    status: AssistantRepairActionStatus

    ticket_id: str

    note_type: RepairNoteType
    body: str
    customer_visible: bool

    created_at: datetime
    applied_at: datetime | None = None
    applied_by_user_id: str | None = None
    failure_reason: str | None = None


class AssistantRepairActionProposalResponse(BaseModel):
    proposal_id: str
    action_type: AssistantRepairActionType
    status: AssistantRepairActionStatus
    ticket_id: str
    note_type: RepairNoteType
    body: str
    customer_visible: bool
    created_at: datetime
    applied_at: datetime | None
    applied_by_user_id: str | None
    failure_reason: str | None

    @classmethod
    def from_proposal(
        cls,
        proposal: AssistantRepairActionProposal,
    ) -> AssistantRepairActionProposalResponse:
        return cls(
            proposal_id=proposal.id,
            action_type=proposal.action_type,
            status=proposal.status,
            ticket_id=proposal.ticket_id,
            note_type=proposal.note_type,
            body=proposal.body,
            customer_visible=proposal.customer_visible,
            created_at=proposal.created_at,
            applied_at=proposal.applied_at,
            applied_by_user_id=(proposal.applied_by_user_id),
            failure_reason=proposal.failure_reason,
        )


class AssistantRepairActionApplyResponse(BaseModel):
    proposal_id: str
    action_type: AssistantRepairActionType
    status: AssistantRepairActionStatus
    ticket_id: str
    applied_at: datetime
    applied_by_user_id: str
    created_note_id: str
    failure_reason: str | None = None
