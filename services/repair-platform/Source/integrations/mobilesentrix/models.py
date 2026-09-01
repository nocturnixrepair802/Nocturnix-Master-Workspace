from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True, slots=True)
class MobileSentrixProduct:
    """
    Normalized Mobile Sentrix search-product result.

    Endpoint:

        GET /api/rest/searchproduct

    Important:

        quantity is treated as Mobile Sentrix's documented binary
        availability indicator:

            1 = In Stock
            0 = Out of Stock

        It is NOT treated as literal inventory quantity.

        Real inventory quantity, when supplied by Mobile Sentrix,
        comes from the detailed-product field:

            in_stock_qty
    """

    supplier: str

    supplier_product_id: str | None
    supplier_sku: str | None
    new_sku: str | None

    name: str | None
    description: str | None

    unit_cost: Decimal | None
    list_price: Decimal | None

    in_stock: bool | None

    product_url: str | None
    image_url: str | None

    tags: str | None
    front_position: str | None

    @classmethod
    def from_api_item(
        cls,
        item: dict[str, Any],
    ) -> "MobileSentrixProduct":
        """
        Convert a /searchproduct API item into the normalized
        Nocturnix representation.
        """

        quantity = _to_integer(item.get("quantity"))

        if quantity is None:
            in_stock: bool | None = None

        elif quantity == 1:
            in_stock = True

        elif quantity == 0:
            in_stock = False

        else:
            in_stock = None

        return cls(
            supplier="Mobile Sentrix",
            supplier_product_id=_to_string(item.get("product_id")),
            supplier_sku=_to_string(item.get("product_code")),
            new_sku=_to_string(item.get("new_sku")),
            name=_to_string(item.get("title")),
            description=_to_string(item.get("description")),
            unit_cost=_to_decimal(item.get("price")),
            list_price=_to_decimal(item.get("list_price")),
            in_stock=in_stock,
            product_url=_to_string(item.get("link")),
            image_url=_to_string(item.get("image_link")),
            tags=_to_string(item.get("tags")),
            front_position=_to_string(item.get("front_position")),
        )

    def to_api_dict(
        self,
    ) -> dict[str, object]:
        """
        Return a JSON-safe representation.
        """

        data = asdict(self)

        data["unit_cost"] = str(self.unit_cost) if self.unit_cost is not None else None

        data["list_price"] = (
            str(self.list_price) if self.list_price is not None else None
        )

        return data


@dataclass(frozen=True, slots=True)
class MobileSentrixDetailedProduct:
    """
    Normalized detailed Mobile Sentrix product.

    Endpoint:

        GET /api/rest/products/{entity_id}

    This model is intentionally separate from MobileSentrixProduct
    because the detailed endpoint exposes richer supplier data and
    uses different inventory semantics.
    """

    supplier: str

    entity_id: str | None
    sku: str | None
    new_sku: str | None

    name: str | None
    description: str | None

    customer_price: Decimal | None

    status: str | None
    is_saleable: bool | None

    is_in_stock: bool | None
    in_stock_qty: int | None

    manufacturer_id: str | None
    manufacturer_text: str | None

    model_ids: tuple[str, ...]
    model_names: tuple[str, ...]

    category_ids: tuple[str, ...]

    premium: bool | None
    end_of_life: bool | None

    warranty_period_id: str | None

    product_badges: tuple[str, ...]
    product_badges_text: tuple[str, ...]

    related_product_ids: tuple[str, ...]

    weight: Decimal | None
    color: str | None
    barcode: str | None

    battery_volt: Decimal | None
    battery_mah: Decimal | None
    battery_wh: Decimal | None

    product_url: str | None
    image_url: str | None

    updated_at: str | None

    device_manufacturer_id: str | None
    device_manufacturer_text: str | None

    device_model_ids: tuple[str, ...]
    device_model_names: tuple[str, ...]

    device_carrier_ids: tuple[str, ...]
    device_carrier_names: tuple[str, ...]

    device_size_ids: tuple[str, ...]
    device_size_names: tuple[str, ...]

    device_color_ids: tuple[str, ...]
    device_color_names: tuple[str, ...]

    device_grade_ids: tuple[str, ...]
    device_grade_names: tuple[str, ...]

    @classmethod
    def from_api_item(
        cls,
        item: dict[str, Any],
    ) -> "MobileSentrixDetailedProduct":
        """
        Convert a detailed /products/{entity_id} response into the
        normalized Nocturnix representation.
        """

        return cls(
            supplier="Mobile Sentrix",
            entity_id=_to_string(item.get("entity_id") or item.get("product_id")),
            sku=_to_string(item.get("sku") or item.get("product_code")),
            new_sku=_to_string(item.get("new_sku")),
            name=_to_string(item.get("name") or item.get("title")),
            description=_to_string(item.get("description")),
            customer_price=_to_decimal(
                item.get("customer_price")
                if item.get("customer_price") is not None
                else item.get("price")
            ),
            status=_to_string(item.get("status")),
            is_saleable=_to_boolean(item.get("is_saleable")),
            is_in_stock=_to_boolean(item.get("is_in_stock")),
            in_stock_qty=_to_integer(item.get("in_stock_qty")),
            manufacturer_id=_to_string(item.get("manufacturer")),
            manufacturer_text=_to_string(item.get("manufacturer_text")),
            model_ids=_to_string_tuple(item.get("model")),
            model_names=_to_string_tuple(item.get("model_text")),
            category_ids=_to_string_tuple(item.get("category_ids")),
            premium=_to_boolean(item.get("premium")),
            end_of_life=_to_boolean(item.get("end_of_life")),
            warranty_period_id=_to_string(item.get("warranty_period")),
            product_badges=_to_string_tuple(item.get("product_badges")),
            product_badges_text=_to_string_tuple(item.get("product_badges_text")),
            related_product_ids=_to_string_tuple(item.get("related_product")),
            weight=_to_decimal(item.get("weight")),
            color=_to_string(item.get("color")),
            barcode=_to_string(item.get("barcode")),
            battery_volt=_to_decimal(item.get("battery_volt")),
            battery_mah=_to_decimal(item.get("battery_mah")),
            battery_wh=_to_decimal(item.get("battery_wh")),
            product_url=_to_string(item.get("url") or item.get("product_url")),
            image_url=_to_string(item.get("image_url") or item.get("default_image")),
            updated_at=_to_string(item.get("updated_at")),
            device_manufacturer_id=_to_string(item.get("device_manufacturer")),
            device_manufacturer_text=_to_string(item.get("device_manufacturer_text")),
            device_model_ids=_to_string_tuple(item.get("device_model")),
            device_model_names=_to_string_tuple(item.get("device_model_text")),
            device_carrier_ids=_to_string_tuple(item.get("device_carrier")),
            device_carrier_names=_to_string_tuple(item.get("device_carrier_text")),
            device_size_ids=_to_string_tuple(item.get("device_size")),
            device_size_names=_to_string_tuple(item.get("device_size_text")),
            device_color_ids=_to_string_tuple(item.get("device_color")),
            device_color_names=_to_string_tuple(item.get("device_color_text")),
            device_grade_ids=_to_string_tuple(item.get("device_grade")),
            device_grade_names=_to_string_tuple(item.get("device_grade_text")),
        )

    def to_api_dict(
        self,
    ) -> dict[str, object]:
        """
        Return a JSON-safe representation of the detailed product.
        """

        data = asdict(self)

        decimal_fields = (
            "customer_price",
            "weight",
            "battery_volt",
            "battery_mah",
            "battery_wh",
        )

        for field_name in decimal_fields:
            value = data[field_name]

            data[field_name] = str(value) if value is not None else None

        return data


def _to_string(
    value: object,
) -> str | None:
    """
    Normalize an API value into a stripped string.

    Empty values become None.
    """

    if value is None:
        return None

    text = str(value).strip()

    return text or None


def _to_decimal(
    value: object,
) -> Decimal | None:
    """
    Normalize a monetary or numeric API value into Decimal.
    """

    if value is None:
        return None

    if isinstance(
        value,
        Decimal,
    ):
        return value

    text = str(value).strip()

    if not text:
        return None

    text = text.replace("$", "").replace(",", "").strip()

    try:
        return Decimal(text)

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        return None


def _to_integer(
    value: object,
) -> int | None:
    """
    Normalize an integer-like API value.
    """

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return int(value)

    if isinstance(
        value,
        int,
    ):
        return value

    if isinstance(
        value,
        float,
    ):
        if value.is_integer():
            return int(value)

        return None

    text = str(value).strip()

    if not text:
        return None

    try:
        decimal_value = Decimal(text)

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        return None

    if decimal_value != decimal_value.to_integral_value():
        return None

    return int(decimal_value)


def _to_boolean(
    value: object,
) -> bool | None:
    """
    Normalize common Mobile Sentrix boolean-like values.

    Recognized true values:

        True
        1
        "1"
        "true"
        "yes"

    Recognized false values:

        False
        0
        "0"
        "false"
        "no"
    """

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        int,
    ):
        if value == 1:
            return True

        if value == 0:
            return False

        return None

    text = str(value).strip().lower()

    if text in {
        "1",
        "true",
        "yes",
    }:
        return True

    if text in {
        "0",
        "false",
        "no",
    }:
        return False

    return None


def _to_string_tuple(
    value: object,
) -> tuple[str, ...]:
    """
    Normalize Mobile Sentrix scalar/list/comma-separated values into
    an immutable tuple of non-empty strings.
    """

    if value is None:
        return ()

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        values: list[str] = []

        for item in value:
            normalized = _to_string(item)

            if normalized is not None:
                values.append(normalized)

        return tuple(values)

    text = _to_string(value)

    if text is None:
        return ()

    if "," not in text:
        return (text,)

    return tuple(part.strip() for part in text.split(",") if part.strip())
