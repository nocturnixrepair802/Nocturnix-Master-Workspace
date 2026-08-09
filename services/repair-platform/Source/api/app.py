from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from api.operations import RepairApiOperations
from api.schemas import (
    CatalogDeviceResponse,
    CatalogHealthResponse,
    CatalogManufacturerResponse,
    CatalogPricingResponse,
    CatalogSchemaResponse,
    CatalogServiceResponse,
    CustomerCreateRequest,
    CustomerDeviceCreateRequest,
    CustomerDeviceResponse,
    CustomerResponse,
    DashboardResponse,
    RepairCreateRequest,
    RepairEventResponse,
    RepairQueueItemResponse,
    RepairResponse,
    RepairUpdateRequest,
)
from config.database import (
    CATALOG_DATABASE,
    OPERATIONS_DATABASE,
)
from persistence.catalog_db import CatalogDatabase
from persistence.operations_db import OperationsDatabase

DEFAULT_TECHNICIAN = "Ryan Brown"


_database: OperationsDatabase | None = None
_catalog_database: CatalogDatabase | None = None
_operations: RepairApiOperations | None = None


def get_database() -> OperationsDatabase:
    if _database is None:
        raise RuntimeError("Operations database has not initialized.")

    return _database


def get_catalog_database() -> CatalogDatabase:
    if _catalog_database is None:
        raise RuntimeError("Catalog database has not initialized.")

    return _catalog_database


def get_operations() -> RepairApiOperations:
    if _operations is None:
        raise RuntimeError("Repair API operations have not initialized.")

    return _operations


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def customer_response(
    record: dict[str, Any],
) -> CustomerResponse:
    return CustomerResponse(
        id=str(record["customer_id"]),
        first_name=str(record.get("first_name", "") or ""),
        last_name=str(record.get("last_name", "") or ""),
        business_name=str(record.get("business_name", "") or ""),
        email=str(record.get("email", "") or ""),
        mobile_phone=str(record.get("mobile_phone", "") or ""),
        customer_type=str(record.get("customer_type", "") or ""),
        notes=str(record.get("notes", "") or ""),
    )


def device_response(
    record: dict[str, Any],
) -> CustomerDeviceResponse:
    return CustomerDeviceResponse(
        id=str(record["device_id"]),
        customer_id=str(record["customer_id"]),
        catalog_device_id=str(
            record.get(
                "catalog_device_id",
                "",
            )
            or ""
        ),
        manufacturer=str(record.get("manufacturer", "") or ""),
        model=str(record.get("device_model", "") or ""),
        serial_number=str(record.get("serial_number", "") or ""),
        device_type=str(record.get("device_family", "") or ""),
        notes=str(record.get("notes", "") or ""),
    )


def repair_response(
    record: dict[str, Any],
) -> RepairResponse:
    estimated_cost = record.get("estimated_cost")

    final_cost = record.get("final_cost")

    return RepairResponse(
        id=str(record["ticket_id"]),
        customer_id=str(record["customer_id"]),
        device_id=str(record["device_id"]),
        repair_status=str(
            record.get(
                "repair_status",
                "",
            )
            or ""
        ),
        problem_description=str(
            record.get(
                "problem_description",
                "",
            )
            or ""
        ),
        technician_notes=str(record.get("notes", "") or ""),
        estimated_cost=(None if estimated_cost is None else float(estimated_cost)),
        final_cost=(None if final_cost is None else float(final_cost)),
        intake_date=str(record.get("intake_date", "") or ""),
        technician=str(
            record.get(
                "technician",
                DEFAULT_TECHNICIAN,
            )
            or DEFAULT_TECHNICIAN
        ),
        priority=str(
            record.get(
                "priority",
                "Normal",
            )
            or "Normal"
        ),
        due_date=str(
            record.get(
                "due_date",
                "",
            )
            or ""
        ),
    )


def repair_queue_response(
    record: dict[str, Any],
) -> RepairQueueItemResponse:
    business_name = str(record.get("business_name", "") or "").strip()

    first_name = str(record.get("first_name", "") or "").strip()

    last_name = str(record.get("last_name", "") or "").strip()

    customer_name = (
        business_name
        or " ".join(
            part
            for part in (
                first_name,
                last_name,
            )
            if part
        )
        or str(
            record.get(
                "customer_id",
                "",
            )
        )
    )

    estimated_cost = record.get("estimated_cost")

    final_cost = record.get("final_cost")

    return RepairQueueItemResponse(
        id=str(record["ticket_id"]),
        customer_id=str(record["customer_id"]),
        customer_name=customer_name,
        device_id=str(record["device_id"]),
        catalog_device_id=str(
            record.get(
                "catalog_device_id",
                "",
            )
            or ""
        ),
        manufacturer=str(record.get("manufacturer", "") or ""),
        device_model=str(record.get("device_model", "") or ""),
        repair_status=str(
            record.get(
                "repair_status",
                "",
            )
            or ""
        ),
        problem_description=str(
            record.get(
                "problem_description",
                "",
            )
            or ""
        ),
        estimated_cost=(None if estimated_cost is None else float(estimated_cost)),
        final_cost=(None if final_cost is None else float(final_cost)),
        intake_date=str(record.get("intake_date", "") or ""),
        technician=str(
            record.get(
                "technician",
                DEFAULT_TECHNICIAN,
            )
            or DEFAULT_TECHNICIAN
        ),
        priority=str(
            record.get(
                "priority",
                "Normal",
            )
            or "Normal"
        ),
        due_date=str(
            record.get(
                "due_date",
                "",
            )
            or ""
        ),
    )


def repair_event_response(
    record: dict[str, Any],
) -> RepairEventResponse:
    return RepairEventResponse(
        event_id=str(record["event_id"]),
        repair_id=str(record["repair_id"]),
        event_type=str(record["event_type"]),
        old_value=str(record.get("old_value", "") or ""),
        new_value=str(record.get("new_value", "") or ""),
        notes=str(record.get("notes", "") or ""),
        created_at=str(record["created_at"]),
        created_by=str(
            record.get(
                "created_by",
                DEFAULT_TECHNICIAN,
            )
            or DEFAULT_TECHNICIAN
        ),
    )


def create_repair_event(
    database: OperationsDatabase,
    *,
    repair_id: str,
    event_type: str,
    old_value: str = "",
    new_value: str = "",
    notes: str = "",
) -> dict[str, Any]:
    event_id = database.next_id(
        table="repair_events",
        column="event_id",
        prefix="EVT",
        width=6,
    )

    return database.create_repair_event(
        {
            "event_id": event_id,
            "repair_id": repair_id,
            "event_type": event_type,
            "old_value": old_value,
            "new_value": new_value,
            "notes": notes,
            "created_at": utc_now(),
            "created_by": DEFAULT_TECHNICIAN,
        }
    )


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    del app

    global _database
    global _catalog_database
    global _operations

    _database = OperationsDatabase(OPERATIONS_DATABASE)

    _catalog_database = CatalogDatabase(CATALOG_DATABASE)

    _operations = RepairApiOperations(_database)

    yield

    _operations = None
    _catalog_database = None
    _database = None


app = FastAPI(
    title="Nocturnix Repair Platform API",
    version="0.5.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://[::1]:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    database = get_database()

    return {
        "status": "ok",
        "service": "repair-platform",
        "database": str(database.database_path),
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
    database = get_database()

    return [customer_response(record) for record in database.list_customers(search=q)]


@app.post(
    "/api/customers",
    response_model=CustomerResponse,
    status_code=201,
)
def create_customer(
    payload: CustomerCreateRequest,
) -> CustomerResponse:
    record = get_operations().create_customer(payload)

    return customer_response(record)


@app.get(
    "/api/customers/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: str,
) -> CustomerResponse:
    record = get_database().get_customer(customer_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    return customer_response(record)


@app.get(
    "/api/customers/{customer_id}/devices",
    response_model=list[CustomerDeviceResponse],
)
def list_customer_devices(
    customer_id: str,
) -> list[CustomerDeviceResponse]:
    database = get_database()

    if database.get_customer(customer_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    return [
        device_response(record)
        for record in database.list_customer_devices(customer_id)
    ]


@app.get(
    "/api/devices/{device_id}",
    response_model=CustomerDeviceResponse,
)
def get_device(
    device_id: str,
) -> CustomerDeviceResponse:
    record = get_database().get_customer_device(device_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=("Customer device not found."),
        )

    return device_response(record)


@app.post(
    "/api/devices",
    response_model=CustomerDeviceResponse,
    status_code=201,
)
def create_device(
    payload: CustomerDeviceCreateRequest,
) -> CustomerDeviceResponse:
    try:
        record = get_operations().create_customer_device(payload)
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
    return [repair_response(record) for record in get_database().list_repairs(search=q)]


@app.post(
    "/api/repairs",
    response_model=RepairResponse,
    status_code=201,
)
def create_repair(
    payload: RepairCreateRequest,
) -> RepairResponse:
    operations = get_operations()
    database = get_database()

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

    database.update_repair(
        str(record["ticket_id"]),
        {
            "technician": DEFAULT_TECHNICIAN,
            "priority": "Normal",
            "due_date": "",
        },
    )

    record = database.get_repair(str(record["ticket_id"])) or record

    create_repair_event(
        database,
        repair_id=str(record["ticket_id"]),
        event_type="repair_created",
        new_value=str(
            record.get(
                "repair_status",
                "New Intake",
            )
        ),
        notes=("Repair ticket created."),
    )

    return repair_response(record)


@app.get(
    "/api/repairs/{repair_id}",
    response_model=RepairResponse,
)
def get_repair(
    repair_id: str,
) -> RepairResponse:
    record = get_database().get_repair(repair_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=("Repair ticket not found."),
        )

    return repair_response(record)


@app.patch(
    "/api/repairs/{repair_id}",
    response_model=RepairResponse,
)
def update_repair(
    repair_id: str,
    payload: RepairUpdateRequest,
) -> RepairResponse:
    database = get_database()

    existing = database.get_repair(repair_id)

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=("Repair ticket not found."),
        )

    updates: dict[str, Any] = {
        "last_modified": utc_now(),
    }

    if payload.repair_status is not None:
        old_value = str(
            existing.get(
                "repair_status",
                "",
            )
            or ""
        )

        new_value = payload.repair_status

        if new_value != old_value:
            updates["repair_status"] = new_value

            create_repair_event(
                database,
                repair_id=repair_id,
                event_type=("status_changed"),
                old_value=old_value,
                new_value=new_value,
            )

            if new_value == "Completed":
                updates["date_completed"] = utc_now()

    if payload.technician_notes is not None:
        old_value = str(
            existing.get(
                "notes",
                "",
            )
            or ""
        )

        new_value = payload.technician_notes

        if new_value != old_value:
            updates["notes"] = new_value

            create_repair_event(
                database,
                repair_id=repair_id,
                event_type=("technician_notes_changed"),
                old_value=old_value,
                new_value=new_value,
            )

    if payload.final_cost is not None:
        old_raw = existing.get("final_cost")

        old_value = "" if old_raw is None else str(old_raw)

        new_value = str(payload.final_cost)

        if new_value != old_value:
            updates["final_cost"] = payload.final_cost

            create_repair_event(
                database,
                repair_id=repair_id,
                event_type=("final_cost_changed"),
                old_value=old_value,
                new_value=new_value,
            )

    technician = (
        payload.technician if payload.technician is not None else DEFAULT_TECHNICIAN
    )

    old_technician = str(
        existing.get(
            "technician",
            "",
        )
        or ""
    )

    if technician != old_technician:
        updates["technician"] = technician

        create_repair_event(
            database,
            repair_id=repair_id,
            event_type=("technician_changed"),
            old_value=old_technician,
            new_value=technician,
        )

    if payload.priority is not None:
        allowed_priorities = {
            "Low",
            "Normal",
            "High",
            "Urgent",
        }

        if payload.priority not in allowed_priorities:
            raise HTTPException(
                status_code=422,
                detail=("Priority must be Low, Normal, High, or Urgent."),
            )

        old_value = str(
            existing.get(
                "priority",
                "Normal",
            )
            or "Normal"
        )

        new_value = payload.priority

        if new_value != old_value:
            updates["priority"] = new_value

            create_repair_event(
                database,
                repair_id=repair_id,
                event_type=("priority_changed"),
                old_value=old_value,
                new_value=new_value,
            )

    if payload.due_date is not None:
        old_value = str(
            existing.get(
                "due_date",
                "",
            )
            or ""
        )

        new_value = payload.due_date.strip()

        if new_value != old_value:
            updates["due_date"] = new_value

            create_repair_event(
                database,
                repair_id=repair_id,
                event_type=("due_date_changed"),
                old_value=old_value,
                new_value=new_value,
            )

    updated = database.update_repair(
        repair_id,
        updates,
    )

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail=("Repair ticket not found."),
        )

    return repair_response(updated)


@app.get(
    "/api/repairs/{repair_id}/events",
    response_model=list[RepairEventResponse],
)
def list_repair_events(
    repair_id: str,
) -> list[RepairEventResponse]:
    database = get_database()

    if database.get_repair(repair_id) is None:
        raise HTTPException(
            status_code=404,
            detail=("Repair ticket not found."),
        )

    return [
        repair_event_response(record)
        for record in database.list_repair_events(repair_id)
    ]


@app.get(
    "/api/repair-queue",
    response_model=list[RepairQueueItemResponse],
)
def repair_queue() -> list[RepairQueueItemResponse]:
    return [
        repair_queue_response(record) for record in get_database().list_repair_queue()
    ]


@app.get(
    "/api/dashboard",
    response_model=DashboardResponse,
)
def dashboard() -> DashboardResponse:
    counts = get_database().counts()

    return DashboardResponse(
        customers=counts["customers"],
        devices=counts["devices"],
        repairs=counts["repairs"],
        repairs_by_status=counts["repairs_by_status"],
    )


@app.get(
    "/api/catalog/health",
    response_model=CatalogHealthResponse,
)
def catalog_health() -> CatalogHealthResponse:
    catalog = get_catalog_database()

    return CatalogHealthResponse(
        database=str(catalog.database_path),
        counts=(catalog.table_counts()),
    )


@app.get(
    "/api/catalog/schema",
    response_model=CatalogSchemaResponse,
)
def catalog_schema() -> CatalogSchemaResponse:
    catalog = get_catalog_database()

    return CatalogSchemaResponse(tables=catalog.schema())


@app.get(
    "/api/catalog/manufacturers",
    response_model=list[CatalogManufacturerResponse],
)
def catalog_manufacturers() -> list[CatalogManufacturerResponse]:
    return [
        CatalogManufacturerResponse(**record)
        for record in get_catalog_database().list_manufacturers()
    ]


@app.get(
    "/api/catalog/devices",
    response_model=list[CatalogDeviceResponse],
)
def catalog_devices(
    q: str = Query(
        default="",
        max_length=200,
    ),
    manufacturer_id: str | None = Query(
        default=None,
    ),
    limit: int = Query(
        default=250,
        ge=1,
        le=1000,
    ),
) -> list[CatalogDeviceResponse]:
    records = get_catalog_database().list_devices(
        search=q,
        manufacturer_id=(manufacturer_id),
        limit=limit,
    )

    return [CatalogDeviceResponse(**record) for record in records]


@app.get(
    "/api/catalog/devices/{device_id}",
    response_model=CatalogDeviceResponse,
)
def catalog_device(
    device_id: str,
) -> CatalogDeviceResponse:
    record = get_catalog_database().get_device(device_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=("Catalog device not found."),
        )

    return CatalogDeviceResponse(**record)


@app.get(
    "/api/catalog/services",
    response_model=list[CatalogServiceResponse],
)
def catalog_services(
    q: str = Query(
        default="",
        max_length=200,
    ),
    device_id: str | None = Query(
        default=None,
    ),
    limit: int = Query(
        default=250,
        ge=1,
        le=1000,
    ),
) -> list[CatalogServiceResponse]:
    records = get_catalog_database().list_services(
        search=q,
        device_id=device_id,
        limit=limit,
    )

    return [CatalogServiceResponse(**record) for record in records]


@app.get(
    "/api/catalog/pricing",
    response_model=list[CatalogPricingResponse],
)
def catalog_pricing(
    q: str = Query(
        default="",
        max_length=200,
    ),
    service_id: str | None = Query(
        default=None,
    ),
    device_id: str | None = Query(
        default=None,
    ),
    limit: int = Query(
        default=250,
        ge=1,
        le=1000,
    ),
) -> list[CatalogPricingResponse]:
    records = get_catalog_database().list_pricing(
        search=q,
        service_id=service_id,
        device_id=device_id,
        limit=limit,
    )

    return [CatalogPricingResponse(**record) for record in records]
