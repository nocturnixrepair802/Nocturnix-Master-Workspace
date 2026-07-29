from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from nocturnix.db import Base


class CustomerRow(Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("owner_user_id", "email", name="uq_customers_owner_email"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), index=True)
    phone: Mapped[str | None] = mapped_column(String(40), index=True)
    company_name: Mapped[str | None] = mapped_column(String(160))
    preferred_contact_method: Mapped[str] = mapped_column(String(30), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    devices: Mapped[list[CustomerDeviceRow]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    repair_tickets: Mapped[list[RepairTicketRow]] = relationship(back_populates="customer")


class CustomerDeviceRow(Base):
    __tablename__ = "customer_devices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    device_type: Mapped[str] = mapped_column(String(80), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(80), index=True)
    model: Mapped[str | None] = mapped_column(String(120), index=True)
    serial_number: Mapped[str | None] = mapped_column(String(160))
    imei: Mapped[str | None] = mapped_column(String(40))
    color: Mapped[str | None] = mapped_column(String(60))
    storage_capacity: Mapped[str | None] = mapped_column(String(60))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    customer: Mapped[CustomerRow] = relationship(back_populates="devices")
    repair_tickets: Mapped[list[RepairTicketRow]] = relationship(back_populates="device")


class RepairTicketRow(Base):
    __tablename__ = "repair_tickets"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "ticket_number", name="uq_repair_tickets_owner_number"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    ticket_number: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    customer_device_id: Mapped[str] = mapped_column(
        ForeignKey("customer_devices.id"), index=True, nullable=False
    )
    assigned_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    diagnostic_summary: Mapped[str | None] = mapped_column(Text)
    estimated_cost_cents: Mapped[int | None] = mapped_column(Integer)
    approved_cost_cents: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    intake_channel: Mapped[str] = mapped_column(String(40), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    customer: Mapped[CustomerRow] = relationship(back_populates="repair_tickets")
    device: Mapped[CustomerDeviceRow] = relationship(back_populates="repair_tickets")
    status_history: Mapped[list[RepairTicketStatusHistoryRow]] = relationship(
        back_populates="repair_ticket", cascade="all, delete-orphan"
    )
    notes: Mapped[list[RepairTicketNoteRow]] = relationship(
        back_populates="repair_ticket", cascade="all, delete-orphan"
    )
    line_items: Mapped[list[RepairTicketLineItemRow]] = relationship(
        back_populates="repair_ticket",
        cascade="all, delete-orphan",
        order_by="RepairTicketLineItemRow.line_number",
    )


class RepairTicketLineItemRow(Base):
    __tablename__ = "repair_ticket_line_items"
    __table_args__ = (
        UniqueConstraint(
            "repair_ticket_id",
            "line_number",
            name="uq_repair_ticket_line_items_ticket_line",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(
        String(120),
        index=True,
        nullable=False,
    )
    repair_ticket_id: Mapped[str] = mapped_column(
        ForeignKey("repair_tickets.id"),
        index=True,
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    line_type: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost_cents: Mapped[int | None] = mapped_column(Integer)
    discount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    taxable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    repair_ticket: Mapped[RepairTicketRow] = relationship(back_populates="line_items")


class RepairTicketStatusHistoryRow(Base):
    __tablename__ = "repair_ticket_status_history"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    repair_ticket_id: Mapped[str] = mapped_column(
        ForeignKey("repair_tickets.id"), index=True, nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(40))
    to_status: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    changed_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str | None] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )

    repair_ticket: Mapped[RepairTicketRow] = relationship(back_populates="status_history")


class RepairTicketNoteRow(Base):
    __tablename__ = "repair_ticket_notes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    repair_ticket_id: Mapped[str] = mapped_column(
        ForeignKey("repair_tickets.id"), index=True, nullable=False
    )
    author_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    note_type: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    customer_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    repair_ticket: Mapped[RepairTicketRow] = relationship(back_populates="notes")


class RepairConfirmationRow(Base):
    __tablename__ = "repair_confirmations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    previous_response_id: Mapped[str] = mapped_column(String(200), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(120), nullable=False)
    arguments_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    action_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
