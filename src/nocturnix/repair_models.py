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


class RepairTicketLineItemType(StrEnum):
    labor = "labor"
    part = "part"
    fee = "fee"
    discount = "discount"
    other = "other"


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
            self.preferred_contact_method in {ContactMethod.phone, ContactMethod.text}
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


class RepairTicketLineItemCreateRequest(StrictModel):
    line_type: RepairTicketLineItemType
    description: str = Field(min_length=1, max_length=500)
    quantity: int = Field(default=1, ge=1)
    unit_price_cents: int = Field(ge=0)
    unit_cost_cents: int | None = Field(default=None, ge=0)
    discount_cents: int = Field(default=0, ge=0)
    taxable: bool = True
    currency: str = Field(default="USD", min_length=3, max_length=3)

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("description must not be empty")
        return cleaned

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned.isalpha() or len(cleaned) != 3:
            raise ValueError("currency must be a three-letter code")
        return cleaned

    @model_validator(mode="after")
    def validate_discount(self) -> RepairTicketLineItemCreateRequest:
        gross_total = self.quantity * self.unit_price_cents
        if self.discount_cents > gross_total:
            raise ValueError("discount cannot exceed the gross line total")
        return self


class RepairTicketLineItemUpdateRequest(StrictModel):
    line_type: RepairTicketLineItemType | None = None
    description: str | None = Field(default=None, min_length=1, max_length=500)
    quantity: int | None = Field(default=None, ge=1)
    unit_price_cents: int | None = Field(default=None, ge=0)
    unit_cost_cents: int | None = Field(default=None, ge=0)
    discount_cents: int | None = Field(default=None, ge=0)
    taxable: bool | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        if not cleaned:
            raise ValueError("description must not be empty")

        return cleaned

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().upper()
        if not cleaned.isalpha() or len(cleaned) != 3:
            raise ValueError("currency must be a three-letter code")
        return cleaned


class RepairTicketLineItemResponse(RepairResponseModel):
    id: str
    owner_user_id: str
    repair_ticket_id: str
    line_number: int
    line_type: RepairTicketLineItemType
    description: str
    quantity: int
    unit_price_cents: int
    unit_cost_cents: int | None
    discount_cents: int
    line_total_cents: int
    taxable: bool
    currency: str
    created_at: datetime
    updated_at: datetime


class RepairTicketFinancialSummaryResponse(StrictModel):
    repair_ticket_id: str
    currency: str
    line_item_count: int = Field(ge=0)
    gross_subtotal_cents: int = Field(ge=0)
    discount_total_cents: int = Field(ge=0)
    net_subtotal_cents: int = Field(ge=0)
    taxable_subtotal_cents: int = Field(ge=0)
    non_taxable_subtotal_cents: int = Field(ge=0)


class RepairTaxPolicyCreateRequest(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    jurisdiction: str | None = Field(default=None, max_length=120)
    tax_rate_basis_points: int = Field(ge=0, le=10000)
    is_default: bool = False
    effective_at: datetime

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned

    @field_validator("jurisdiction")
    @classmethod
    def clean_jurisdiction(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class RepairTaxPolicyUpdateRequest(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    jurisdiction: str | None = Field(default=None, max_length=120)
    tax_rate_basis_points: int | None = Field(default=None, ge=0, le=10000)
    is_default: bool | None = None
    effective_at: datetime | None = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned

    @field_validator("jurisdiction")
    @classmethod
    def clean_jurisdiction(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class RepairTaxPolicyResponse(RepairResponseModel):
    id: str
    owner_user_id: str
    name: str
    jurisdiction: str | None
    tax_rate_basis_points: int
    is_default: bool
    effective_at: datetime
    created_at: datetime
    updated_at: datetime


class RepairTaxPolicyListResponse(StrictModel):
    items: list[RepairTaxPolicyResponse]
    total: int = Field(ge=0)


class RepairTicketLineItemListResponse(StrictModel):
    items: list[RepairTicketLineItemResponse]
    total: int = Field(ge=0)


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


class RepairDashboardSummary(StrictModel):
    total_customers: int = Field(ge=0)
    total_devices: int = Field(ge=0)
    total_tickets: int = Field(ge=0)
    open_tickets: int = Field(ge=0)
    urgent_tickets: int = Field(ge=0)
    awaiting_approval: int = Field(ge=0)
    ready_for_pickup: int = Field(ge=0)
    completed_tickets: int = Field(ge=0)


class RepairDashboardQueueItem(StrictModel):
    id: str
    ticket_number: str
    status: RepairTicketStatus
    priority: RepairPriority
    issue_description: str
    customer_name: str
    device_label: str
    estimated_cost_cents: int | None
    approved_cost_cents: int | None
    currency: str
    due_at: datetime | None
    updated_at: datetime


class RepairDashboardResponse(StrictModel):
    summary: RepairDashboardSummary
    tickets_by_status: dict[RepairTicketStatus, int]
    tickets_by_priority: dict[RepairPriority, int]
    recent_queue: list[RepairDashboardQueueItem]
    development_only: bool = True
