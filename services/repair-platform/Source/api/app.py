from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from secrets import compare_digest
from typing import Any

from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from fastapi.responses import RedirectResponse

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
    IFixitAttributionResponse,
    IFixitDeviceGuideMatchResponse,
    IFixitDeviceResultResponse,
    IFixitDeviceSearchResponse,
    IFixitGuideMetadataResponse,
    IFixitGuideResponse,
    IFixitGuideSearchResponse,
    ProcurementCreateRequest,
    ProcurementDecisionRequest,
    ProcurementItemCreateRequest,
    ProcurementItemResponse,
    ProcurementOrderRequest,
    ProcurementReceiveRequest,
    ProcurementResponse,
    ProcurementSummaryResponse,
    RepairCheckinCreateRequest,
    RepairCheckinResponse,
    RepairCheckinUpdateRequest,
    RepairCreateRequest,
    RepairEventResponse,
    RepairPaymentResponse,
    RepairPaymentSummaryResponse,
    RepairQueueItemResponse,
    RepairResponse,
    RepairUpdateRequest,
    RepairWorkspaceResponse,
    ServicePricingCatalogApprovalRequest,
    ServicePricingCatalogResponse,
    ServicePricingCatalogSaveRequest,
    ServicePricingPreviewRequest,
    ServicePricingPreviewResponse,
    WPFormsIntakeRequest,
    WPFormsIntakeResponse,
)
from config.database import (
    CATALOG_DATABASE,
    OPERATIONS_DATABASE,
)
from integrations.ifixit import IFixitApiError, IFixitClient
from integrations.mobilesentrix import (
    MobileSentrixApiError,
    MobileSentrixClient,
    MobileSentrixDetailedProduct,
    MobileSentrixOAuthError,
    MobileSentrixOAuthService,
    MobileSentrixProduct,
)
from integrations.wpforms import (
    WPFormsMapper,
    WPFormsMappingError,
)
from persistence.catalog_db import CatalogDatabase
from persistence.operations_db import OperationsDatabase
from services.ifixit_device_matching_service import IFixitDeviceMatchingService
from services.pricing_rule_loader import (
    PricingRuleLoader,
    PricingRuleLoadError,
)
from services.pricing_rule_provider import (
    PricingRuleNotFoundError,
    PricingRuleProvider,
)
from services.procurement_service import (
    ProcurementNotFoundError,
    ProcurementService,
    ProcurementStateError,
    ProcurementValidationError,
)
from services.service_pricing_catalog_service import (
    ServicePricingCatalogApprovalError,
    ServicePricingCatalogNotFoundError,
    ServicePricingCatalogService,
    ServicePricingCatalogValidationError,
)
from services.service_pricing_service import (
    ServicePricingNotFoundError,
    ServicePricingService,
    ServicePricingValidationError,
)

# ======================================================
# Environment Configuration
# ======================================================

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

load_dotenv(
    dotenv_path=ENV_FILE,
    override=False,
)


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

WPFORMS_WEBHOOK_SECRET = os.getenv(
    "NOCTURNIX_WPFORMS_WEBHOOK_SECRET",
    "",
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


def get_procurement_service() -> ProcurementService:
    return ProcurementService()


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


def repair_workspace_response(
    repair: dict[str, Any],
    customer: dict[str, Any],
    device: dict[str, Any],
) -> RepairWorkspaceResponse:
    estimated_cost = repair.get("estimated_cost")
    final_cost = repair.get("final_cost")

    return RepairWorkspaceResponse(
        id=str(repair["ticket_id"]),
        customer_id=str(repair["customer_id"]),
        device_id=str(repair["device_id"]),
        repair_status=str(
            repair.get(
                "repair_status",
                "",
            )
            or ""
        ),
        problem_description=str(
            repair.get(
                "problem_description",
                "",
            )
            or ""
        ),
        technician_notes=str(
            repair.get(
                "notes",
                "",
            )
            or ""
        ),
        estimated_cost=(None if estimated_cost is None else float(estimated_cost)),
        final_cost=(None if final_cost is None else float(final_cost)),
        intake_date=str(
            repair.get(
                "intake_date",
                "",
            )
            or ""
        ),
        technician=str(
            repair.get(
                "technician",
                DEFAULT_TECHNICIAN,
            )
            or DEFAULT_TECHNICIAN
        ),
        priority=str(
            repair.get(
                "priority",
                "Normal",
            )
            or "Normal"
        ),
        due_date=str(
            repair.get(
                "due_date",
                "",
            )
            or ""
        ),
        diagnosis=str(
            repair.get(
                "diagnosis",
                "",
            )
            or ""
        ),
        date_completed=str(
            repair.get(
                "date_completed",
                "",
            )
            or ""
        ),
        date_picked_up=str(
            repair.get(
                "date_picked_up",
                "",
            )
            or ""
        ),
        warranty=bool(
            repair.get(
                "warranty",
                False,
            )
        ),
        notes=str(
            repair.get(
                "notes",
                "",
            )
            or ""
        ),
        last_modified=str(
            repair.get(
                "last_modified",
                "",
            )
            or ""
        ),
        customer_type=str(
            customer.get(
                "customer_type",
                "",
            )
            or ""
        ),
        first_name=str(
            customer.get(
                "first_name",
                "",
            )
            or ""
        ),
        last_name=str(
            customer.get(
                "last_name",
                "",
            )
            or ""
        ),
        business_name=str(
            customer.get(
                "business_name",
                "",
            )
            or ""
        ),
        email=str(
            customer.get(
                "email",
                "",
            )
            or ""
        ),
        mobile_phone=str(
            customer.get(
                "mobile_phone",
                "",
            )
            or ""
        ),
        preferred_contact=str(
            customer.get(
                "preferred_contact",
                "",
            )
            or ""
        ),
        catalog_device_id=str(
            device.get(
                "catalog_device_id",
                "",
            )
            or ""
        ),
        manufacturer=str(
            device.get(
                "manufacturer",
                "",
            )
            or ""
        ),
        device_family=str(
            device.get(
                "device_family",
                "",
            )
            or ""
        ),
        device_model=str(
            device.get(
                "device_model",
                "",
            )
            or ""
        ),
        serial_number=str(
            device.get(
                "serial_number",
                "",
            )
            or ""
        ),
        imei_service_tag=str(
            device.get(
                "imei_service_tag",
                "",
            )
            or ""
        ),
        color=str(
            device.get(
                "color",
                "",
            )
            or ""
        ),
        storage=str(
            device.get(
                "storage",
                "",
            )
            or ""
        ),
        carrier=str(
            device.get(
                "carrier",
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


def repair_payment_response(
    record: dict[str, Any],
) -> RepairPaymentResponse:
    return RepairPaymentResponse(
        payment_id=str(
            record.get(
                "payment_id",
                "",
            )
            or ""
        ),
        repair_id=str(
            record.get(
                "repair_id",
                "",
            )
            or ""
        ),
        payment_status=str(
            record.get(
                "payment_status",
                "",
            )
            or ""
        ),
        payment_method=str(
            record.get(
                "payment_method",
                "",
            )
            or ""
        ),
        amount=float(
            record.get(
                "amount",
                0.0,
            )
            or 0.0
        ),
        currency=str(
            record.get(
                "currency",
                "USD",
            )
            or "USD"
        ),
        payment_timestamp=str(
            record.get(
                "payment_timestamp",
                "",
            )
            or ""
        ),
        reference_number=str(
            record.get(
                "reference_number",
                "",
            )
            or ""
        ),
        square_payment_id=str(
            record.get(
                "square_payment_id",
                "",
            )
            or ""
        ),
        square_order_id=str(
            record.get(
                "square_order_id",
                "",
            )
            or ""
        ),
        square_terminal_checkout_id=str(
            record.get(
                "square_terminal_checkout_id",
                "",
            )
            or ""
        ),
        square_receipt_url=str(
            record.get(
                "square_receipt_url",
                "",
            )
            or ""
        ),
        square_refund_id=str(
            record.get(
                "square_refund_id",
                "",
            )
            or ""
        ),
        refunded_square_payment_id=str(
            record.get(
                "refunded_square_payment_id",
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
        created_at=str(
            record.get(
                "created_at",
                "",
            )
            or ""
        ),
        created_by=str(
            record.get(
                "created_by",
                "",
            )
            or ""
        ),
    )


def repair_payment_summary_response(
    record: dict[str, Any],
) -> RepairPaymentSummaryResponse:
    return RepairPaymentSummaryResponse(
        repair_id=str(
            record.get(
                "repair_id",
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
        final_cost=float(
            record.get(
                "final_cost",
                0.0,
            )
            or 0.0
        ),
        amount_paid=float(
            record.get(
                "amount_paid",
                0.0,
            )
            or 0.0
        ),
        balance_due=float(
            record.get(
                "balance_due",
                0.0,
            )
            or 0.0
        ),
        payment_status=str(
            record.get(
                "payment_status",
                "",
            )
            or ""
        ),
        currency=str(
            record.get(
                "currency",
                "USD",
            )
            or "USD"
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


def verify_wpforms_webhook_secret(
    supplied_secret: str | None,
) -> None:
    configured_secret = WPFORMS_WEBHOOK_SECRET.strip()

    if not configured_secret:
        raise HTTPException(
            status_code=503,
            detail=("WPForms webhook authentication is not configured."),
        )

    if not supplied_secret:
        raise HTTPException(
            status_code=401,
            detail=("WPForms webhook secret is required."),
        )

    if not compare_digest(
        supplied_secret,
        configured_secret,
    ):
        raise HTTPException(
            status_code=401,
            detail=("Invalid WPForms webhook secret."),
        )


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
    webhook_secret: str | None = Header(
        default=None,
        alias="X-Nocturnix-Webhook-Secret",
    ),
) -> WPFormsIntakeResponse:
    try:
        verify_wpforms_webhook_secret(webhook_secret)
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


@app.get(
    "/api/repairs/{repair_id}/workspace",
    response_model=RepairWorkspaceResponse,
)
def get_repair_workspace(
    repair_id: str,
) -> RepairWorkspaceResponse:
    database = get_database()

    repair = database.get_repair(repair_id)

    if repair is None:
        raise HTTPException(
            status_code=404,
            detail=("Repair ticket not found."),
        )

    customer_id = str(repair["customer_id"])
    device_id = str(repair["device_id"])

    customer = database.get_customer(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail=("Repair customer not found."),
        )

    device = database.get_customer_device(device_id)

    if device is None:
        raise HTTPException(
            status_code=404,
            detail=("Repair device not found."),
        )

    return repair_workspace_response(
        repair,
        customer,
        device,
    )


@app.get(
    "/api/repairs/{repair_id}/payments",
    response_model=list[RepairPaymentResponse],
)
def list_repair_payments(
    repair_id: str,
) -> list[RepairPaymentResponse]:
    database = get_database()

    if database.get_repair(repair_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Repair ticket not found.",
        )

    return [
        repair_payment_response(record)
        for record in database.list_repair_payments(repair_id)
    ]


@app.post(
    "/api/repairs/{repair_id}/procurements",
    response_model=ProcurementResponse,
    status_code=201,
)
def create_repair_procurement(
    repair_id: str,
    payload: ProcurementCreateRequest,
    service: ProcurementService = Depends(get_procurement_service),
) -> ProcurementResponse:
    try:
        record = service.create_procurement(
            repair_id,
            payload.model_dump(),
        )
    except ProcurementNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ProcurementValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return ProcurementResponse(**record)


@app.get(
    "/api/repairs/{repair_id}/procurements",
    response_model=list[ProcurementResponse],
)
def list_repair_procurements(
    repair_id: str,
    service: ProcurementService = Depends(get_procurement_service),
) -> list[ProcurementResponse]:
    try:
        records = service.list_repair_procurements(repair_id)
    except ProcurementNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return [ProcurementResponse(**record) for record in records]


@app.get(
    "/api/procurements/{procurement_id}",
    response_model=ProcurementResponse,
)
def get_procurement(
    procurement_id: str,
    service: ProcurementService = Depends(get_procurement_service),
) -> ProcurementResponse:
    record = service.get_procurement(procurement_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Procurement request not found.",
        )

    return ProcurementResponse(**record)


@app.post(
    "/api/procurements/{procurement_id}/items",
    response_model=ProcurementItemResponse,
    status_code=201,
)
def add_procurement_item(
    procurement_id: str,
    payload: ProcurementItemCreateRequest,
    service: ProcurementService = Depends(get_procurement_service),
) -> ProcurementItemResponse:
    try:
        record = service.add_item(
            procurement_id,
            payload.model_dump(),
        )
    except ProcurementNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ProcurementValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except ProcurementStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    record = dict(record)

    stock_value = record.get("supplier_in_stock")

    if stock_value is not None:
        record["supplier_in_stock"] = bool(stock_value)

    return ProcurementItemResponse(**record)


@app.get(
    "/api/procurements/{procurement_id}/items",
    response_model=list[ProcurementItemResponse],
)
def list_procurement_items(
    procurement_id: str,
    service: ProcurementService = Depends(get_procurement_service),
) -> list[ProcurementItemResponse]:
    try:
        records = service.list_items(procurement_id)
    except ProcurementNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    output: list[ProcurementItemResponse] = []

    for record in records:
        normalized = dict(record)

        stock_value = normalized.get("supplier_in_stock")

        if stock_value is not None:
            normalized["supplier_in_stock"] = bool(stock_value)

        output.append(ProcurementItemResponse(**normalized))

    return output


@app.get(
    "/api/procurements/{procurement_id}/summary",
    response_model=ProcurementSummaryResponse,
)
def get_procurement_summary(
    procurement_id: str,
    service: ProcurementService = Depends(get_procurement_service),
) -> ProcurementSummaryResponse:
    try:
        record = service.procurement_summary(procurement_id)
    except ProcurementNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return ProcurementSummaryResponse(**record)


@app.post(
    "/api/procurements/{procurement_id}/approve",
    response_model=ProcurementResponse,
)
def approve_procurement(
    procurement_id: str,
    payload: ProcurementDecisionRequest,
    service: ProcurementService = Depends(get_procurement_service),
) -> ProcurementResponse:
    try:
        record = service.approve(
            procurement_id,
            approved_by=payload.actor,
        )
    except ProcurementNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ProcurementValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except ProcurementStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return ProcurementResponse(**record)


@app.post(
    "/api/procurements/{procurement_id}/ready",
    response_model=ProcurementResponse,
)
def mark_procurement_ready(
    procurement_id: str,
    service: ProcurementService = Depends(get_procurement_service),
) -> ProcurementResponse:
    try:
        record = service.mark_ready_for_order(procurement_id)
    except ProcurementNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ProcurementStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return ProcurementResponse(**record)


@app.post(
    "/api/procurements/{procurement_id}/reject",
    response_model=ProcurementResponse,
)
def reject_procurement(
    procurement_id: str,
    payload: ProcurementDecisionRequest,
    service: ProcurementService = Depends(get_procurement_service),
) -> ProcurementResponse:
    try:
        record = service.reject(
            procurement_id,
            rejected_by=payload.actor,
            reason=payload.reason,
        )
    except ProcurementNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ProcurementStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return ProcurementResponse(**record)


@app.post(
    "/api/procurements/{procurement_id}/order",
    response_model=ProcurementResponse,
)
def record_procurement_order(
    procurement_id: str,
    payload: ProcurementOrderRequest,
    service: ProcurementService = Depends(get_procurement_service),
) -> ProcurementResponse:
    try:
        record = service.record_manual_order(
            procurement_id,
            supplier_order_id=(payload.supplier_order_id),
            actual_supplier_cost=(payload.actual_supplier_cost),
            ordered_by=payload.ordered_by,
            supplier_order_date=(payload.supplier_order_date),
        )
    except ProcurementNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ProcurementValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except ProcurementStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return ProcurementResponse(**record)


@app.post(
    "/api/procurements/{procurement_id}/receive",
    response_model=ProcurementResponse,
)
def receive_procurement(
    procurement_id: str,
    payload: ProcurementReceiveRequest,
    service: ProcurementService = Depends(get_procurement_service),
) -> ProcurementResponse:
    try:
        record = service.receive(
            procurement_id,
            received_by=payload.received_by,
        )
    except ProcurementNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ProcurementStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return ProcurementResponse(**record)


@app.post(
    "/api/procurements/{procurement_id}/cancel",
    response_model=ProcurementResponse,
)
def cancel_procurement(
    procurement_id: str,
    payload: ProcurementDecisionRequest,
    service: ProcurementService = Depends(get_procurement_service),
) -> ProcurementResponse:
    try:
        record = service.cancel(
            procurement_id,
            cancelled_by=payload.actor,
            reason=payload.reason,
        )
    except ProcurementNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ProcurementStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return ProcurementResponse(**record)


@app.get(
    "/api/repairs/{repair_id}/payments/summary",
    response_model=RepairPaymentSummaryResponse,
)
def get_repair_payment_summary(
    repair_id: str,
) -> RepairPaymentSummaryResponse:
    database = get_database()

    summary = database.repair_payment_summary(repair_id)

    if summary is None:
        raise HTTPException(
            status_code=404,
            detail="Repair ticket not found.",
        )

    return repair_payment_summary_response(summary)


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
        counts=catalog.table_counts(),
    )


@app.get(
    "/api/catalog/schema",
    response_model=CatalogSchemaResponse,
)
def catalog_schema() -> CatalogSchemaResponse:
    catalog = get_catalog_database()

    return CatalogSchemaResponse(
        tables=catalog.schema(),
    )


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
        manufacturer_id=manufacturer_id,
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
            detail="Catalog device not found.",
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


# ======================================================
# Mobile Sentrix OAuth Integration
# ======================================================


def get_mobilesentrix_oauth() -> MobileSentrixOAuthService:
    return MobileSentrixOAuthService()


@app.get(
    "/api/v1/integrations/mobilesentrix/oauth/status",
)
def mobilesentrix_oauth_status() -> dict[str, object]:
    oauth = get_mobilesentrix_oauth()

    return oauth.status()


@app.get(
    "/api/v1/integrations/mobilesentrix/oauth/start",
)
def mobilesentrix_oauth_start() -> RedirectResponse:
    oauth = get_mobilesentrix_oauth()

    try:
        authorization_url = oauth.build_authorization_url()

    except MobileSentrixOAuthError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return RedirectResponse(
        url=authorization_url,
        status_code=302,
    )


@app.get(
    "/api/v1/integrations/mobilesentrix/oauth/callback",
)
def mobilesentrix_oauth_callback(
    oauth_token: str = Query(...),
    oauth_verifier: str = Query(...),
) -> dict[str, object]:
    oauth = get_mobilesentrix_oauth()

    try:
        result = oauth.exchange_token(
            oauth_token=oauth_token,
            oauth_verifier=oauth_verifier,
        )

    except MobileSentrixOAuthError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    return {
        **result,
        "message": (
            "Mobile Sentrix authorization completed. "
            "Access credentials were stored securely."
        ),
    }


# ======================================================
# Mobile Sentrix Product Search and Detail
# ======================================================


def get_mobilesentrix_client() -> MobileSentrixClient:
    return MobileSentrixClient()


def raise_mobilesentrix_http_error(
    exc: MobileSentrixApiError,
) -> None:
    """
    Translate structured Mobile Sentrix supplier failures into
    stable Nocturnix API responses.

    Supplier authentication details remain an internal integration
    concern and are therefore exposed to API consumers as an
    upstream-service failure rather than a Nocturnix authentication
    failure.
    """

    if exc.not_found:
        status_code = 404
        detail = "Mobile Sentrix product was not found."

    elif exc.timed_out:
        status_code = 504
        detail = "Mobile Sentrix did not respond before the request timed out."

    elif exc.rate_limited:
        status_code = 503
        detail = "Mobile Sentrix is temporarily rate limiting requests."

    elif exc.authentication_failed:
        status_code = 502
        detail = "Mobile Sentrix authentication failed."

    elif exc.connection_failed:
        status_code = 503
        detail = "Mobile Sentrix is currently unreachable."

    else:
        status_code = 502
        detail = "Mobile Sentrix returned an upstream service error."

    raise HTTPException(
        status_code=status_code,
        detail=detail,
    ) from exc


@app.get(
    "/api/v1/integrations/mobilesentrix/products/search",
)
def mobilesentrix_product_search(
    q: str = Query(
        ...,
        min_length=1,
        max_length=200,
    ),
    max_results: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    start_index: int = Query(
        default=0,
        ge=0,
    ),
) -> dict[str, object]:
    """
    Search the Mobile Sentrix supplier catalog.

    Mobile Sentrix remains the source of truth for supplier-specific
    products, SKUs, pricing, and availability. Search results are
    normalized before they are exposed through the Nocturnix API.
    """

    client = get_mobilesentrix_client()

    try:
        result = client.search_products(
            query=q,
            max_results=max_results,
            start_index=start_index,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except MobileSentrixApiError as exc:
        raise_mobilesentrix_http_error(exc)

    data = result.get("data") or {}

    if not isinstance(data, dict):
        return {
            "query": q,
            "environment": client.oauth.status()["environment"],
            "total_items": 0,
            "returned_items": 0,
            "items": [],
        }

    raw_items = data.get("items") or []

    items: list[dict[str, object]] = []

    if isinstance(raw_items, list):
        for item in raw_items:
            if not isinstance(item, dict):
                continue

            product = MobileSentrixProduct.from_api_item(item)

            items.append(product.to_api_dict())

    return {
        "query": q,
        "environment": client.oauth.status()["environment"],
        "total_items": data.get(
            "total_items",
            len(items),
        ),
        "returned_items": len(items),
        "items": items,
    }


@app.get(
    "/api/v1/integrations/mobilesentrix/products/{product_id}",
)
def mobilesentrix_product_detail(
    product_id: str,
) -> dict[str, object]:
    """
    Retrieve one Mobile Sentrix product by supplier product/entity ID.

    The raw Mobile Sentrix response is normalized before it is
    returned through the Nocturnix API.
    """

    normalized_product_id = product_id.strip()

    if not normalized_product_id:
        raise HTTPException(
            status_code=422,
            detail=("Mobile Sentrix product_id must not be empty."),
        )

    client = get_mobilesentrix_client()

    try:
        result = client.get_product(
            product_id=normalized_product_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except MobileSentrixApiError as exc:
        raise_mobilesentrix_http_error(exc)

    if not isinstance(result, dict):
        raise HTTPException(
            status_code=502,
            detail=("Mobile Sentrix returned an unexpected product detail response."),
        )

    product = MobileSentrixDetailedProduct.from_api_item(result)

    return product.to_api_dict()


# ======================================================
# Service Pricing Preview
# ======================================================


def get_pricing_rule_provider() -> PricingRuleProvider:
    """
    Build the runtime pricing-rule provider.

    If no runtime artifact path is configured, pricing remains
    intentionally unavailable and the provider contains zero rules.

    If a path is configured, the artifact must load successfully.
    Invalid, missing, unsupported, or unapproved configured artifacts
    are treated as deployment/configuration errors rather than silently
    falling back to an empty provider.
    """

    configured_path = os.getenv(
        "NOCTURNIX_PRICING_RULES_PATH",
        "",
    ).strip()

    if not configured_path:
        return PricingRuleProvider()

    artifact_path = Path(configured_path)

    if not artifact_path.is_absolute():
        artifact_path = Path(__file__).resolve().parents[2] / artifact_path

    try:
        rules = PricingRuleLoader(artifact_path).load()

    except PricingRuleLoadError as exc:
        raise RuntimeError(
            f"Configured runtime pricing rules could not be loaded: {exc}"
        ) from exc

    return PricingRuleProvider(rules)


def get_service_pricing_catalog_service() -> ServicePricingCatalogService:
    """
    Build the governed service-pricing catalog persistence service.

    Catalog pricing snapshots are stored in the writable Nocturnix
    operations database. The read-only catalog database remains
    unchanged.
    """

    return ServicePricingCatalogService(
        operations_database=get_database(),
    )


def get_service_pricing_service() -> ServicePricingService:
    """
    Build the read-only service pricing preview service.

    The service combines:
    - Nocturnix catalog device identity;
    - an explicitly supplied runtime pricing-rule provider;
    - the pure PricingEngine calculation layer.

    No pricing records are written or approved here.
    """

    return ServicePricingService(
        catalog_database=get_catalog_database(),
        pricing_rule_provider=get_pricing_rule_provider(),
    )


def service_pricing_catalog_response(
    record: Any,
) -> ServicePricingCatalogResponse:
    return ServicePricingCatalogResponse(
        pricing_record_id=record.pricing_record_id,
        catalog_device_id=record.catalog_device_id,
        service_type_id=record.service_type_id,
        service_type=record.service_type,
        service_category_id=record.service_category_id,
        variant_key=record.variant_key,
        variant_name=record.variant_name,
        supplier=record.supplier,
        supplier_product_id=record.supplier_product_id,
        supplier_sku=record.supplier_sku,
        part_name=record.part_name,
        part_cost=float(record.part_cost),
        supplier_in_stock=record.supplier_in_stock,
        supplier_stock_qty=record.supplier_stock_qty,
        supplier_observed_at=record.supplier_observed_at,
        default_labor_hours=float(record.default_labor_hours),
        labor_profile_id=record.labor_profile_id,
        labor_tier=record.labor_tier,
        hourly_rate=float(record.hourly_rate),
        minimum_charge=float(record.minimum_charge),
        target_margin=float(record.target_margin),
        minimum_margin=float(record.minimum_margin),
        overhead_rate=float(record.overhead_rate),
        warranty_rate=float(record.warranty_rate),
        risk_rate=float(record.risk_rate),
        processing_rate=float(record.processing_rate),
        rounding_rule=record.rounding_rule,
        billable_labor_cost=float(record.billable_labor_cost),
        shipping=float(record.shipping),
        consumables=float(record.consumables),
        base_direct_cost=float(record.base_direct_cost),
        total_internal_cost=float(record.total_internal_cost),
        recommended_price=float(record.recommended_price),
        gross_profit=float(record.gross_profit),
        gross_margin=float(record.gross_margin),
        pricing_status=record.pricing_status,
        approved_price=(
            None if record.approved_price is None else float(record.approved_price)
        ),
        approval_status=record.approval_status,
        approved_at=record.approved_at,
        approved_by=record.approved_by,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@app.post(
    "/api/v1/pricing/preview",
    response_model=ServicePricingPreviewResponse,
)
def service_pricing_preview(
    request: ServicePricingPreviewRequest,
) -> ServicePricingPreviewResponse:
    """
    Calculate a read-only Nocturnix service pricing preview.

    The caller supplies:
    - Nocturnix Device ID;
    - governed Service Type ID;
    - selected Mobile Sentrix product/entity ID;
    - optional shipping and consumables.

    Labor rules, margins, reserves, and other pricing policy are
    resolved internally by Nocturnix.

    This endpoint does not approve, publish, persist, procure, or
    place supplier orders.
    """

    supplier_product_id = request.supplier_product_id.strip()

    if not supplier_product_id:
        raise HTTPException(
            status_code=422,
            detail=("Mobile Sentrix supplier_product_id must not be empty."),
        )

    client = get_mobilesentrix_client()

    try:
        raw_product = client.get_product(
            product_id=supplier_product_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except MobileSentrixApiError as exc:
        raise_mobilesentrix_http_error(exc)

    if not isinstance(raw_product, dict):
        raise HTTPException(
            status_code=502,
            detail=("Mobile Sentrix returned an unexpected product detail response."),
        )

    product = MobileSentrixDetailedProduct.from_api_item(raw_product)

    pricing_service = get_service_pricing_service()

    try:
        preview = pricing_service.preview(
            device_id=request.device_id,
            service_type_id=request.service_type_id,
            variant_key=request.variant_key,
            product=product,
            shipping=request.shipping,
            consumables=request.consumables,
        )

    except ServicePricingValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except ServicePricingNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except PricingRuleNotFoundError as exc:
        raise HTTPException(
            status_code=409,
            detail=(
                "No approved runtime pricing rule is available "
                f"for {request.service_type_id.strip()}."
            ),
        ) from exc

    return ServicePricingPreviewResponse(
        device_id=preview.device_id,
        device_model=preview.device_model,
        manufacturer_id=preview.manufacturer_id,
        manufacturer=preview.manufacturer,
        service_type_id=preview.service_type_id,
        service_type=preview.service_type,
        service_category_id=preview.service_category_id,
        variant_key=preview.variant_key,
        variant_name=preview.variant_name,
        supplier=preview.supplier,
        supplier_product_id=preview.supplier_product_id,
        supplier_sku=preview.supplier_sku,
        part_name=preview.part_name,
        part_cost=float(preview.part_cost),
        supplier_in_stock=preview.supplier_in_stock,
        supplier_stock_qty=preview.supplier_stock_qty,
        default_labor_hours=float(preview.default_labor_hours),
        labor_profile_id=preview.labor_profile_id,
        labor_tier=preview.labor_tier,
        hourly_rate=float(preview.hourly_rate),
        minimum_charge=float(preview.minimum_charge),
        calculated_labor_cost=float(preview.calculated_labor_cost),
        billable_labor_cost=float(preview.billable_labor_cost),
        shipping=float(preview.shipping),
        consumables=float(preview.consumables),
        base_direct_cost=float(preview.base_direct_cost),
        overhead_rate=float(preview.overhead_rate),
        overhead_reserve=float(preview.overhead_reserve),
        warranty_rate=float(preview.warranty_rate),
        warranty_reserve=float(preview.warranty_reserve),
        risk_rate=float(preview.risk_rate),
        risk_reserve=float(preview.risk_reserve),
        processing_rate=float(preview.processing_rate),
        processing_reserve=float(preview.processing_reserve),
        total_internal_cost=float(preview.total_internal_cost),
        target_margin=float(preview.target_margin),
        minimum_margin=float(preview.minimum_margin),
        raw_retail_price=float(preview.raw_retail_price),
        recommended_retail_price=float(preview.recommended_retail_price),
        gross_profit=float(preview.gross_profit),
        gross_margin=float(preview.gross_margin),
        pricing_status=preview.pricing_status,
        market_low=(
            float(preview.market_low) if preview.market_low is not None else None
        ),
        market_average=(
            float(preview.market_average)
            if preview.market_average is not None
            else None
        ),
        market_high=(
            float(preview.market_high) if preview.market_high is not None else None
        ),
        market_sample_count=preview.market_sample_count,
        market_position=preview.market_position,
    )


# ======================================================
# Service Pricing Catalog
# ======================================================


@app.post(
    "/api/v1/pricing/catalog",
    response_model=ServicePricingCatalogResponse,
)
def save_service_pricing_catalog(
    request: ServicePricingCatalogSaveRequest,
    catalog_service: ServicePricingCatalogService = Depends(
        get_service_pricing_catalog_service
    ),
) -> ServicePricingCatalogResponse:
    """
    Calculate and persist a governed service-pricing snapshot.

    The caller provides only pricing inputs and the selected supplier
    product identity. Supplier data and governed pricing policy are
    resolved internally before the resulting snapshot is persisted.

    Repeated saves for the same catalog identity refresh the existing
    DRAFT pricing record rather than creating a duplicate PRC record.

    Approved pricing records are frozen and cannot be refreshed.
    """

    supplier_product_id = request.supplier_product_id.strip()

    if not supplier_product_id:
        raise HTTPException(
            status_code=422,
            detail=("Mobile Sentrix supplier_product_id must not be empty."),
        )

    client = get_mobilesentrix_client()

    try:
        raw_product = client.get_product(
            product_id=supplier_product_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except MobileSentrixApiError as exc:
        raise_mobilesentrix_http_error(exc)

    if not isinstance(
        raw_product,
        dict,
    ):
        raise HTTPException(
            status_code=502,
            detail=("Mobile Sentrix returned an unexpected product detail response."),
        )

    product = MobileSentrixDetailedProduct.from_api_item(raw_product)

    pricing_service = get_service_pricing_service()

    try:
        preview = pricing_service.preview(
            device_id=request.device_id,
            service_type_id=request.service_type_id,
            variant_key=request.variant_key,
            product=product,
            shipping=request.shipping,
            consumables=request.consumables,
        )

        timestamp = datetime.now(UTC)

        record = catalog_service.save_from_preview(
            preview,
            supplier_observed_at=timestamp,
            now=timestamp,
        )

    except ServicePricingValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except ServicePricingNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except PricingRuleNotFoundError as exc:
        raise HTTPException(
            status_code=409,
            detail=(
                "No approved runtime pricing rule "
                "is available for "
                f"{request.service_type_id.strip()}."
            ),
        ) from exc

    except ServicePricingCatalogValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except ServicePricingCatalogApprovalError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return service_pricing_catalog_response(record)


@app.get(
    "/api/v1/pricing/catalog",
    response_model=list[ServicePricingCatalogResponse],
)
def list_service_pricing_catalog(
    catalog_device_id: str | None = Query(
        default=None,
    ),
    service_type_id: str | None = Query(
        default=None,
    ),
    variant_key: str | None = Query(
        default=None,
    ),
    approval_status: str | None = Query(
        default=None,
    ),
    catalog_service: ServicePricingCatalogService = Depends(
        get_service_pricing_catalog_service
    ),
) -> list[ServicePricingCatalogResponse]:
    try:
        records = catalog_service.list_records(
            catalog_device_id=catalog_device_id,
            service_type_id=service_type_id,
            variant_key=variant_key,
            approval_status=approval_status,
        )

    except ServicePricingCatalogValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return [service_pricing_catalog_response(record) for record in records]


@app.get(
    "/api/v1/pricing/catalog/{pricing_record_id}",
    response_model=ServicePricingCatalogResponse,
)
def get_service_pricing_catalog_record(
    pricing_record_id: str,
    catalog_service: ServicePricingCatalogService = Depends(
        get_service_pricing_catalog_service
    ),
) -> ServicePricingCatalogResponse:
    try:
        record = catalog_service.get(pricing_record_id)

    except ServicePricingCatalogValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Service pricing record not found.",
        )

    return service_pricing_catalog_response(record)


@app.post(
    ("/api/v1/pricing/catalog/{pricing_record_id}/approve"),
    response_model=ServicePricingCatalogResponse,
)
def approve_service_pricing_catalog_record(
    pricing_record_id: str,
    request: ServicePricingCatalogApprovalRequest,
    catalog_service: ServicePricingCatalogService = Depends(
        get_service_pricing_catalog_service
    ),
) -> ServicePricingCatalogResponse:
    try:
        record = catalog_service.approve(
            pricing_record_id,
            approved_price=Decimal(str(request.approved_price)),
            approved_by=request.approved_by,
        )

    except ServicePricingCatalogNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ServicePricingCatalogValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except ServicePricingCatalogApprovalError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return service_pricing_catalog_response(record)


# ======================================================
# iFixit Technical Guide Metadata
# ======================================================


def get_ifixit_client() -> IFixitClient:
    base_url = os.getenv(
        "NOCTURNIX_IFIXIT_BASE_URL",
        IFixitClient.DEFAULT_BASE_URL,
    )
    timeout_value = os.getenv(
        "NOCTURNIX_IFIXIT_TIMEOUT_SECONDS",
        str(IFixitClient.DEFAULT_TIMEOUT_SECONDS),
    )

    try:
        timeout_seconds = float(timeout_value)

    except ValueError as exc:
        raise RuntimeError(
            "NOCTURNIX_IFIXIT_TIMEOUT_SECONDS must be a number."
        ) from exc

    return IFixitClient(
        base_url=base_url,
        timeout_seconds=timeout_seconds,
    )


def get_ifixit_matching_service(
    client: IFixitClient = Depends(get_ifixit_client),
) -> IFixitDeviceMatchingService:
    return IFixitDeviceMatchingService(client)


def ifixit_attribution() -> IFixitAttributionResponse:
    return IFixitAttributionResponse()


def ifixit_upstream_error(
    exc: IFixitApiError,
) -> HTTPException:
    if exc.timed_out:
        status_code = 504

    elif exc.status_code == 429:
        status_code = 503

    else:
        status_code = 502

    return HTTPException(
        status_code=status_code,
        detail=str(exc),
    )


@app.get(
    "/api/v1/integrations/ifixit/devices/search",
    response_model=IFixitDeviceSearchResponse,
)
def ifixit_device_search(
    q: str = Query(
        ...,
        min_length=1,
        max_length=200,
    ),
    client: IFixitClient = Depends(get_ifixit_client),
) -> IFixitDeviceSearchResponse:
    try:
        results = client.search_devices(query=q)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except IFixitApiError as exc:
        raise ifixit_upstream_error(exc) from exc

    items = [
        IFixitDeviceResultResponse.model_validate(item.to_api_dict())
        for item in results
    ]

    return IFixitDeviceSearchResponse(
        query=q,
        returned_items=len(items),
        items=items,
        attribution=ifixit_attribution(),
    )


@app.get(
    "/api/v1/integrations/ifixit/guides/search",
    response_model=IFixitGuideSearchResponse,
)
def ifixit_guide_search(
    q: str = Query(
        ...,
        min_length=1,
        max_length=200,
    ),
    client: IFixitClient = Depends(get_ifixit_client),
) -> IFixitGuideSearchResponse:
    try:
        results = client.search_guides(query=q)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except IFixitApiError as exc:
        raise ifixit_upstream_error(exc) from exc

    items = [
        IFixitGuideMetadataResponse.model_validate(item.to_api_dict())
        for item in results
    ]

    return IFixitGuideSearchResponse(
        query=q,
        returned_items=len(items),
        items=items,
        attribution=ifixit_attribution(),
    )


@app.get(
    "/api/v1/integrations/ifixit/guides/{guide_id}",
    response_model=IFixitGuideResponse,
)
def get_ifixit_guide(
    guide_id: int,
    client: IFixitClient = Depends(get_ifixit_client),
) -> IFixitGuideResponse:
    try:
        guide = client.get_guide_metadata(guide_id=guide_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except IFixitApiError as exc:
        raise ifixit_upstream_error(exc) from exc

    if guide is None:
        raise HTTPException(
            status_code=404,
            detail="iFixit guide was not found.",
        )

    return IFixitGuideResponse(
        guide=IFixitGuideMetadataResponse.model_validate(guide.to_api_dict()),
        attribution=ifixit_attribution(),
    )


@app.get(
    "/api/v1/integrations/ifixit/device-guide-match",
    response_model=IFixitDeviceGuideMatchResponse,
)
def match_ifixit_device_guides(
    manufacturer: str = Query(
        ...,
        min_length=1,
        max_length=100,
    ),
    model: str = Query(
        ...,
        min_length=1,
        max_length=200,
    ),
    ifixit_device_override: str | None = Query(
        default=None,
        min_length=1,
        max_length=200,
    ),
    service: IFixitDeviceMatchingService = Depends(get_ifixit_matching_service),
) -> IFixitDeviceGuideMatchResponse:
    try:
        result = service.match_device(
            manufacturer=manufacturer,
            model=model,
            ifixit_device_override=ifixit_device_override,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except IFixitApiError as exc:
        raise ifixit_upstream_error(exc) from exc

    payload = result.to_api_dict()
    payload["attribution"] = ifixit_attribution().model_dump()

    return IFixitDeviceGuideMatchResponse.model_validate(payload)
