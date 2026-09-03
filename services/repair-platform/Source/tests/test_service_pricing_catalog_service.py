from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from models.service_pricing import ServicePricingPreview
from persistence.operations_db import OperationsDatabase
from services.service_pricing_catalog_service import (
    ServicePricingCatalogApprovalError,
    ServicePricingCatalogNotFoundError,
    ServicePricingCatalogService,
    ServicePricingCatalogValidationError,
)


def pricing_preview() -> ServicePricingPreview:
    return ServicePricingPreview(
        device_id="DEV000093",
        device_model="iPhone 15 Pro",
        manufacturer_id="MFR000001",
        manufacturer="Apple",
        service_type_id="STY000001",
        service_type="Screen Replacement",
        service_category_id="SC000010",
        variant_key="BASE",
        variant_name=None,
        supplier="Mobile Sentrix",
        supplier_product_id="249690",
        supplier_sku="107082999999",
        part_name="OLED Screen Assembly",
        part_cost=Decimal("45.00"),
        supplier_in_stock=True,
        supplier_stock_qty=12,
        default_labor_hours=Decimal("1.00"),
        labor_profile_id="LAB000002",
        labor_tier="L2 Standard",
        hourly_rate=Decimal("100.00"),
        minimum_charge=Decimal("85.00"),
        calculated_labor_cost=Decimal("100.00"),
        billable_labor_cost=Decimal("100.00"),
        shipping=Decimal("0.00"),
        consumables=Decimal("5.00"),
        base_direct_cost=Decimal("150.00"),
        overhead_rate=Decimal("0.12"),
        overhead_reserve=Decimal("18.00"),
        warranty_rate=Decimal("0.05"),
        warranty_reserve=Decimal("7.50"),
        risk_rate=Decimal("0.04"),
        risk_reserve=Decimal("6.00"),
        processing_rate=Decimal("0.03"),
        processing_reserve=Decimal("4.50"),
        rounding_rule="End in .99",
        total_internal_cost=Decimal("186.00"),
        target_margin=Decimal("0.30"),
        minimum_margin=Decimal("0.20"),
        raw_retail_price=Decimal("265.7142857"),
        recommended_retail_price=Decimal("265.99"),
        gross_profit=Decimal("79.99"),
        gross_margin=Decimal("0.300827"),
        pricing_status="READY",
    )


def test_save_from_preview_refreshes_existing_identity(
    tmp_path: Path,
) -> None:
    service = catalog_service(tmp_path)

    first = service.save_from_preview(
        pricing_preview(),
        supplier_observed_at=datetime(
            2026,
            9,
            3,
            18,
            0,
            tzinfo=UTC,
        ),
        now=datetime(
            2026,
            9,
            3,
            19,
            0,
            tzinfo=UTC,
        ),
    )

    refreshed_preview = replace(
        pricing_preview(),
        part_cost=Decimal("50.00"),
        recommended_retail_price=Decimal("279.99"),
        gross_profit=Decimal("89.99"),
    )

    second = service.save_from_preview(
        refreshed_preview,
        supplier_observed_at=datetime(
            2026,
            9,
            3,
            20,
            0,
            tzinfo=UTC,
        ),
        now=datetime(
            2026,
            9,
            3,
            20,
            5,
            tzinfo=UTC,
        ),
    )

    assert first.pricing_record_id == "PRC000001"
    assert second.pricing_record_id == "PRC000001"

    assert second.part_cost == Decimal("50.00")
    assert second.recommended_price == Decimal("279.99")

    assert second.supplier_observed_at == datetime(
        2026,
        9,
        3,
        20,
        0,
        tzinfo=UTC,
    )

    assert second.updated_at == datetime(
        2026,
        9,
        3,
        20,
        5,
        tzinfo=UTC,
    )


def test_save_from_preview_creates_new_identity(
    tmp_path: Path,
) -> None:
    service = catalog_service(tmp_path)

    first = service.save_from_preview(
        pricing_preview(),
        now=datetime(
            2026,
            9,
            3,
            19,
            0,
            tzinfo=UTC,
        ),
    )

    second_preview = replace(
        pricing_preview(),
        supplier_product_id="249691",
        supplier_sku="107082999998",
    )

    second = service.save_from_preview(
        second_preview,
        now=datetime(
            2026,
            9,
            3,
            19,
            5,
            tzinfo=UTC,
        ),
    )

    assert first.pricing_record_id == "PRC000001"
    assert second.pricing_record_id == "PRC000002"


def catalog_service(
    tmp_path: Path,
) -> ServicePricingCatalogService:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    return ServicePricingCatalogService(database)


def test_create_from_preview_persists_snapshot(
    tmp_path: Path,
) -> None:
    service = catalog_service(tmp_path)

    now = datetime(
        2026,
        9,
        3,
        19,
        0,
        tzinfo=UTC,
    )

    observed_at = datetime(
        2026,
        9,
        3,
        18,
        55,
        tzinfo=UTC,
    )

    result = service.create_from_preview(
        pricing_preview(),
        supplier_observed_at=observed_at,
        now=now,
    )

    assert result.pricing_record_id == "PRC000001"
    assert result.catalog_device_id == "DEV000093"

    assert result.service_type_id == "STY000001"
    assert result.variant_key == "BASE"
    assert result.variant_name is None

    assert result.supplier == "Mobile Sentrix"
    assert result.supplier_product_id == "249690"
    assert result.supplier_sku == "107082999999"

    assert result.part_cost == Decimal("45.00")
    assert result.supplier_in_stock is True
    assert result.supplier_stock_qty == 12
    assert result.supplier_observed_at == observed_at

    assert result.recommended_price == Decimal("265.99")

    assert result.approved_price is None
    assert result.approval_status == "DRAFT"
    assert result.approved_at is None
    assert result.approved_by is None

    assert result.created_at == now
    assert result.updated_at == now


def test_create_from_preview_stores_integer_cents(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    service = ServicePricingCatalogService(database)

    result = service.create_from_preview(
        pricing_preview(),
        now=datetime(
            2026,
            9,
            3,
            19,
            0,
            tzinfo=UTC,
        ),
    )

    stored = database.get_service_pricing_record(result.pricing_record_id)

    assert stored is not None

    assert stored["part_cost_cents"] == 4500
    assert stored["hourly_rate_cents"] == 10000
    assert stored["minimum_charge_cents"] == 8500

    assert stored["billable_labor_cost_cents"] == 10000

    assert stored["shipping_cents"] == 0
    assert stored["consumables_cents"] == 500
    assert stored["base_direct_cost_cents"] == 15000

    assert stored["total_internal_cost_cents"] == 18600

    assert stored["recommended_price_cents"] == 26599

    assert stored["gross_profit_cents"] == 7999


def test_decimal_policy_values_are_preserved_as_text(
    tmp_path: Path,
) -> None:
    database = OperationsDatabase(tmp_path / "operations.sqlite3")

    service = ServicePricingCatalogService(database)

    result = service.create_from_preview(
        pricing_preview(),
        now=datetime(
            2026,
            9,
            3,
            19,
            0,
            tzinfo=UTC,
        ),
    )

    stored = database.get_service_pricing_record(result.pricing_record_id)

    assert stored is not None

    assert stored["default_labor_hours"] == "1.00"
    assert stored["target_margin"] == "0.30"
    assert stored["minimum_margin"] == "0.20"
    assert stored["overhead_rate"] == "0.12"
    assert stored["warranty_rate"] == "0.05"
    assert stored["risk_rate"] == "0.04"
    assert stored["processing_rate"] == "0.03"
    assert stored["gross_margin"] == "0.300827"


def test_variant_identity_is_preserved(
    tmp_path: Path,
) -> None:
    service = catalog_service(tmp_path)

    variant = replace(
        pricing_preview(),
        service_type_id="STY000055",
        service_type="Diagnostic",
        service_category_id="SC000009",
        variant_key="ADVANCED_DIAGNOSTIC",
        variant_name="Advanced Diagnostic",
    )

    result = service.create_from_preview(
        variant,
        now=datetime(
            2026,
            9,
            3,
            19,
            0,
            tzinfo=UTC,
        ),
    )

    assert result.service_type_id == "STY000055"
    assert result.variant_key == "ADVANCED_DIAGNOSTIC"
    assert result.variant_name == "Advanced Diagnostic"


def test_naive_now_is_rejected(
    tmp_path: Path,
) -> None:
    service = catalog_service(tmp_path)

    with pytest.raises(
        ServicePricingCatalogValidationError,
        match="timezone-aware",
    ):
        service.create_from_preview(
            pricing_preview(),
            now=datetime(
                2026,
                9,
                3,
                19,
                0,
            ),
        )


def test_naive_supplier_observed_at_is_rejected(
    tmp_path: Path,
) -> None:
    service = catalog_service(tmp_path)

    with pytest.raises(
        ServicePricingCatalogValidationError,
        match="supplier_observed_at",
    ):
        service.create_from_preview(
            pricing_preview(),
            supplier_observed_at=datetime(
                2026,
                9,
                3,
                18,
                55,
            ),
            now=datetime(
                2026,
                9,
                3,
                19,
                0,
                tzinfo=UTC,
            ),
        )


def test_multiple_records_receive_sequential_ids(
    tmp_path: Path,
) -> None:
    service = catalog_service(tmp_path)

    now = datetime(
        2026,
        9,
        3,
        19,
        0,
        tzinfo=UTC,
    )

    first = service.create_from_preview(
        pricing_preview(),
        now=now,
    )

    second_preview = replace(
        pricing_preview(),
        supplier_product_id="249691",
        supplier_sku="107082999998",
    )

    second = service.create_from_preview(
        second_preview,
        now=now,
    )

    assert first.pricing_record_id == "PRC000001"
    assert second.pricing_record_id == "PRC000002"


def test_approve_sets_explicit_business_price(
    tmp_path: Path,
) -> None:
    service = catalog_service(tmp_path)

    created = service.save_from_preview(
        pricing_preview(),
        now=datetime(
            2026,
            9,
            3,
            19,
            0,
            tzinfo=UTC,
        ),
    )

    approved = service.approve(
        created.pricing_record_id,
        approved_price=Decimal("259.99"),
        approved_by="Ryan Brown",
        approved_at=datetime(
            2026,
            9,
            3,
            20,
            0,
            tzinfo=UTC,
        ),
    )

    assert approved.pricing_record_id == "PRC000001"
    assert approved.approval_status == "APPROVED"
    assert approved.approved_price == Decimal("259.99")
    assert approved.approved_by == "Ryan Brown"

    assert approved.approved_at == datetime(
        2026,
        9,
        3,
        20,
        0,
        tzinfo=UTC,
    )

    assert approved.updated_at == datetime(
        2026,
        9,
        3,
        20,
        0,
        tzinfo=UTC,
    )


def test_approve_requires_existing_record(
    tmp_path: Path,
) -> None:
    service = catalog_service(tmp_path)

    with pytest.raises(ServicePricingCatalogNotFoundError):
        service.approve(
            "PRC999999",
            approved_price=Decimal("259.99"),
            approved_by="Ryan Brown",
            approved_at=datetime(
                2026,
                9,
                3,
                20,
                0,
                tzinfo=UTC,
            ),
        )


def test_approve_rejects_second_approval(
    tmp_path: Path,
) -> None:
    service = catalog_service(tmp_path)

    created = service.save_from_preview(
        pricing_preview(),
        now=datetime(
            2026,
            9,
            3,
            19,
            0,
            tzinfo=UTC,
        ),
    )

    service.approve(
        created.pricing_record_id,
        approved_price=Decimal("259.99"),
        approved_by="Ryan Brown",
        approved_at=datetime(
            2026,
            9,
            3,
            20,
            0,
            tzinfo=UTC,
        ),
    )

    with pytest.raises(ServicePricingCatalogApprovalError):
        service.approve(
            created.pricing_record_id,
            approved_price=Decimal("249.99"),
            approved_by="Ryan Brown",
            approved_at=datetime(
                2026,
                9,
                3,
                21,
                0,
                tzinfo=UTC,
            ),
        )


@pytest.mark.parametrize(
    "approved_price",
    [
        Decimal("0"),
        Decimal("-1.00"),
        Decimal("NaN"),
        Decimal("Infinity"),
    ],
)
def test_approve_rejects_invalid_price(
    tmp_path: Path,
    approved_price: Decimal,
) -> None:
    service = catalog_service(tmp_path)

    created = service.save_from_preview(pricing_preview())

    with pytest.raises(ServicePricingCatalogValidationError):
        service.approve(
            created.pricing_record_id,
            approved_price=approved_price,
            approved_by="Ryan Brown",
            approved_at=datetime(
                2026,
                9,
                3,
                20,
                0,
                tzinfo=UTC,
            ),
        )


def test_approve_requires_approver(
    tmp_path: Path,
) -> None:
    service = catalog_service(tmp_path)

    created = service.save_from_preview(pricing_preview())

    with pytest.raises(ServicePricingCatalogValidationError):
        service.approve(
            created.pricing_record_id,
            approved_price=Decimal("259.99"),
            approved_by="   ",
            approved_at=datetime(
                2026,
                9,
                3,
                20,
                0,
                tzinfo=UTC,
            ),
        )


def test_approve_rejects_naive_timestamp(
    tmp_path: Path,
) -> None:
    service = catalog_service(tmp_path)

    created = service.save_from_preview(pricing_preview())

    with pytest.raises(ServicePricingCatalogValidationError):
        service.approve(
            created.pricing_record_id,
            approved_price=Decimal("259.99"),
            approved_by="Ryan Brown",
            approved_at=datetime(
                2026,
                9,
                3,
                20,
                0,
            ),
        )
