from __future__ import annotations

from pydantic import BaseModel


class CustomerCreateRequest(BaseModel):
    first_name: str = ""
    last_name: str = ""
    business_name: str = ""
    email: str = ""
    mobile_phone: str = ""
    customer_type: str = "Individual"
    notes: str = ""


class CustomerResponse(BaseModel):
    id: str
    first_name: str = ""
    last_name: str = ""
    business_name: str = ""
    email: str = ""
    mobile_phone: str = ""
    customer_type: str = ""
    notes: str = ""


class CustomerDeviceCreateRequest(BaseModel):
    customer_id: str
    catalog_device_id: str = ""
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    device_type: str = ""
    notes: str = ""


class CustomerDeviceResponse(BaseModel):
    id: str
    customer_id: str
    catalog_device_id: str = ""
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    device_type: str = ""
    notes: str = ""


class RepairCreateRequest(BaseModel):
    customer_id: str
    device_id: str
    repair_status: str = "New Intake"
    problem_description: str = ""
    technician_notes: str = ""
    estimated_cost: float | None = None


class RepairUpdateRequest(BaseModel):
    repair_status: str | None = None
    technician_notes: str | None = None
    final_cost: float | None = None
    technician: str | None = None
    priority: str | None = None
    due_date: str | None = None


class RepairResponse(BaseModel):
    id: str
    customer_id: str
    device_id: str
    repair_status: str = ""
    problem_description: str = ""
    technician_notes: str = ""
    estimated_cost: float | None = None
    final_cost: float | None = None
    intake_date: str = ""
    technician: str = ""
    priority: str = "Normal"
    due_date: str = ""


class RepairQueueItemResponse(BaseModel):
    id: str
    customer_id: str
    customer_name: str = ""
    device_id: str
    catalog_device_id: str = ""
    manufacturer: str = ""
    device_model: str = ""
    repair_status: str = ""
    problem_description: str = ""
    estimated_cost: float | None = None
    final_cost: float | None = None
    intake_date: str = ""
    technician: str = ""
    priority: str = "Normal"
    due_date: str = ""


class RepairEventResponse(BaseModel):
    event_id: str
    repair_id: str
    event_type: str
    old_value: str = ""
    new_value: str = ""
    notes: str = ""
    created_at: str
    created_by: str = "Ryan Brown"


class DashboardResponse(BaseModel):
    customers: int
    devices: int
    repairs: int
    repairs_by_status: dict[str, int]


class CatalogManufacturerResponse(BaseModel):
    manufacturer_id: str
    manufacturer: str


class CatalogDeviceResponse(BaseModel):
    device_id: str | int
    device_type_id: str | int = ""
    manufacturer_id: str | int = ""
    manufacturer: str = ""
    device_family_id: str | int = ""
    device_family: str = ""
    device_model_id: str | int = ""
    device_model: str = ""
    active: bool = True


class CatalogServiceResponse(BaseModel):
    service_id: str | int
    service_name: str = ""
    device_id: str | int = ""
    manufacturer: str = ""
    device_model: str = ""
    service_type_id: str | int = ""
    service_type: str = ""
    status: str = ""


class CatalogPricingResponse(BaseModel):
    service_id: str | int = ""
    service_name: str = ""
    device_id: str | int = ""
    legacy_price: float | str | None = None
    part_cost: float | str | None = None
    labor_hours: float | str | None = None
    labor_rate: float | str | None = None
    price: float | str | None = None
    status: str = ""


class CatalogHealthResponse(BaseModel):
    database: str
    counts: dict[str, int]


class CatalogSchemaResponse(BaseModel):
    tables: dict[str, list[str]]
