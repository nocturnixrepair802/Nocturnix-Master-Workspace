from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CustomerCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(default="", max_length=120)
    last_name: str = Field(default="", max_length=120)
    business_name: str = Field(default="", max_length=200)
    email: str = Field(default="", max_length=254)
    mobile_phone: str = Field(default="", max_length=50)
    customer_type: str = Field(default="Individual", max_length=80)
    notes: str = Field(default="", max_length=5000)

    @field_validator(
        "first_name",
        "last_name",
        "business_name",
        "email",
        "mobile_phone",
        "customer_type",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_text(
        cls,
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return str(value).strip()


class CustomerResponse(BaseModel):
    id: int | str
    first_name: str
    last_name: str
    business_name: str
    email: str
    mobile_phone: str
    customer_type: str
    notes: str = ""


class CustomerDeviceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: int | str
    manufacturer: str = Field(min_length=1, max_length=120)
    model: str = Field(min_length=1, max_length=160)
    serial_number: str = Field(default="", max_length=160)
    device_type: str = Field(default="Mobile Device", max_length=120)
    notes: str = Field(default="", max_length=5000)

    @field_validator(
        "manufacturer",
        "model",
        "serial_number",
        "device_type",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_device_text(
        cls,
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return str(value).strip()


class CustomerDeviceResponse(BaseModel):
    id: int | str
    customer_id: int | str
    manufacturer: str
    model: str
    serial_number: str
    device_type: str
    notes: str = ""


class RepairCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: int | str
    device_id: int | str
    repair_status: str = Field(
        default="New Intake",
        max_length=100,
    )
    problem_description: str = Field(
        min_length=1,
        max_length=5000,
    )
    technician_notes: str = Field(
        default="",
        max_length=5000,
    )
    estimated_cost: float | None = Field(
        default=None,
        ge=0,
    )

    @field_validator(
        "repair_status",
        "problem_description",
        "technician_notes",
        mode="before",
    )
    @classmethod
    def normalize_repair_text(
        cls,
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return str(value).strip()


class RepairResponse(BaseModel):
    id: int | str
    customer_id: int | str
    device_id: int | str
    repair_status: str
    problem_description: str
    technician_notes: str
    estimated_cost: float | None


class DashboardResponse(BaseModel):
    customers: int
    devices: int
    repairs: int
    repairs_by_status: dict[str, int]
