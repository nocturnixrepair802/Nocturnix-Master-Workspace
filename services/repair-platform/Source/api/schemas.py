from __future__ import annotations

from typing import Any

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


class RepairWorkspaceResponse(BaseModel):
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

    diagnosis: str = ""
    date_completed: str = ""
    date_picked_up: str = ""
    warranty: bool = False
    notes: str = ""
    last_modified: str = ""

    customer_type: str = ""
    first_name: str = ""
    last_name: str = ""
    business_name: str = ""
    email: str = ""
    mobile_phone: str = ""
    preferred_contact: str = ""

    catalog_device_id: str = ""
    manufacturer: str = ""
    device_family: str = ""
    device_model: str = ""
    serial_number: str = ""
    imei_service_tag: str = ""
    color: str = ""
    storage: str = ""
    carrier: str = ""


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


# ======================================================
# Repair Check-In
# ======================================================


class RepairCheckinCreateRequest(BaseModel):
    powers_on: str = ""
    battery_percentage: int | None = None
    screen_condition: str = ""
    frame_condition: str = ""
    back_glass_condition: str = ""
    charging_port_condition: str = ""
    camera_condition: str = ""
    speaker_condition: str = ""
    microphone_condition: str = ""
    face_id_touch_id: str = ""
    liquid_damage: str = ""
    existing_damage: str = ""
    accessories_received: str = ""
    device_passcode: str = ""
    passcode_available: str = ""
    intake_notes: str = ""


class RepairCheckinUpdateRequest(BaseModel):
    powers_on: str | None = None
    battery_percentage: int | None = None
    screen_condition: str | None = None
    frame_condition: str | None = None
    back_glass_condition: str | None = None
    charging_port_condition: str | None = None
    camera_condition: str | None = None
    speaker_condition: str | None = None
    microphone_condition: str | None = None
    face_id_touch_id: str | None = None
    liquid_damage: str | None = None
    existing_damage: str | None = None
    accessories_received: str | None = None
    device_passcode: str | None = None
    passcode_available: str | None = None
    intake_notes: str | None = None


class RepairCheckinResponse(BaseModel):
    id: str
    repair_id: str
    customer_id: str
    device_id: str

    technician: str = "Ryan Brown"
    checkin_timestamp: str = ""

    powers_on: str = ""
    battery_percentage: int | None = None
    screen_condition: str = ""
    frame_condition: str = ""
    back_glass_condition: str = ""
    charging_port_condition: str = ""
    camera_condition: str = ""
    speaker_condition: str = ""
    microphone_condition: str = ""
    face_id_touch_id: str = ""
    liquid_damage: str = ""
    existing_damage: str = ""
    accessories_received: str = ""
    device_passcode: str = ""
    passcode_available: str = ""
    intake_notes: str = ""


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


class WPFormsIntakeRequest(BaseModel):
    form_id: str
    entry_id: str
    fields: dict[str, Any]


class WPFormsIntakeResponse(BaseModel):
    customer_id: str
    device_id: str
    repair_id: str
    checkin_id: str
    duplicate: bool = False


class RepairPaymentResponse(BaseModel):
    payment_id: str
    repair_id: str
    payment_status: str = ""
    payment_method: str = ""
    amount: float = 0.0
    currency: str = "USD"
    payment_timestamp: str = ""
    reference_number: str = ""
    square_payment_id: str = ""
    square_order_id: str = ""
    square_terminal_checkout_id: str = ""
    square_receipt_url: str = ""
    square_refund_id: str = ""
    refunded_square_payment_id: str = ""
    notes: str = ""
    created_at: str = ""
    created_by: str = ""


class RepairPaymentSummaryResponse(BaseModel):
    repair_id: str
    repair_status: str = ""
    final_cost: float = 0.0
    amount_paid: float = 0.0
    balance_due: float = 0.0
    payment_status: str = ""
    currency: str = "USD"


class ProcurementCreateRequest(BaseModel):
    supplier: str = "Mobile Sentrix"
    requested_by: str = ""
    notes: str = ""


class ProcurementItemCreateRequest(BaseModel):
    supplier: str = "Mobile Sentrix"
    supplier_product_id: str = ""
    supplier_sku: str = ""
    product_name: str = ""
    product_url: str = ""
    quantity: int = 1
    unit_cost: float | None = None
    supplier_in_stock: bool | None = None
    supplier_stock_quantity: int | None = None
    supplier_observed_at: str = ""
    notes: str = ""
    created_by: str = ""


class ProcurementDecisionRequest(BaseModel):
    actor: str = ""
    reason: str = ""


class ProcurementOrderRequest(BaseModel):
    supplier_order_id: str
    actual_supplier_cost: float | None = None
    ordered_by: str = ""
    supplier_order_date: str = ""


class ProcurementReceiveRequest(BaseModel):
    received_by: str = ""


class ProcurementItemResponse(BaseModel):
    procurement_item_id: str
    procurement_id: str
    repair_id: str

    supplier: str = "Mobile Sentrix"

    supplier_product_id: str | None = None
    supplier_sku: str | None = None

    product_name: str = ""
    product_url: str | None = None

    quantity: int = 1
    unit_cost: float | None = None
    estimated_line_total: float | None = None

    supplier_in_stock: bool | None = None
    supplier_stock_quantity: int | None = None
    supplier_observed_at: str | None = None

    received_quantity: int = 0

    notes: str = ""
    created_at: str
    created_by: str = ""
    updated_at: str


class ProcurementResponse(BaseModel):
    procurement_id: str
    repair_id: str

    supplier: str = "Mobile Sentrix"
    procurement_status: str

    requested_at: str
    requested_by: str = ""

    approved_at: str | None = None
    approved_by: str | None = None

    rejected_at: str | None = None
    rejected_by: str | None = None
    rejection_reason: str | None = None

    ready_for_order_at: str | None = None

    supplier_order_id: str | None = None
    supplier_order_date: str | None = None

    actual_supplier_cost: float | None = None

    ordered_at: str | None = None
    ordered_by: str | None = None

    received_at: str | None = None
    received_by: str | None = None

    cancelled_at: str | None = None
    cancelled_by: str | None = None
    cancellation_reason: str | None = None

    notes: str = ""

    created_at: str
    created_by: str = ""
    updated_at: str


class ProcurementSummaryResponse(BaseModel):
    procurement_id: str
    repair_id: str
    supplier: str
    procurement_status: str
    item_count: int
    requested_units: int
    received_units: int
    estimated_total: float
    actual_supplier_cost: float | None = None
    supplier_order_id: str | None = None


# ======================================================
# iFixit Read-Only Metadata
# ======================================================


class IFixitAttributionResponse(BaseModel):
    provider: str = "iFixit"
    provider_url: str = "https://www.ifixit.com/"
    api_version: str = "2.0"
    license_name: str = "CC BY-NC-SA 3.0"
    license_url: str = "https://creativecommons.org/licenses/by-nc-sa/3.0/"


class IFixitDeviceResultResponse(BaseModel):
    title: str
    result_type: str
    category: str | None = None
    url: str | None = None


class IFixitGuideMetadataResponse(BaseModel):
    guide_id: int | None = None
    title: str
    category: str | None = None
    subject: str | None = None
    guide_type: str | None = None
    url: str | None = None
    locale: str | None = None
    author: str | None = None
    revision_id: int | None = None
    modified_date: float | None = None
    time_required_min: int | None = None
    time_required_max: int | None = None
    difficulty: str | None = None


class IFixitDeviceSearchResponse(BaseModel):
    query: str
    returned_items: int
    items: list[IFixitDeviceResultResponse]
    attribution: IFixitAttributionResponse


class IFixitGuideSearchResponse(BaseModel):
    query: str
    returned_items: int
    items: list[IFixitGuideMetadataResponse]
    attribution: IFixitAttributionResponse


class IFixitGuideResponse(BaseModel):
    guide: IFixitGuideMetadataResponse
    attribution: IFixitAttributionResponse


class IFixitNormalizedDeviceResponse(BaseModel):
    manufacturer: str
    model: str
    search_query: str


class IFixitRankedCandidateResponse(BaseModel):
    title: str
    result_type: str
    category: str | None = None
    url: str | None = None
    confidence: float
    classification: str
    reasons: list[str]


class IFixitDeviceGuideMatchResponse(BaseModel):
    normalized_device: IFixitNormalizedDeviceResponse
    candidates: list[IFixitRankedCandidateResponse]
    selected_candidate: IFixitRankedCandidateResponse | None = None
    match_classification: str
    confidence: float
    guide_summaries: list[IFixitGuideMetadataResponse]
    override_applied: bool
    attribution: IFixitAttributionResponse

# ======================================================
# Service Pricing Preview
# ======================================================


class ServicePricingPreviewRequest(BaseModel):
    device_id: str
    service_type_id: str
    supplier_product_id: str
    shipping: float = 0.0
    consumables: float = 5.0


class ServicePricingPreviewResponse(BaseModel):
    device_id: str
    device_model: str
    manufacturer_id: str
    manufacturer: str

    service_type_id: str
    service_type: str
    service_category_id: str

    supplier: str
    supplier_product_id: str
    supplier_sku: str
    part_name: str
    part_cost: float

    supplier_in_stock: bool | None = None
    supplier_stock_qty: int | None = None

    default_labor_hours: float
    labor_profile_id: str
    labor_tier: str
    hourly_rate: float
    minimum_charge: float

    calculated_labor_cost: float
    billable_labor_cost: float

    shipping: float
    consumables: float

    base_direct_cost: float

    overhead_rate: float
    overhead_reserve: float

    warranty_rate: float
    warranty_reserve: float

    risk_rate: float
    risk_reserve: float

    processing_rate: float
    processing_reserve: float

    total_internal_cost: float

    target_margin: float
    minimum_margin: float

    raw_retail_price: float
    recommended_retail_price: float

    gross_profit: float
    gross_margin: float

    pricing_status: str

    market_low: float | None = None
    market_average: float | None = None
    market_high: float | None = None
    market_sample_count: int | None = None
    market_position: str | None = None
