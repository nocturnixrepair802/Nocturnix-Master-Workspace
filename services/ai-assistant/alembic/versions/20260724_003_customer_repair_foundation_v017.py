"""customer and repair ticket foundation for v0.1.7

Revision ID: 20260724_003
Revises: 20260724_002
Create Date: 2026-07-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_003"
down_revision: str | None = "20260724_002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("first_name", sa.String(120), nullable=False),
        sa.Column("last_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(254)),
        sa.Column("phone", sa.String(40)),
        sa.Column("company_name", sa.String(160)),
        sa.Column("preferred_contact_method", sa.String(30), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_user_id", "email", name="uq_customers_owner_email"),
    )
    for column in ["owner_user_id", "last_name", "email", "phone", "status"]:
        op.create_index(f"ix_customers_{column}", "customers", [column])

    op.create_table(
        "customer_devices",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("customer_id", sa.String(64), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("device_type", sa.String(80), nullable=False),
        sa.Column("manufacturer", sa.String(80)),
        sa.Column("model", sa.String(120)),
        sa.Column("serial_number", sa.String(160)),
        sa.Column("imei", sa.String(40)),
        sa.Column("color", sa.String(60)),
        sa.Column("storage_capacity", sa.String(60)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ["owner_user_id", "customer_id", "manufacturer", "model"]:
        op.create_index(f"ix_customer_devices_{column}", "customer_devices", [column])

    op.create_table(
        "repair_tickets",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("ticket_number", sa.String(40), nullable=False),
        sa.Column("customer_id", sa.String(64), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column(
            "customer_device_id",
            sa.String(64),
            sa.ForeignKey("customer_devices.id"),
            nullable=False,
        ),
        sa.Column("assigned_user_id", sa.String(64), sa.ForeignKey("users.id")),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("issue_description", sa.Text(), nullable=False),
        sa.Column("diagnostic_summary", sa.Text()),
        sa.Column("estimated_cost_cents", sa.Integer()),
        sa.Column("approved_cost_cents", sa.Integer()),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("intake_channel", sa.String(40), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint(
            "owner_user_id", "ticket_number", name="uq_repair_tickets_owner_number"
        ),
    )
    for column in [
        "owner_user_id",
        "ticket_number",
        "customer_id",
        "customer_device_id",
        "assigned_user_id",
        "status",
        "priority",
        "due_at",
    ]:
        op.create_index(f"ix_repair_tickets_{column}", "repair_tickets", [column])

    op.create_table(
        "repair_ticket_status_history",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column(
            "repair_ticket_id",
            sa.String(64),
            sa.ForeignKey("repair_tickets.id"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(40)),
        sa.Column("to_status", sa.String(40), nullable=False),
        sa.Column("changed_by_user_id", sa.String(64), sa.ForeignKey("users.id")),
        sa.Column("reason", sa.String(240)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ["owner_user_id", "repair_ticket_id", "to_status", "created_at"]:
        op.create_index(
            f"ix_repair_ticket_status_history_{column}",
            "repair_ticket_status_history",
            [column],
        )

    op.create_table(
        "repair_ticket_notes",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column(
            "repair_ticket_id",
            sa.String(64),
            sa.ForeignKey("repair_tickets.id"),
            nullable=False,
        ),
        sa.Column("author_user_id", sa.String(64), sa.ForeignKey("users.id")),
        sa.Column("note_type", sa.String(40), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("customer_visible", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ["owner_user_id", "repair_ticket_id", "note_type", "created_at"]:
        op.create_index(f"ix_repair_ticket_notes_{column}", "repair_ticket_notes", [column])


def downgrade() -> None:
    raise NotImplementedError(
        "Destructive schema downgrade is intentionally not implemented for v0.1.7."
    )
