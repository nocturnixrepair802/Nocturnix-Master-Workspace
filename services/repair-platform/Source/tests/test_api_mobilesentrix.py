from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

SOURCE_DIR = Path(__file__).resolve().parents[1]

if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(SOURCE_DIR),
    )

from api import app as api_app_module
from api.app import app
from integrations.mobilesentrix import (
    MobileSentrixApiError,
)


class FakeOAuth:
    def status(
        self,
    ) -> dict[str, object]:
        return {
            "environment": "test",
            "authorized": True,
        }


class FakeMobileSentrixClient:
    def __init__(
        self,
    ) -> None:
        self.oauth = FakeOAuth()

    def search_products(
      self,
      *,
      query: str,
      max_results: int = 10,
      start_index: int = 0,
    ) -> dict[str, Any]:
        return {
            "data": {
                "total_items": 1,
                "items": [
                    {
                        "product_id": "249690",
                        "product_code": "107182127725",
                        "new_sku": None,
                        "title": (
                            "iHeater Pro Desoldering Station "
                            "4th Gen"
                        ),
                        "description": (
                            "Test Mobile Sentrix search product."
                        ),
                        "price": "351.04",
                        "list_price": "399.99",
                        "quantity": 1,
                        "link": (
                            "https://www.mobilesentrix.com/"
                            "test-product"
                        ),
                        "image_link": (
                            "https://www.mobilesentrix.com/"
                            "test-image.jpg"
                        ),
                        "tags": "test",
                        "front_position": "1",
                    }
                ],
            }
        }

    def get_product(
        self,
        *,
        product_id: str | int,
    ) -> dict[str, Any]:
        return {
            "entity_id": str(product_id),
            "sku": "107182127725",
            "new_sku": None,
            "name": ("iHeater Pro Desoldering Station " "4th Gen"),
            "description": ("Test Mobile Sentrix product."),
            "customer_price": "351.04",
            "status": "1",
            "is_saleable": True,
            "is_in_stock": True,
            "in_stock_qty": 3,
            "manufacturer": "Aixun",
            "manufacturer_text": "Aixun",
            "model": [],
            "model_text": [],
            "category_ids": ["123"],
            "premium": False,
            "end_of_life": False,
            "warranty_period": "12",
            "product_badges": [],
            "product_badges_text": [],
            "related_product": [],
            "weight": "1.25",
            "color": None,
            "barcode": None,
            "battery_volt": None,
            "battery_mah": None,
            "battery_wh": None,
            "url": ("https://www.mobilesentrix.com/" "test-product"),
            "image_url": ("https://www.mobilesentrix.com/" "test-image.jpg"),
            "updated_at": ("2026-09-01T00:00:00Z"),
            "device_manufacturer": None,
            "device_manufacturer_text": None,
            "device_model": [],
            "device_model_text": [],
            "device_carrier": [],
            "device_carrier_text": [],
            "device_size": [],
            "device_size_text": [],
            "device_color": [],
            "device_color_text": [],
            "device_grade": [],
            "device_grade_text": [],
        }


class FailingMobileSentrixClient:
    def __init__(
        self,
    ) -> None:
        self.oauth = FakeOAuth()

    def search_products(
        self,
        *,
        query: str,
        max_results: int = 10,
        start_index: int = 0,
    ) -> dict[str, Any]:
        raise MobileSentrixApiError("simulated Mobile Sentrix search failure")

    def get_product(
        self,
        *,
        product_id: str | int,
    ) -> dict[str, Any]:
        raise MobileSentrixApiError("simulated Mobile Sentrix detail failure")


def test_mobilesentrix_product_search(
    monkeypatch,
) -> None:
    fake_client = FakeMobileSentrixClient()

    monkeypatch.setattr(
        api_app_module,
        "get_mobilesentrix_client",
        lambda: fake_client,
    )

    client = TestClient(app)

    response = client.get(
        "/api/v1/integrations/" "mobilesentrix/products/search",
        params={
            "q": "iHeater",
            "max_results": 10,
            "start_index": 0,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["query"] == "iHeater"

    assert payload["environment"] == "test"

    assert payload["total_items"] == 1

    assert payload["returned_items"] == 1

    assert len(payload["items"]) == 1

    product = payload["items"][0]

    assert product["supplier"] == "Mobile Sentrix"

    assert product["supplier_product_id"] == "249690"

    assert product["supplier_sku"] == "107182127725"

    assert product["name"] == ("iHeater Pro Desoldering Station " "4th Gen")

    assert product["unit_cost"] == "351.04"

    assert product["list_price"] == "399.99"

    assert product["in_stock"] is True


def test_mobilesentrix_product_search_requires_query() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/integrations/" "mobilesentrix/products/search")

    assert response.status_code == 422


def test_mobilesentrix_product_search_upstream_error(
    monkeypatch,
) -> None:
    fake_client = FailingMobileSentrixClient()

    monkeypatch.setattr(
        api_app_module,
        "get_mobilesentrix_client",
        lambda: fake_client,
    )

    client = TestClient(app)

    response = client.get(
        "/api/v1/integrations/" "mobilesentrix/products/search",
        params={"q": "iPhone"},
    )

    assert response.status_code == 502

    payload = response.json()

    assert payload["detail"] == (
        "Mobile Sentrix returned an " "upstream service error."
    )


def test_mobilesentrix_product_detail(
    monkeypatch,
) -> None:
    fake_client = FakeMobileSentrixClient()

    monkeypatch.setattr(
        api_app_module,
        "get_mobilesentrix_client",
        lambda: fake_client,
    )

    client = TestClient(app)

    response = client.get("/api/v1/integrations/" "mobilesentrix/products/249690")

    assert response.status_code == 200

    payload = response.json()

    assert payload["supplier"] == "Mobile Sentrix"

    assert payload["entity_id"] == "249690"

    assert payload["sku"] == "107182127725"

    assert payload["name"] == ("iHeater Pro Desoldering " "Station 4th Gen")

    assert payload["customer_price"] == "351.04"

    assert payload["is_saleable"] is True

    assert payload["is_in_stock"] is True

    assert payload["in_stock_qty"] == 3

    assert payload["end_of_life"] is False

    assert payload["category_ids"] == ["123"]


def test_mobilesentrix_product_detail_upstream_error(
    monkeypatch,
) -> None:
    fake_client = FailingMobileSentrixClient()

    monkeypatch.setattr(
        api_app_module,
        "get_mobilesentrix_client",
        lambda: fake_client,
    )

    client = TestClient(app)

    response = client.get("/api/v1/integrations/" "mobilesentrix/products/249690")

    assert response.status_code == 502

    payload = response.json()

    assert payload["detail"] == (
        "Mobile Sentrix returned an " "upstream service error."
    )


class ClassifiedFailureClient:
    def __init__(
        self,
        error: MobileSentrixApiError,
    ) -> None:
        self.oauth = FakeOAuth()
        self.error = error

    def get_product(
        self,
        *,
        product_id: str | int,
    ) -> dict[str, Any]:
        raise self.error


def test_mobilesentrix_product_detail_not_found(
    monkeypatch,
) -> None:
    fake_client = ClassifiedFailureClient(
        MobileSentrixApiError(
            "supplier 404",
            status_code=404,
        )
    )

    monkeypatch.setattr(
        api_app_module,
        "get_mobilesentrix_client",
        lambda: fake_client,
    )

    client = TestClient(app)

    response = client.get("/api/v1/integrations/" "mobilesentrix/products/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == ("Mobile Sentrix product was not found.")


def test_mobilesentrix_product_detail_timeout(
    monkeypatch,
) -> None:
    fake_client = ClassifiedFailureClient(
        MobileSentrixApiError(
            "supplier timeout",
            timed_out=True,
        )
    )

    monkeypatch.setattr(
        api_app_module,
        "get_mobilesentrix_client",
        lambda: fake_client,
    )

    client = TestClient(app)

    response = client.get("/api/v1/integrations/" "mobilesentrix/products/249690")

    assert response.status_code == 504


def test_mobilesentrix_product_detail_rate_limit(
    monkeypatch,
) -> None:
    fake_client = ClassifiedFailureClient(
        MobileSentrixApiError(
            "supplier rate limit",
            status_code=429,
        )
    )

    monkeypatch.setattr(
        api_app_module,
        "get_mobilesentrix_client",
        lambda: fake_client,
    )

    client = TestClient(app)

    response = client.get("/api/v1/integrations/" "mobilesentrix/products/249690")

    assert response.status_code == 503


def test_mobilesentrix_product_detail_authentication_failure(
    monkeypatch,
) -> None:
    fake_client = ClassifiedFailureClient(
        MobileSentrixApiError(
            "supplier authentication failure",
            status_code=401,
        )
    )

    monkeypatch.setattr(
        api_app_module,
        "get_mobilesentrix_client",
        lambda: fake_client,
    )

    client = TestClient(app)

    response = client.get("/api/v1/integrations/" "mobilesentrix/products/249690")

    assert response.status_code == 502


def test_mobilesentrix_product_detail_connection_failure(
    monkeypatch,
) -> None:
    fake_client = ClassifiedFailureClient(
        MobileSentrixApiError(
            "supplier unavailable",
            connection_failed=True,
        )
    )

    monkeypatch.setattr(
        api_app_module,
        "get_mobilesentrix_client",
        lambda: fake_client,
    )

    client = TestClient(app)

    response = client.get("/api/v1/integrations/" "mobilesentrix/products/249690")

    assert response.status_code == 503
