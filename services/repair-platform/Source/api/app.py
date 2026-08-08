from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.operations import RepairApiOperations
from api.schemas import (
    CustomerCreateRequest,
    CustomerDeviceCreateRequest,
    CustomerDeviceResponse,
    CustomerResponse,
    DashboardResponse,
    RepairCreateRequest,
    RepairResponse,
)
from api.serialization import (
    record_from_series,
    records_from_dataframe,
)
from app import Application

_application: Application | None = None
_operations: RepairApiOperations | None = None


def get_application() -> Application:
    if _application is None:
        raise RuntimeError("Repair Platform API has not initialized.")

    return _application


def get_operations() -> RepairApiOperations:
    if _operations is None:
        raise RuntimeError("Repair Platform API operations have not initialized.")

    return _operations


def customer_response(
    record: dict[str, Any],
) -> CustomerResponse:
    return CustomerResponse(
        id=record.get("Customer ID", ""),
        first_name=str(record.get("First Name") or ""),
        last_name=str(record.get("Last Name") or ""),
        business_name=str(record.get("Business Name") or ""),
        email=str(record.get("Email") or ""),
        mobile_phone=str(record.get("Mobile Phone") or ""),
        customer_type=str(record.get("Customer Type") or ""),
        notes=str(record.get("Notes") or ""),
    )


def device_response(
    record: dict[str, Any],
) -> CustomerDeviceResponse:
    serial_number = (
        record.get("Serial Number") or record.get("IMEI / Serial Number") or ""
    )

    return CustomerDeviceResponse(
        id=record.get("Device ID", ""),
        customer_id=record.get(
            "Customer ID",
            "",
        ),
        manufacturer=str(record.get("Manufacturer") or ""),
        model=str(record.get("Model") or ""),
        serial_number=str(serial_number),
        device_type=str(record.get("Device Type") or ""),
        notes=str(record.get("Notes") or ""),
    )


def repair_response(
    record: dict[str, Any],
) -> RepairResponse:
    estimated_cost = record.get("Estimated Cost")

    return RepairResponse(
        id=record.get("Ticket ID", ""),
        customer_id=record.get(
            "Customer ID",
            "",
        ),
        device_id=record.get(
            "Device ID",
            "",
        ),
        repair_status=str(record.get("Repair Status") or ""),
        problem_description=str(record.get("Problem Description") or ""),
        technician_notes=str(record.get("Technician Notes") or ""),
        estimated_cost=(float(estimated_cost) if estimated_cost is not None else None),
    )


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    global _application
    global _operations

    _application = Application()

    _operations = RepairApiOperations(_application)

    yield

    _operations = None
    _application = None


app = FastAPI(
    title="Nocturnix Repair Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "repair-platform",
    }


@app.get(
    "/api/customers",
    response_model=list[CustomerResponse],
)
def list_customers(
    q: str = Query(
        default="",
        max_length=200,
    ),
) -> list[CustomerResponse]:
    application = get_application()

    table = (
        application.services.customers.search(q)
        if q
        else application.services.customers.all()
    )

    return [customer_response(record) for record in records_from_dataframe(table)]


@app.post(
    "/api/customers",
    response_model=CustomerResponse,
    status_code=201,
)
def create_customer(
    payload: CustomerCreateRequest,
) -> CustomerResponse:
    operations = get_operations()

    record = operations.create_customer(payload)

    return customer_response(record)


@app.get(
    "/api/customers/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: str,
) -> CustomerResponse:
    application = get_application()

    row = application.services.customers.get(customer_id)

    if row is None:
        try:
            numeric_id = int(customer_id)
        except ValueError:
            numeric_id = None

        if numeric_id is not None:
            row = application.services.customers.get(numeric_id)

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    return customer_response(record_from_series(row))


@app.get(
    "/api/customers/{customer_id}/devices",
    response_model=list[CustomerDeviceResponse],
)
def list_customer_devices(
    customer_id: str,
) -> list[CustomerDeviceResponse]:
    application = get_application()

    resolved_id: int | str = customer_id

    try:
        resolved_id = int(customer_id)
    except ValueError:
        pass

    table = application.services.customer_devices.customer_devices(resolved_id)

    return [device_response(record) for record in records_from_dataframe(table)]


@app.post(
    "/api/devices",
    response_model=CustomerDeviceResponse,
    status_code=201,
)
def create_device(
    payload: CustomerDeviceCreateRequest,
) -> CustomerDeviceResponse:
    operations = get_operations()

    try:
        record = operations.create_customer_device(payload)
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return device_response(record)


@app.get(
    "/api/repairs",
    response_model=list[RepairResponse],
)
def list_repairs(
    q: str = Query(
        default="",
        max_length=200,
    ),
) -> list[RepairResponse]:
    application = get_application()

    table = (
        application.services.repairs.search(q)
        if q
        else application.services.repairs.all()
    )

    return [repair_response(record) for record in records_from_dataframe(table)]


@app.post(
    "/api/repairs",
    response_model=RepairResponse,
    status_code=201,
)
def create_repair(
    payload: RepairCreateRequest,
) -> RepairResponse:
    operations = get_operations()

    try:
        record = operations.create_repair(payload)
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return repair_response(record)


@app.get(
    "/api/repairs/{repair_id}",
    response_model=RepairResponse,
)
def get_repair(
    repair_id: str,
) -> RepairResponse:
    application = get_application()

    resolved_id: int | str = repair_id

    try:
        resolved_id = int(repair_id)
    except ValueError:
        pass

    row = application.services.repairs.get(resolved_id)

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Repair ticket not found.",
        )

    return repair_response(record_from_series(row))


@app.get(
    "/api/dashboard",
    response_model=DashboardResponse,
)
def dashboard() -> DashboardResponse:
    application = get_application()

    repairs = application.services.repairs.all()

    counts: dict[str, int] = {}

    if not repairs.empty and "Repair Status" in repairs.columns:
        raw_counts = (
            repairs["Repair Status"]
            .fillna("Unknown")
            .astype(str)
            .value_counts()
            .to_dict()
        )

        counts = {str(status): int(count) for status, count in raw_counts.items()}

    return DashboardResponse(
        customers=(application.services.customers.count()),
        devices=(application.services.customer_devices.count()),
        repairs=(application.services.repairs.count()),
        repairs_by_status=counts,
    )
