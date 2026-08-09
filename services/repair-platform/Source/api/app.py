from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
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
    RepairCheckinCreateRequest,
    RepairCheckinResponse,
    RepairCheckinUpdateRequest,
    RepairCreateRequest,
    RepairEventResponse,
    RepairQueueItemResponse,
    RepairResponse,
    RepairUpdateRequest,
    WPFormsIntakeRequest,
    WPFormsIntakeResponse,
)
from config.database import (
    CATALOG_DATABASE,
    OPERATIONS_DATABASE,
)
from integrations.wpforms import (
    WPFormsMapper,
    WPFormsMappingError,
)
from persistence.catalog_db import CatalogDatabase
from persistence.operations_db import OperationsDatabase

# ======================================================
# Application Configuration
# ======================================================

DEFAULT_TECHNICIAN = "Ryan Brown"


WPFORMS_MAPPINGS_DIRECTORY = (
    Path(__file__).resolve().parents[4]
    / "integrations"
    / "wordpress"
    / "wpforms"
    / "mappings"
)


# ======================================================
# Application State
# ======================================================

_database: OperationsDatabase | None = None

_catalog_database: CatalogDatabase | None = None

_operations: RepairApiOperations | None = None

_wpforms_mapper: WPFormsMapper | None = None


# ======================================================
# Application State Access
# ======================================================


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


def get_wpforms_mapper() -> WPFormsMapper:
    global _wpforms_mapper

    if _wpforms_mapper is None:
        _wpforms_mapper = WPFormsMapper(WPFORMS_MAPPINGS_DIRECTORY)

    return _wpforms_mapper


# ======================================================
# Date / Time
# ======================================================


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


# ======================================================
# Response Serialization
# ======================================================


def customer_response(
    record: dict[str, Any],
) -> CustomerResponse:
    return CustomerResponse(
        id=str(record["customer_id"]),
        first_name=str(
            record.get(
                "first_name",
                "",
            )
            or ""
        ),
        last_name=str(
            record.get(
                "last_name",
                "",
            )
            or ""
        ),
        business_name=str(
            record.get(
                "business_name",
                "",
            )
            or ""
        ),
        email=str(
            record.get(
                "email",
                "",
            )
            or ""
        ),
        mobile_phone=str(
            record.get(
                "mobile_phone",
                "",
            )
            or ""
        ),
        customer_type=str(
            record.get(
                "customer_type",
                "",
            )
            or ""
        ),
        notes=str(
            record.get(
                "notes",
                "",
            )
            or ""
        ),
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
        manufacturer=str(
            record.get(
                "manufacturer",
                "",
            )
            or ""
        ),
        model=str(
            record.get(
                "device_model",
                "",
            )
            or ""
        ),
        serial_number=str(
            record.get(
                "serial_number",
                "",
            )
            or ""
        ),
        device_type=str(
            record.get(
                "device_family",
                "",
            )
            or ""
        ),
        notes=str(
            record.get(
                "notes",
                "",
            )
            or ""
        ),
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
        technician_notes=str(
            record.get(
                "notes",
                "",
            )
            or ""
        ),
        estimated_cost=(None if estimated_cost is None else float(estimated_cost)),
        final_cost=(None if final_cost is None else float(final_cost)),
        intake_date=str(
            record.get(
                "intake_date",
                "",
            )
            or ""
        ),
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
    business_name = str(
        record.get(
            "business_name",
            "",
        )
        or ""
    ).strip()

    first_name = str(
        record.get(
            "first_name",
            "",
        )
        or ""
    ).strip()

    last_name = str(
        record.get(
            "last_name",
            "",
        )
        or ""
    ).strip()

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
        manufacturer=str(
            record.get(
                "manufacturer",
                "",
            )
            or ""
        ),
        device_model=str(
            record.get(
                "device_model",
                "",
            )
            or ""
        ),
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
        intake_date=str(
            record.get(
                "intake_date",
                "",
            )
            or ""
        ),
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
        old_value=str(
            record.get(
                "old_value",
                "",
            )
            or ""
        ),
        new_value=str(
            record.get(
                "new_value",
                "",
            )
            or ""
        ),
        notes=str(
            record.get(
                "notes",
                "",
            )
            or ""
        ),
        created_at=str(record["created_at"]),
        created_by=str(
            record.get(
                "created_by",
                DEFAULT_TECHNICIAN,
            )
            or DEFAULT_TECHNICIAN
        ),
    )


def repair_checkin_response(
    record: dict[str, Any],
) -> RepairCheckinResponse:
    battery_percentage = record.get("battery_percentage")

    return RepairCheckinResponse(
        id=str(record["checkin_id"]),
        repair_id=str(record["repair_id"]),
        customer_id=str(record["customer_id"]),
        device_id=str(record["device_id"]),
        technician=str(
            record.get(
                "technician",
                DEFAULT_TECHNICIAN,
            )
            or DEFAULT_TECHNICIAN
        ),
        checkin_timestamp=str(
            record.get(
                "checkin_timestamp",
                "",
            )
            or ""
        ),
        powers_on=str(
            record.get(
                "powers_on",
                "",
            )
            or ""
        ),
        battery_percentage=(
            None if battery_percentage is None else int(battery_percentage)
        ),
        screen_condition=str(
            record.get(
                "screen_condition",
                "",
            )
            or ""
        ),
        frame_condition=str(
            record.get(
                "frame_condition",
                "",
            )
            or ""
        ),
        back_glass_condition=str(
            record.get(
                "back_glass_condition",
                "",
            )
            or ""
        ),
        charging_port_condition=str(
            record.get(
                "charging_port_condition",
                "",
            )
            or ""
        ),
        camera_condition=str(
            record.get(
                "camera_condition",
                "",
            )
            or ""
        ),
        speaker_condition=str(
            record.get(
                "speaker_condition",
                "",
            )
            or ""
        ),
        microphone_condition=str(
            record.get(
                "microphone_condition",
                "",
            )
            or ""
        ),
        face_id_touch_id=str(
            record.get(
                "face_id_touch_id",
                "",
            )
            or ""
        ),
        liquid_damage=str(
            record.get(
                "liquid_damage",
                "",
            )
            or ""
        ),
        existing_damage=str(
            record.get(
                "existing_damage",
                "",
            )
            or ""
        ),
        accessories_received=str(
            record.get(
                "accessories_received",
                "",
            )
            or ""
        ),
        device_passcode=str(
            record.get(
                "device_passcode",
                "",
            )
            or ""
        ),
        passcode_available=str(
            record.get(
                "passcode_available",
                "",
            )
            or ""
        ),
        intake_notes=str(
            record.get(
                "intake_notes",
                "",
            )
            or ""
        ),
    )


# ======================================================
# Repair Event Helper
# ======================================================


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


# ======================================================
# Application Lifecycle
# ======================================================


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    del app

    global _database
    global _catalog_database
    global _operations
    global _wpforms_mapper

    _database = OperationsDatabase(OPERATIONS_DATABASE)

    _catalog_database = CatalogDatabase(CATALOG_DATABASE)

    _operations = RepairApiOperations(_database)

    _wpforms_mapper = None

    yield

    _wpforms_mapper = None
    _operations = None
    _catalog_database = None
    _database = None


# ======================================================
# FastAPI Application
# ======================================================


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


# ======================================================
# Health
# ======================================================


@app.get("/health")
def health() -> dict[str, str]:
    database = get_database()

    return {
        "status": "ok",
        "service": "repair-platform",
        "database": str(database.database_path),
    }


# ======================================================
# Customers
# ======================================================


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
            detail=("Customer not found."),
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
            detail=("Customer not found."),
        )

    return [
        device_response(record)
        for record in database.list_customer_devices(customer_id)
    ]


# ======================================================
# Customer Devices
# ======================================================


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


# ======================================================
# WPForms Mapping
# ======================================================


@app.post("/api/integrations/wpforms/map")
def map_wpforms_submission(
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        return get_wpforms_mapper().map_submission(payload)

    except WPFormsMappingError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


# ======================================================
# WPForms Intake
# ======================================================


@app.post(
    "/api/integrations/wpforms/intake",
    response_model=WPFormsIntakeResponse,
    status_code=201,
)
def create_wpforms_intake(
    payload: WPFormsIntakeRequest,
) -> WPFormsIntakeResponse:
    try:
        database = get_database()

        form_id = payload.form_id.strip()

        entry_id = payload.entry_id.strip()

        if not form_id:
            raise HTTPException(
                status_code=422,
                detail=("WPForms form_id is required."),
            )

        if not entry_id:
            raise HTTPException(
                status_code=422,
                detail=("WPForms entry_id is required."),
            )

        existing_submission = database.get_wpforms_submission(
            form_id,
            entry_id,
        )

        if existing_submission is not None:
            return WPFormsIntakeResponse(
                customer_id=str(existing_submission["customer_id"]),
                device_id=str(existing_submission["device_id"]),
                repair_id=str(existing_submission["repair_id"]),
                checkin_id=str(existing_submission["checkin_id"]),
                duplicate=True,
            )

        mapped = get_wpforms_mapper().map_submission(payload.model_dump())

        fields = mapped.get(
            "fields",
            {},
        )

        if not isinstance(
            fields,
            dict,
        ):
            raise HTTPException(
                status_code=422,
                detail=("Mapped WPForms fields are invalid."),
            )

        customer_name = str(
            fields.get(
                "customer_name",
                "",
            )
        ).strip()

        email = str(
            fields.get(
                "email",
                "",
            )
        ).strip()

        mobile_phone = str(
            fields.get(
                "mobile_phone",
                "",
            )
        ).strip()

        business_name = str(
            fields.get(
                "business_name",
                "",
            )
        ).strip()

        first_name = ""
        last_name = ""

        raw_customer_name = fields.get("customer_name")

        if isinstance(
            raw_customer_name,
            dict,
        ):
            first_name = str(
                raw_customer_name.get(
                    "first_name",
                    "",
                )
            ).strip()

            last_name = str(
                raw_customer_name.get(
                    "last_name",
                    "",
                )
            ).strip()

        elif customer_name:
            name_parts = customer_name.split()

            if name_parts:
                first_name = name_parts[0]

            if len(name_parts) > 1:
                last_name = " ".join(name_parts[1:])

        now = utc_now()

        # ----------------------------------------------
        # Customer
        # ----------------------------------------------

        customer_id = database.next_id(
            table="customers",
            column="customer_id",
            prefix="CUS",
            width=6,
        )

        customer_record = {
            "customer_id": customer_id,
            "customer_type": "Individual",
            "first_name": first_name,
            "last_name": last_name,
            "business_name": business_name,
            "email": email,
            "mobile_phone": mobile_phone,
            "home_phone": "",
            "work_phone": "",
            "preferred_contact": str(
                fields.get(
                    "preferred_contact",
                    "Mobile Phone",
                )
            ),
            "billing_address": "",
            "shipping_address": "",
            "tax_exempt": 0,
            "active": 1,
            "date_created": now,
            "last_modified": now,
            "notes": ("Created from WPForms intake."),
        }

        customer = database.create_customer(customer_record)

        # ----------------------------------------------
        # Customer Device
        # ----------------------------------------------

        device_id = database.next_id(
            table="customer_devices",
            column="device_id",
            prefix="CDEV",
            width=6,
        )

        device_record = {
            "device_id": device_id,
            "customer_id": customer_id,
            "catalog_device_id": "",
            "manufacturer": str(
                fields.get(
                    "manufacturer",
                    "",
                )
            ),
            "device_family": str(
                fields.get(
                    "device_family",
                    "",
                )
            ),
            "device_model": str(
                fields.get(
                    "device_model",
                    "",
                )
            ),
            "serial_number": str(
                fields.get(
                    "serial_number",
                    "",
                )
            ),
            "imei_service_tag": str(
                fields.get(
                    "imei",
                    "",
                )
                or fields.get(
                    "asset_tag",
                    "",
                )
            ),
            "color": str(
                fields.get(
                    "color",
                    "",
                )
            ),
            "storage": str(
                fields.get(
                    "storage",
                    "",
                )
            ),
            "carrier": str(
                fields.get(
                    "carrier",
                    "",
                )
            ),
            "purchase_date": str(
                fields.get(
                    "purchase_date",
                    "",
                )
            ),
            "warranty_expiration": str(
                fields.get(
                    "warranty_expiration",
                    "",
                )
            ),
            "active": 1,
            "notes": ("Created from WPForms intake."),
        }

        device = database.create_customer_device(device_record)

        # ----------------------------------------------
        # Repair
        # ----------------------------------------------

        repair_id = database.next_id(
            table="repair_tickets",
            column="ticket_id",
            prefix="RPR",
            width=6,
        )

        repair_record = {
            "ticket_id": repair_id,
            "customer_id": customer_id,
            "device_id": device_id,
            "repair_status": "New Intake",
            "intake_date": now,
            "technician": DEFAULT_TECHNICIAN,
            "problem_description": str(
                fields.get(
                    "problem_description",
                    ("WPForms repair intake"),
                )
            ),
            "diagnosis": "",
            "estimated_cost": None,
            "final_cost": None,
            "date_completed": None,
            "date_picked_up": None,
            "warranty": 0,
            "notes": ("Created from WPForms intake."),
            "last_modified": now,
            "priority": "Normal",
            "due_date": "",
        }

        repair = database.create_repair(repair_record)

        # ----------------------------------------------
        # Repair Check-In
        # ----------------------------------------------

        checkin_id = database.next_id(
            table="repair_checkins",
            column="checkin_id",
            prefix="CHK",
            width=6,
        )

        checkin_record = {
            "checkin_id": checkin_id,
            "repair_id": repair_id,
            "customer_id": customer_id,
            "device_id": device_id,
            "technician": DEFAULT_TECHNICIAN,
            "checkin_timestamp": now,
            "powers_on": str(
                fields.get(
                    "powers_on",
                    "",
                )
            ),
            "battery_percentage": None,
            "screen_condition": str(
                fields.get(
                    "screen_condition",
                    "",
                )
            ),
            "frame_condition": str(
                fields.get(
                    "frame_condition",
                    "",
                )
            ),
            "back_glass_condition": str(
                fields.get(
                    "back_glass_condition",
                    "",
                )
            ),
            "charging_port_condition": str(
                fields.get(
                    "charging_port_condition",
                    "",
                )
            ),
            "camera_condition": str(
                fields.get(
                    "camera_condition",
                    "",
                )
            ),
            "speaker_condition": str(
                fields.get(
                    "speaker_condition",
                    "",
                )
            ),
            "microphone_condition": str(
                fields.get(
                    "microphone_condition",
                    "",
                )
            ),
            "face_id_touch_id": str(
                fields.get(
                    "face_id_touch_id",
                    "",
                )
            ),
            "liquid_damage": str(
                fields.get(
                    "liquid_damage",
                    "",
                )
            ),
            "existing_damage": str(
                fields.get(
                    "existing_damage",
                    "",
                )
            ),
            "accessories_received": str(
                fields.get(
                    "accessories_received",
                    "",
                )
            ),
            "device_passcode": "",
            "passcode_available": str(
                fields.get(
                    "passcode_available",
                    "",
                )
            ),
            "intake_notes": str(
                fields.get(
                    "intake_notes",
                    "",
                )
            ),
        }

        checkin = database.create_repair_checkin(checkin_record)

        # ----------------------------------------------
        # WPForms Submission Tracking
        # ----------------------------------------------

        submission_id = database.next_id(
            table=("wpforms_submissions"),
            column="submission_id",
            prefix="WPF",
            width=6,
        )

        database.create_wpforms_submission(
            {
                "submission_id": submission_id,
                "wpforms_form_id": form_id,
                "wpforms_entry_id": entry_id,
                "customer_id": customer_id,
                "device_id": device_id,
                "repair_id": repair_id,
                "checkin_id": checkin_id,
                "received_at": now,
            }
        )

        # ----------------------------------------------
        # Timeline
        # ----------------------------------------------

        create_repair_event(
            database,
            repair_id=repair_id,
            event_type=("wpforms_intake_created"),
            new_value=repair_id,
            notes=("Repair created from WPForms intake."),
        )

        return WPFormsIntakeResponse(
            customer_id=str(customer["customer_id"]),
            device_id=str(device["device_id"]),
            repair_id=str(repair["ticket_id"]),
            checkin_id=str(checkin["checkin_id"]),
            duplicate=False,
        )

    except HTTPException:
        raise

    except WPFormsMappingError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(f"{type(exc).__name__}: {exc}"),
        ) from exc


# ======================================================
# Repairs
# ======================================================


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
        event_type=("repair_created"),
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
        payload.technician if (payload.technician is not None) else DEFAULT_TECHNICIAN
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
            old_value=(old_technician),
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


# ======================================================
# Repair Timeline
# ======================================================


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


# ======================================================
# Repair Check-In
# ======================================================


@app.post(
    "/api/repairs/{repair_id}/checkin",
    response_model=RepairCheckinResponse,
    status_code=201,
)
def create_repair_checkin(
    repair_id: str,
    payload: RepairCheckinCreateRequest,
) -> RepairCheckinResponse:
    database = get_database()

    repair = database.get_repair(repair_id)

    if repair is None:
        raise HTTPException(
            status_code=404,
            detail=("Repair ticket not found."),
        )

    existing = database.get_repair_checkin(repair_id)

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=("A check-in already exists for this repair ticket."),
        )

    if payload.battery_percentage is not None and (
        payload.battery_percentage < 0 or payload.battery_percentage > 100
    ):
        raise HTTPException(
            status_code=422,
            detail=("Battery percentage must be between 0 and 100."),
        )

    checkin_id = database.next_id(
        table="repair_checkins",
        column="checkin_id",
        prefix="CHK",
        width=6,
    )

    record: dict[str, Any] = {
        "checkin_id": checkin_id,
        "repair_id": repair_id,
        "customer_id": str(repair["customer_id"]),
        "device_id": str(repair["device_id"]),
        "technician": DEFAULT_TECHNICIAN,
        "checkin_timestamp": utc_now(),
        "powers_on": payload.powers_on,
        "battery_percentage": payload.battery_percentage,
        "screen_condition": payload.screen_condition,
        "frame_condition": payload.frame_condition,
        "back_glass_condition": payload.back_glass_condition,
        "charging_port_condition": (payload.charging_port_condition),
        "camera_condition": payload.camera_condition,
        "speaker_condition": payload.speaker_condition,
        "microphone_condition": payload.microphone_condition,
        "face_id_touch_id": payload.face_id_touch_id,
        "liquid_damage": payload.liquid_damage,
        "existing_damage": payload.existing_damage,
        "accessories_received": (payload.accessories_received),
        "device_passcode": payload.device_passcode,
        "passcode_available": payload.passcode_available,
        "intake_notes": payload.intake_notes,
    }

    created = database.create_repair_checkin(record)

    create_repair_event(
        database,
        repair_id=repair_id,
        event_type=("checkin_created"),
        new_value=checkin_id,
        notes=(f"Device check-in completed by {DEFAULT_TECHNICIAN}."),
    )

    return repair_checkin_response(created)


@app.get(
    "/api/repairs/{repair_id}/checkin",
    response_model=RepairCheckinResponse,
)
def get_repair_checkin(
    repair_id: str,
) -> RepairCheckinResponse:
    database = get_database()

    if database.get_repair(repair_id) is None:
        raise HTTPException(
            status_code=404,
            detail=("Repair ticket not found."),
        )

    record = database.get_repair_checkin(repair_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=("Repair check-in not found."),
        )

    return repair_checkin_response(record)


@app.patch(
    "/api/repairs/{repair_id}/checkin",
    response_model=RepairCheckinResponse,
)
def update_repair_checkin(
    repair_id: str,
    payload: RepairCheckinUpdateRequest,
) -> RepairCheckinResponse:
    database = get_database()

    repair = database.get_repair(repair_id)

    if repair is None:
        raise HTTPException(
            status_code=404,
            detail=("Repair ticket not found."),
        )

    existing = database.get_repair_checkin(repair_id)

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=("Repair check-in not found."),
        )

    if payload.battery_percentage is not None and (
        payload.battery_percentage < 0 or payload.battery_percentage > 100
    ):
        raise HTTPException(
            status_code=422,
            detail=("Battery percentage must be between 0 and 100."),
        )

    raw_updates = payload.model_dump(exclude_unset=True)

    changes: list[str] = []

    updates: dict[str, Any] = {}

    for (
        key,
        new_value,
    ) in raw_updates.items():
        old_value = existing.get(key)

        if new_value == old_value:
            continue

        updates[key] = new_value

        changes.append(f"{key}: {old_value!s} -> {new_value!s}")

    if not updates:
        return repair_checkin_response(existing)

    updated = database.update_repair_checkin(
        str(existing["checkin_id"]),
        updates,
    )

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail=("Repair check-in not found."),
        )

    create_repair_event(
        database,
        repair_id=repair_id,
        event_type=("checkin_updated"),
        old_value="",
        new_value="",
        notes="; ".join(changes),
    )

    return repair_checkin_response(updated)


# ======================================================
# Repair Queue
# ======================================================


@app.get(
    "/api/repair-queue",
    response_model=list[RepairQueueItemResponse],
)
def repair_queue() -> list[RepairQueueItemResponse]:
    return [
        repair_queue_response(record) for record in get_database().list_repair_queue()
    ]


# ======================================================
# Dashboard
# ======================================================


@app.get(
    "/api/dashboard",
    response_model=DashboardResponse,
)
def dashboard() -> DashboardResponse:
    counts = get_database().counts()

    return DashboardResponse(
        customers=(counts["customers"]),
        devices=(counts["devices"]),
        repairs=(counts["repairs"]),
        repairs_by_status=(counts["repairs_by_status"]),
    )


# ======================================================
# Catalog
# ======================================================


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

    return CatalogSchemaResponse(tables=(catalog.schema()))


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
