from decimal import Decimal

import pytest

from integrations.mobilesentrix.models import (
    MobileSentrixDetailedProduct,
    MobileSentrixProduct,
)
from models.service_pricing import ServicePricingRule
from services.service_pricing_service import (
    ServicePricingNotFoundError,
    ServicePricingService,
    ServicePricingValidationError,
)


class FakeCatalogDatabase:
    def __init__(self) -> None:
        self.devices = {
            "DEV000093": {
                "device_id": "DEV000093",
                "device_type_id": "DTY000001",
                "manufacturer_id": "MFR000001",
                "manufacturer": "Apple",
                "device_family_id": "DFM000001",
                "device_family": "",
                "device_model_id": "",
                "device_model": "iPhone 13 Pro",
                "active": True,
            }
        }

    def get_device(
        self,
        device_id: str,
    ) -> dict[str, object] | None:
        return self.devices.get(device_id)


def screen_rule() -> ServicePricingRule:
    return ServicePricingRule(
        service_type_id="STY000001",
        service_type="Screen Replacement",
        service_category_id="SC000010",
        default_labor_hours=Decimal("1.00"),
        labor_profile_id="LAB000002",
        labor_tier="L2 Standard",
        hourly_rate=Decimal("100.00"),
        minimum_charge=Decimal("85.00"),
        target_margin=Decimal("0.30"),
        minimum_margin=Decimal("0.20"),
        overhead_rate=Decimal("0.12"),
        warranty_rate=Decimal("0.05"),
        risk_rate=Decimal("0.04"),
        processing_rate=Decimal("0.03"),
    )


def detailed_screen_product() -> MobileSentrixDetailedProduct:
    return MobileSentrixDetailedProduct.from_api_item(
        {
            "entity_id": "249690",
            "sku": "107082080528",
            "name": ("OLED Assembly For iPhone 13 Pro " "(Refurbished)"),
            "customer_price": "115.40",
            "status": "1",
            "is_saleable": True,
            "is_in_stock": True,
            "in_stock_qty": 3,
        }
    )


def search_screen_product() -> MobileSentrixProduct:
    return MobileSentrixProduct.from_api_item(
        {
            "product_id": "249690",
            "product_code": "107082080528",
            "name": ("OLED Assembly For iPhone 13 Pro " "(Refurbished)"),
            "price": "115.40",
            "quantity": 1,
        }
    )


def test_preview_from_detailed_product() -> None:
    service = ServicePricingService(FakeCatalogDatabase())

    result = service.preview(
        device_id="DEV000093",
        rule=screen_rule(),
        product=detailed_screen_product(),
        shipping=Decimal("10.00"),
        consumables=Decimal("5.00"),
    )

    assert result.device_id == "DEV000093"
    assert result.device_model == "iPhone 13 Pro"

    assert result.service_type_id == "STY000001"
    assert result.service_type == "Screen Replacement"

    assert result.supplier == "Mobile Sentrix"
    assert result.supplier_product_id == "249690"
    assert result.supplier_sku == "107082080528"

    assert result.part_cost == Decimal("115.40")
    assert result.supplier_in_stock is True
    assert result.supplier_stock_qty == 3

    assert result.calculated_labor_cost == Decimal("100.00")
    assert result.billable_labor_cost == Decimal("100.00")

    assert result.base_direct_cost == Decimal("230.40")

    assert result.overhead_reserve == Decimal("27.65")
    assert result.warranty_reserve == Decimal("11.52")
    assert result.risk_reserve == Decimal("9.22")
    assert result.processing_reserve == Decimal("6.91")

    assert result.total_internal_cost == Decimal("285.70")
    assert result.raw_retail_price == Decimal("408.14")
    assert result.recommended_retail_price == Decimal("408.99")

    assert result.gross_profit == Decimal("123.29")
    assert result.pricing_status == "READY"


def test_search_product_preserves_binary_availability() -> None:
    service = ServicePricingService(FakeCatalogDatabase())

    result = service.preview(
        device_id="DEV000093",
        rule=screen_rule(),
        product=search_screen_product(),
    )

    assert result.supplier_in_stock is True
    assert result.supplier_stock_qty is None


def test_detailed_product_preserves_literal_stock_quantity() -> None:
    service = ServicePricingService(FakeCatalogDatabase())

    result = service.preview(
        device_id="DEV000093",
        rule=screen_rule(),
        product=detailed_screen_product(),
    )

    assert result.supplier_in_stock is True
    assert result.supplier_stock_qty == 3


def test_unknown_device_is_rejected() -> None:
    service = ServicePricingService(FakeCatalogDatabase())

    with pytest.raises(
        ServicePricingNotFoundError,
        match="DEV999999",
    ):
        service.preview(
            device_id="DEV999999",
            rule=screen_rule(),
            product=detailed_screen_product(),
        )


def test_blank_device_id_is_rejected() -> None:
    service = ServicePricingService(FakeCatalogDatabase())

    with pytest.raises(
        ServicePricingValidationError,
        match="device_id",
    ):
        service.preview(
            device_id=" ",
            rule=screen_rule(),
            product=detailed_screen_product(),
        )


@pytest.mark.parametrize(
    "service_type_id",
    [
        "SVC000001",
        "STY1",
        "STYABC001",
        "",
    ],
)
def test_non_governed_service_type_id_is_rejected(
    service_type_id: str,
) -> None:
    service = ServicePricingService(FakeCatalogDatabase())

    rule = ServicePricingRule(
        service_type_id=service_type_id,
        service_type="Screen Replacement",
        service_category_id="SC000010",
        default_labor_hours=Decimal("1.00"),
        labor_profile_id="LAB000002",
        labor_tier="L2 Standard",
        hourly_rate=Decimal("100.00"),
        minimum_charge=Decimal("85.00"),
        target_margin=Decimal("0.30"),
        minimum_margin=Decimal("0.20"),
        overhead_rate=Decimal("0.12"),
        warranty_rate=Decimal("0.05"),
        risk_rate=Decimal("0.04"),
        processing_rate=Decimal("0.03"),
    )

    with pytest.raises(
        ServicePricingValidationError,
        match="STY",
    ):
        service.preview(
            device_id="DEV000093",
            rule=rule,
            product=detailed_screen_product(),
        )


def test_detailed_product_requires_price() -> None:
    product = MobileSentrixDetailedProduct.from_api_item(
        {
            "entity_id": "249690",
            "sku": "107082080528",
            "name": "Screen",
        }
    )

    service = ServicePricingService(FakeCatalogDatabase())

    with pytest.raises(
        ServicePricingValidationError,
        match="customer_price",
    ):
        service.preview(
            device_id="DEV000093",
            rule=screen_rule(),
            product=product,
        )


def test_detailed_product_requires_entity_id() -> None:
    product = MobileSentrixDetailedProduct.from_api_item(
        {
            "sku": "107082080528",
            "name": "Screen",
            "customer_price": "115.40",
        }
    )

    service = ServicePricingService(FakeCatalogDatabase())

    with pytest.raises(
        ServicePricingValidationError,
        match="entity_id",
    ):
        service.preview(
            device_id="DEV000093",
            rule=screen_rule(),
            product=product,
        )


def test_detailed_product_requires_sku() -> None:
    product = MobileSentrixDetailedProduct.from_api_item(
        {
            "entity_id": "249690",
            "name": "Screen",
            "customer_price": "115.40",
        }
    )

    service = ServicePricingService(FakeCatalogDatabase())

    with pytest.raises(
        ServicePricingValidationError,
        match="sku",
    ):
        service.preview(
            device_id="DEV000093",
            rule=screen_rule(),
            product=product,
        )
