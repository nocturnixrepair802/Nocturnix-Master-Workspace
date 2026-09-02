from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from integrations.mobilesentrix.client import (
    MobileSentrixClient,
)

# Known Mobile Sentrix product from earlier testing.
PRODUCT_ID = "78664"
EXPECTED_SKU = "107082069101"


def main() -> None:
    client = MobileSentrixClient()

    base_url = client.oauth.base_url.rstrip("/")
    url = f"{base_url}/api/rest/products/{PRODUCT_ID}"

    print()
    print("Mobile Sentrix Detailed Product Test")
    print("------------------------------------")
    print("Base URL:", client.oauth.base_url)
    print("Product ID:", PRODUCT_ID)
    print("Expected SKU:", EXPECTED_SKU)
    print("Endpoint:", url)
    print()

    request = Request(
        url,
        headers={
            "Authorization": client._authorization_header(),
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
        },
        method="GET",
    )

    try:
        with urlopen(
            request,
            timeout=30,
        ) as response:
            status_code = response.status

            response_body = response.read().decode(
                "utf-8",
                errors="replace",
            )

    except HTTPError as exc:
        response_body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        print("HTTP REQUEST: FAILED")
        print("HTTP status:", exc.code)
        print()
        print("Response:")
        print(response_body[:5000])
        return

    except URLError as exc:
        print("CONNECTION FAILED")
        print("Reason:", exc.reason)
        return

    print("HTTP REQUEST: SUCCESS")
    print("HTTP status:", status_code)
    print()

    try:
        result = json.loads(response_body)

    except json.JSONDecodeError:
        print("Mobile Sentrix returned a non-JSON response.")
        print()
        print(response_body[:5000])
        return

    print("RESPONSE TYPE")
    print("-------------")
    print(type(result).__name__)
    print()

    if not isinstance(result, dict):
        print("Unexpected response structure.")
        print()
        print(
            json.dumps(
                result,
                indent=2,
                default=str,
            )[:10000]
        )
        return

    print("CORE PRODUCT DATA")
    print("-----------------")

    core_fields = [
        "entity_id",
        "product_id",
        "sku",
        "product_code",
        "new_sku",
        "name",
        "title",
        "status",
        "price",
        "customer_price",
        "is_saleable",
        "is_in_stock",
        "in_stock_qty",
        "quantity",
        "updated_at",
    ]

    for field in core_fields:
        print(
            f"{field}:",
            result.get(field),
        )

    print()
    print("PRODUCT CLASSIFICATION")
    print("----------------------")

    classification_fields = [
        "manufacturer",
        "manufacturer_text",
        "model",
        "model_text",
        "front_position",
        "front_position_text",
        "premium",
        "end_of_life",
        "warranty_period",
        "product_badges",
        "product_badges_text",
        "attribute_set_id",
        "attribute_set",
    ]

    for field in classification_fields:
        print(
            f"{field}:",
            result.get(field),
        )

    print()
    print("CATEGORY DATA")
    print("-------------")
    print(
        "category_ids:",
        result.get("category_ids"),
    )

    print()
    print("RELATED PRODUCT DATA")
    print("--------------------")
    print(
        "related_product:",
        result.get("related_product"),
    )

    print()
    print("PHYSICAL / IDENTIFIER DATA")
    print("--------------------------")

    physical_fields = [
        "weight",
        "barcode",
        "hst_code",
        "hst_description",
        "color",
    ]

    for field in physical_fields:
        print(
            f"{field}:",
            result.get(field),
        )

    print()
    print("BATTERY DATA")
    print("------------")

    battery_fields = [
        "battery_volt",
        "battery_mah",
        "battery_wh",
    ]

    for field in battery_fields:
        print(
            f"{field}:",
            result.get(field),
        )

    print()
    print("DEVICE DATA")
    print("-----------")

    device_fields = [
        "device_manufacturer",
        "device_manufacturer_text",
        "device_model",
        "device_model_text",
        "device_carrier",
        "device_carrier_text",
        "device_size",
        "device_size_text",
        "device_color",
        "device_color_text",
        "device_grade",
        "device_grade_text",
    ]

    for field in device_fields:
        print(
            f"{field}:",
            result.get(field),
        )

    print()
    print("URL / IMAGE DATA")
    print("----------------")

    url_fields = [
        "url",
        "product_url",
        "image_url",
        "default_image",
    ]

    for field in url_fields:
        print(
            f"{field}:",
            result.get(field),
        )

    print()
    print("FIELD INVENTORY")
    print("---------------")

    for field in sorted(result.keys()):
        print(field)

    print()
    print(
        "Total fields returned:",
        len(result),
    )

    returned_sku = result.get("sku") or result.get("product_code")

    print()
    print("VALIDATION")
    print("----------")
    print(
        "Returned SKU:",
        returned_sku,
    )
    print(
        "Expected SKU:",
        EXPECTED_SKU,
    )

    if returned_sku is not None and str(returned_sku).strip() == EXPECTED_SKU:
        print("SKU validation: PASS")
    else:
        print("SKU validation: REVIEW")

    if result.get("in_stock_qty") is not None:
        print("Real stock quantity field: AVAILABLE")
        print(
            "in_stock_qty:",
            result.get("in_stock_qty"),
        )
    else:
        print("Real stock quantity field: NOT RETURNED")

    print()
    print("RAW RESPONSE")
    print("------------")
    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )

    print()
    print("Detailed product test complete.")


if __name__ == "__main__":
    main()
