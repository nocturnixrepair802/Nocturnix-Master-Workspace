from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.config import Settings

OWNER_HEADERS = {"X-Nocturnix-Dev-User": "repair-owner-001"}
OTHER_HEADERS = {"X-Nocturnix-Dev-User": "repair-owner-002"}


@pytest.fixture
def repair_client(tmp_path: Path):
    app = create_app(
        Settings(
            database_url=f"sqlite:///{tmp_path / 'repair_pricing_policies.db'}",
            database_migration_mode="auto-test-only",
            auth_mode="development_header",
            allow_development_header_auth=True,
            rate_limit_per_minute=500,
        )
    )

    with TestClient(app) as client:
        yield client

    cast(Any, app).state.container.engine.dispose()


def pricing_policy_payload(
    *,
    name: str = "Standard Repair Pricing",
    labor_rate_cents_per_hour: int = 12500,
    processing_fee_cents: int = 350,
    overhead_basis_points: int = 1200,
    markup_basis_points: int = 2500,
    currency: str = "usd",
    is_default: bool = True,
    effective_at: str = "2026-07-29T12:00:00Z",
) -> dict[str, Any]:
    return {
        "name": name,
        "labor_rate_cents_per_hour": labor_rate_cents_per_hour,
        "processing_fee_cents": processing_fee_cents,
        "overhead_basis_points": overhead_basis_points,
        "markup_basis_points": markup_basis_points,
        "currency": currency,
        "is_default": is_default,
        "effective_at": effective_at,
    }


def create_pricing_policy(
    client: TestClient,
    *,
    headers: dict[str, str] = OWNER_HEADERS,
    **overrides: Any,
) -> dict[str, Any]:
    payload = pricing_policy_payload(**overrides)

    response = client.post(
        "/api/v1/repair/pricing-policies",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_pricing_policy_crud_and_default_management(
    repair_client: TestClient,
) -> None:
    first_policy = create_pricing_policy(repair_client)

    assert first_policy["owner_user_id"] == "repair-owner-001"
    assert first_policy["name"] == "Standard Repair Pricing"
    assert first_policy["labor_rate_cents_per_hour"] == 12500
    assert first_policy["processing_fee_cents"] == 350
    assert first_policy["overhead_basis_points"] == 1200
    assert first_policy["markup_basis_points"] == 2500
    assert first_policy["currency"] == "USD"
    assert first_policy["is_default"] is True
    assert first_policy["id"].startswith("price_")
    assert first_policy["created_at"]
    assert first_policy["updated_at"]

    first_policy_id = first_policy["id"]

    get_response = repair_client.get(
        f"/api/v1/repair/pricing-policies/{first_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert get_response.status_code == 200, get_response.text
    assert get_response.json()["id"] == first_policy_id

    default_response = repair_client.get(
        "/api/v1/repair/pricing-policies/default",
        headers=OWNER_HEADERS,
    )
    assert default_response.status_code == 200, default_response.text
    assert default_response.json()["id"] == first_policy_id

    second_policy = create_pricing_policy(
        repair_client,
        name="Premium Repair Pricing",
        labor_rate_cents_per_hour=17500,
        processing_fee_cents=500,
        overhead_basis_points=1500,
        markup_basis_points=3000,
        currency="eur",
        is_default=False,
        effective_at="2026-08-01T09:30:00Z",
    )

    second_policy_id = second_policy["id"]
    assert second_policy["currency"] == "EUR"
    assert second_policy["is_default"] is False

    list_response = repair_client.get(
        "/api/v1/repair/pricing-policies",
        headers=OWNER_HEADERS,
    )
    assert list_response.status_code == 200, list_response.text

    listed = list_response.json()
    assert listed["total"] == 2
    assert len(listed["items"]) == 2
    assert listed["items"][0]["id"] == first_policy_id
    assert listed["items"][0]["is_default"] is True

    update_response = repair_client.patch(
        f"/api/v1/repair/pricing-policies/{second_policy_id}",
        headers=OWNER_HEADERS,
        json={
            "name": "  Premium Default Pricing  ",
            "labor_rate_cents_per_hour": 18500,
            "processing_fee_cents": 625,
            "overhead_basis_points": 1800,
            "markup_basis_points": 3250,
            "currency": "cad",
            "is_default": True,
            "effective_at": "2026-08-15T10:00:00Z",
        },
    )
    assert update_response.status_code == 200, update_response.text

    updated = update_response.json()
    assert updated["id"] == second_policy_id
    assert updated["name"] == "Premium Default Pricing"
    assert updated["labor_rate_cents_per_hour"] == 18500
    assert updated["processing_fee_cents"] == 625
    assert updated["overhead_basis_points"] == 1800
    assert updated["markup_basis_points"] == 3250
    assert updated["currency"] == "CAD"
    assert updated["is_default"] is True

    new_default_response = repair_client.get(
        "/api/v1/repair/pricing-policies/default",
        headers=OWNER_HEADERS,
    )
    assert new_default_response.status_code == 200, new_default_response.text
    assert new_default_response.json()["id"] == second_policy_id

    first_after_update_response = repair_client.get(
        f"/api/v1/repair/pricing-policies/{first_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert first_after_update_response.status_code == 200
    assert first_after_update_response.json()["is_default"] is False

    reordered_list_response = repair_client.get(
        "/api/v1/repair/pricing-policies",
        headers=OWNER_HEADERS,
    )
    assert reordered_list_response.status_code == 200

    reordered = reordered_list_response.json()
    assert reordered["total"] == 2
    assert reordered["items"][0]["id"] == second_policy_id
    assert reordered["items"][0]["is_default"] is True

    delete_response = repair_client.delete(
        f"/api/v1/repair/pricing-policies/{first_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert delete_response.status_code == 204, delete_response.text

    deleted_get_response = repair_client.get(
        f"/api/v1/repair/pricing-policies/{first_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert deleted_get_response.status_code == 404

    final_list_response = repair_client.get(
        "/api/v1/repair/pricing-policies",
        headers=OWNER_HEADERS,
    )
    assert final_list_response.status_code == 200

    final_list = final_list_response.json()
    assert final_list["total"] == 1
    assert final_list["items"][0]["id"] == second_policy_id


def test_pricing_policy_owner_isolation_and_missing_resources(
    repair_client: TestClient,
) -> None:
    missing_default_response = repair_client.get(
        "/api/v1/repair/pricing-policies/default",
        headers=OWNER_HEADERS,
    )
    assert missing_default_response.status_code == 404

    owner_policy = create_pricing_policy(repair_client)
    owner_policy_id = owner_policy["id"]

    other_owner_list_response = repair_client.get(
        "/api/v1/repair/pricing-policies",
        headers=OTHER_HEADERS,
    )
    assert other_owner_list_response.status_code == 200
    assert other_owner_list_response.json() == {"items": [], "total": 0}

    other_owner_get_response = repair_client.get(
        f"/api/v1/repair/pricing-policies/{owner_policy_id}",
        headers=OTHER_HEADERS,
    )
    assert other_owner_get_response.status_code == 404

    other_owner_default_response = repair_client.get(
        "/api/v1/repair/pricing-policies/default",
        headers=OTHER_HEADERS,
    )
    assert other_owner_default_response.status_code == 404

    other_owner_update_response = repair_client.patch(
        f"/api/v1/repair/pricing-policies/{owner_policy_id}",
        headers=OTHER_HEADERS,
        json={"name": "Unauthorized Change"},
    )
    assert other_owner_update_response.status_code == 404

    other_owner_delete_response = repair_client.delete(
        f"/api/v1/repair/pricing-policies/{owner_policy_id}",
        headers=OTHER_HEADERS,
    )
    assert other_owner_delete_response.status_code == 404

    missing_policy_id = "price_does_not_exist"

    missing_get_response = repair_client.get(
        f"/api/v1/repair/pricing-policies/{missing_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert missing_get_response.status_code == 404

    missing_update_response = repair_client.patch(
        f"/api/v1/repair/pricing-policies/{missing_policy_id}",
        headers=OWNER_HEADERS,
        json={"name": "Missing Policy"},
    )
    assert missing_update_response.status_code == 404

    missing_delete_response = repair_client.delete(
        f"/api/v1/repair/pricing-policies/{missing_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert missing_delete_response.status_code == 404

    owner_get_response = repair_client.get(
        f"/api/v1/repair/pricing-policies/{owner_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert owner_get_response.status_code == 200
    assert owner_get_response.json()["name"] == "Standard Repair Pricing"


def test_pricing_policy_validation_and_authentication(
    repair_client: TestClient,
) -> None:
    unauthenticated_list_response = repair_client.get(
        "/api/v1/repair/pricing-policies",
    )
    assert unauthenticated_list_response.status_code in {401, 403}

    unauthenticated_create_response = repair_client.post(
        "/api/v1/repair/pricing-policies",
        json=pricing_policy_payload(),
    )
    assert unauthenticated_create_response.status_code in {401, 403}

    empty_name_response = repair_client.post(
        "/api/v1/repair/pricing-policies",
        headers=OWNER_HEADERS,
        json=pricing_policy_payload(name="   "),
    )
    assert empty_name_response.status_code == 422

    invalid_currency_response = repair_client.post(
        "/api/v1/repair/pricing-policies",
        headers=OWNER_HEADERS,
        json=pricing_policy_payload(currency="12$"),
    )
    assert invalid_currency_response.status_code == 422

    negative_labor_rate_response = repair_client.post(
        "/api/v1/repair/pricing-policies",
        headers=OWNER_HEADERS,
        json=pricing_policy_payload(labor_rate_cents_per_hour=-1),
    )
    assert negative_labor_rate_response.status_code == 422

    invalid_effective_at_response = repair_client.post(
        "/api/v1/repair/pricing-policies",
        headers=OWNER_HEADERS,
        json=pricing_policy_payload(effective_at="not-a-date"),
    )
    assert invalid_effective_at_response.status_code == 422

    valid_policy = create_pricing_policy(repair_client)
    policy_id = valid_policy["id"]

    empty_update_name_response = repair_client.patch(
        f"/api/v1/repair/pricing-policies/{policy_id}",
        headers=OWNER_HEADERS,
        json={"name": "   "},
    )
    assert empty_update_name_response.status_code == 422

    invalid_update_currency_response = repair_client.patch(
        f"/api/v1/repair/pricing-policies/{policy_id}",
        headers=OWNER_HEADERS,
        json={"currency": "1US"},
    )
    assert invalid_update_currency_response.status_code == 422

    negative_update_fee_response = repair_client.patch(
        f"/api/v1/repair/pricing-policies/{policy_id}",
        headers=OWNER_HEADERS,
        json={"processing_fee_cents": -1},
    )
    assert negative_update_fee_response.status_code == 422
