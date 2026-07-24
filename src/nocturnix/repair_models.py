from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator, model_validator

from nocturnix.models import StrictModel


class CustomerStatus(StrEnum):
    active = "active"
    inactive = "inactive"
    blocked = "blocked"


class ContactMethod(StrEnum):
    phone = "phone"
    email = "email"
    text = "text"
    none = "none"


class RepairTicketStatus(StrEnum):
    received = "received"
    diagnosing = "diagnosing"
    awaiting_approval = "awaiting_approval"
    approved = "approved"
    parts_ordered = "parts_ordered"
    in_repair = "in_repair"
    quality_check = "quality_check"
    ready_for_pickup = "ready_for_pickup"
    completed = "completed"
    cancelled = "cancelled"


class RepairPriority(StrEnum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class IntakeChannel(StrEnum):
    walk_in = "walk_in"
    phone = "phone"
    web = "web"
    email = "email"
    internal = "internal"


class RepairNoteType(StrEnum):
    internal = "internal"
    diagnostic = "diagnostic"
    customer_update = "customer_update"
    parts = "parts"
    quality_check = "quality_check"


class RepairResponseModel(StrictModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class CustomerCreateRequest(StrictModel):
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    company_name: str | None = Field(default=None, max_length=160)
    preferred_contact_method: ContactMethod = ContactMethod.phone
    notes: str | None = Field(default=None, max_length=2000)
    status: CustomerStatus = CustomerStatus.active

    @field_validator("first_name", "last_name", "company_name", "notes")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        cleaned = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", cleaned):
            raise ValueError("email must be a valid email address")
        return cleaned

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        cleaned = value.strip()
        digits = re.sub(r"\D", "", cleaned)
        if len(digits) < 7 or len(digits) > 15:
            raise ValueError("phone must contain between 7 and 15 digits")
        return cleaned

    @model_validator(mode="after")
    def validate_contact_method(self) -> CustomerCreateRequest:
        if self.preferred_contact_method == ContactMethod.email and not self.email:
            raise ValueError("email is required when preferred_contact_method is email")
        if (
<<<<<<< HEAD
            self.preferred_contact_method
            in {ContactMethod.phone, ContactMethod.text}
=======
            self.preferred_contact_method in {ContactMethod.phone, ContactMethod.text}
>>>>>>> 437e3ca9aa84129803ba3df94111f204e4c31533
            and not self.phone
        ):
            raise ValueError("phone is required for phone or text contact")
        return self


class CustomerUpdateRequest(StrictModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    company_name: str | None = Field(default=None, max_length=160)
    preferred_contact_method: ContactMethod | None = None
    notes: str | None = Field(default=None, max_length=2000)
    status: CustomerStatus | None = None

    @field_validator("first_name", "last_name", "company_name", "notes")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        cleaned = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", cleaned):
            raise ValueError("email must be a valid email address")
        return cleaned

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        cleaned = value.strip()
        digits = re.sub(r"\D", "", cleaned)
        if len(digits) < 7 or len(digits) > 15:
            raise ValueError("phone must contain between 7 and 15 digits")
        return cleaned


class CustomerResponse(RepairResponseModel):
    id: str
    owner_user_id: str
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    company_name: str | None
    preferred_contact_method: ContactMethod
    notes: str | None
    status: CustomerStatus
    created_at: datetime
    updated_at: datetime


class CustomerDeviceCreateRequest(StrictModel):
    customer_id: str = Field(min_length=1, max_length=64)
    device_type: str = Field(min_length=1, max_length=80)
    manufacturer: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=120)
    serial_number: str | None = Field(default=None, max_length=160)
    imei: str | None = Field(default=None, max_length=40)
    color: str | None = Field(default=None, max_length=60)
    storage_capacity: str | None = Field(default=None, max_length=60)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator(
        "customer_id",
        "device_type",
        "manufacturer",
        "model",
        "serial_number",
        "imei",
        "color",
        "storage_capacity",
        "notes",
    )
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class CustomerDeviceUpdateRequest(StrictModel):
    device_type: str | None = Field(default=None, min_length=1, max_length=80)
    manufacturer: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=120)
    serial_number: str | None = Field(default=None, max_length=160)
    imei: str | None = Field(default=None, max_length=40)
    color: str | None = Field(default=None, max_length=60)
    storage_capacity: str | None = Field(default=None, max_length=60)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator(
        "device_type",
        "manufacturer",
        "model",
        "serial_number",
        "imei",
        "color",
        "storage_capacity",
        "notes",
    )
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class CustomerDeviceResponse(RepairResponseModel):
    id: str
    owner_user_id: str
    customer_id: str
    device_type: str
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    imei: str | None
    color: str | None
    storage_capacity: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class RepairTicketCreateRequest(StrictModel):
    customer_id: str = Field(min_length=1, max_length=64)
    customer_device_id: str = Field(min_length=1, max_length=64)
    assigned_user_id: str | None = Field(default=None, max_length=64)
    priority: RepairPriority = RepairPriority.normal
    issue_description: str = Field(min_length=1, max_length=5000)
    diagnostic_summary: str | None = Field(default=None, max_length=5000)
    estimated_cost_cents: int | None = Field(default=None, ge=0)
    approved_cost_cents: int | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    intake_channel: IntakeChannel = IntakeChannel.walk_in
    due_at: datetime | None = None

    @field_validator("issue_description", "diagnostic_summary")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned.isalpha() or len(cleaned) != 3:
            raise ValueError("currency must be a three-letter code")
        return cleaned

    @model_validator(mode="after")
    def validate_costs(self) -> RepairTicketCreateRequest:
        if (
            self.estimated_cost_cents is not None
            and self.approved_cost_cents is not None
            and self.approved_cost_cents > self.estimated_cost_cents
        ):
            raise ValueError("approved cost cannot exceed estimated cost")
        return self


class RepairTicketUpdateRequest(StrictModel):
    assigned_user_id: str | None = Field(default=None, max_length=64)
    priority: RepairPriority | None = None
    issue_description: str | None = Field(default=None, min_length=1, max_length=5000)
    diagnostic_summary: str | None = Field(default=None, max_length=5000)
    estimated_cost_cents: int | None = Field(default=None, ge=0)
    approved_cost_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    due_at: datetime | None = None

    @field_validator("issue_description", "diagnostic_summary")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().upper()
        if not cleaned.isalpha() or len(cleaned) != 3:
            raise ValueError("currency must be a three-letter code")
        return cleaned

    @model_validator(mode="after")
    def validate_costs(self) -> RepairTicketUpdateRequest:
        if (
            self.estimated_cost_cents is not None
            and self.approved_cost_cents is not None
            and self.approved_cost_cents > self.estimated_cost_cents
        ):
            raise ValueError("approved cost cannot exceed estimated cost")
        return self


class RepairTicketStatusChangeRequest(StrictModel):
    status: RepairTicketStatus
    reason: str | None = Field(default=None, max_length=240)

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class RepairTicketResponse(RepairResponseModel):
    id: str
    owner_user_id: str
    ticket_number: str
    customer_id: str
    customer_device_id: str
    assigned_user_id: str | None
    status: RepairTicketStatus
    priority: RepairPriority
    issue_description: str
    diagnostic_summary: str | None
    estimated_cost_cents: int | None
    approved_cost_cents: int | None
    currency: str
    intake_channel: IntakeChannel
    due_at: datetime | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    cancelled_at: datetime | None


class RepairTicketStatusHistoryResponse(RepairResponseModel):
    id: str
    owner_user_id: str
    repair_ticket_id: str
    from_status: RepairTicketStatus | None
    to_status: RepairTicketStatus
    changed_by_user_id: str | None
    reason: str | None
    created_at: datetime


class RepairTicketNoteCreateRequest(StrictModel):
    note_type: RepairNoteType = RepairNoteType.internal
    body: str = Field(min_length=1, max_length=5000)
    customer_visible: bool = False

    @field_validator("body")
    @classmethod
    def clean_body(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("body must not be empty")
        return cleaned

    @model_validator(mode="after")
    def validate_visibility(self) -> RepairTicketNoteCreateRequest:
        if self.customer_visible and self.note_type == RepairNoteType.internal:
            raise ValueError("internal notes cannot be customer visible")
        return self


class RepairTicketNoteUpdateRequest(StrictModel):
    note_type: RepairNoteType | None = None
    body: str | None = Field(default=None, min_length=1, max_length=5000)
    customer_visible: bool | None = None

    @field_validator("body")
    @classmethod
    def clean_body(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def validate_visibility(self) -> RepairTicketNoteUpdateRequest:
        if self.customer_visible is True and self.note_type == RepairNoteType.internal:
            raise ValueError("internal notes cannot be customer visible")
        return self


class RepairTicketNoteResponse(RepairResponseModel):
    id: str
    owner_user_id: str
    repair_ticket_id: str
    author_user_id: str | None
    note_type: RepairNoteType
    body: str
    customer_visible: bool
    created_at: datetime
    updated_at: datetime


class CustomerListResponse(StrictModel):
    items: list[CustomerResponse]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)


class CustomerDeviceListResponse(StrictModel):
    items: list[CustomerDeviceResponse]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)


class RepairTicketListResponse(StrictModel):
    items: list[RepairTicketResponse]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
