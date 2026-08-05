from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.config import Settings

OWNER_HEADERS = {"X-Nocturnix-Dev-User": "repair-owner-001"}
OTHER_HEADERS = {"X-Nocturnix-Dev-User": "repair-owner-002"}

TAX_POLICIES_URL = "/api/v1/repair/tax-policies"


@pytest.fixture
def repair_client(tmp_path: Path):
    app = create_app(
        Settings(
            
            database_url=f"sqlite:///{tmp_path / 'repair_tax_policies.db'}",
            database_migration_mode="auto-test-only",
            auth_mode="development_header",
            allow_development_header_auth=True,
            rate_limit_per_minute=500,
        )
    )

    with TestClient(app) as client:
        yield client

    cast(Any, app).state.container.engine.dispose()


def tax_policy_payload(
    name: str = "Standard Sales Tax",
    tax_rate_basis_points: int = 725,
    is_default: bool = True,
    effective_at: str = "2026-07-29T12:00:00Z",
) -> dict[str, Any]:
    return {
        "name": name,
        "tax_rate_basis_points": tax_rate_basis_points,
        "is_default": is_default,
        "effective_at": effective_at,
    }


def create_tax_policy(
    client: TestClient,
    *,
    headers: dict[str, str] = OWNER_HEADERS,
    **overrides: Any,
) -> dict[str, Any]:
    response = client.post(
        TAX_POLICIES_URL,
        headers=headers,
        json=tax_policy_payload(**overrides),
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_tax_policy_crud_and_default_management(
    repair_client: TestClient,
) -> None:
    first_policy = create_tax_policy(repair_client)

    assert first_policy["owner_user_id"] == "repair-owner-001"
    assert first_policy["name"] == "Standard Sales Tax"
    assert first_policy["tax_rate_basis_points"] == 725
    assert first_policy["is_default"] is True
    assert first_policy["id"]
    assert first_policy["created_at"]
    assert first_policy["updated_at"]
    assert first_policy["effective_at"]

    first_policy_id = first_policy["id"]

    get_response = repair_client.get(
        f"{TAX_POLICIES_URL}/{first_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert get_response.status_code == 200, get_response.text

    retrieved = get_response.json()
    assert retrieved["id"] == first_policy_id
    assert retrieved["name"] == "Standard Sales Tax"
    assert retrieved["tax_rate_basis_points"] == 725
    assert retrieved["is_default"] is True

    default_response = repair_client.get(
        f"{TAX_POLICIES_URL}/default",
        headers=OWNER_HEADERS,
    )
    assert default_response.status_code == 200, default_response.text

    default_policy = default_response.json()
    assert default_policy["id"] == first_policy_id
    assert default_policy["is_default"] is True

    second_policy = create_tax_policy(
        repair_client,
        name="Reduced Sales Tax",
        tax_rate_basis_points=500,
        is_default=False,
        effective_at="2026-08-01T09:30:00Z",
    )

    second_policy_id = second_policy["id"]

    assert second_policy["name"] == "Reduced Sales Tax"
    assert second_policy["tax_rate_basis_points"] == 500
    assert second_policy["is_default"] is False

    list_response = repair_client.get(
        TAX_POLICIES_URL,
        headers=OWNER_HEADERS,
    )
    assert list_response.status_code == 200, list_response.text

    listed = list_response.json()

    assert listed["total"] == 2
    assert len(listed["items"]) == 2
    assert listed["items"][0]["id"] == first_policy_id
    assert listed["items"][0]["is_default"] is True

    listed_ids = {item["id"] for item in listed["items"]}
    assert listed_ids == {first_policy_id, second_policy_id}

    update_response = repair_client.patch(
        f"{TAX_POLICIES_URL}/{second_policy_id}",
        headers=OWNER_HEADERS,
        json={
            "name": "  Reduced Default Tax  ",
            "tax_rate_basis_points": 550,
            "is_default": True,
            "effective_at": "2026-08-15T10:00:00Z",
        },
    )
    assert update_response.status_code == 200, update_response.text

    updated = update_response.json()

    assert updated["id"] == second_policy_id
    assert updated["owner_user_id"] == "repair-owner-001"
    assert updated["name"] == "Reduced Default Tax"
    assert updated["tax_rate_basis_points"] == 550
    assert updated["is_default"] is True
    assert updated["effective_at"]
    assert updated["updated_at"]

    new_default_response = repair_client.get(
        f"{TAX_POLICIES_URL}/default",
        headers=OWNER_HEADERS,
    )
    assert new_default_response.status_code == 200, new_default_response.text

    new_default = new_default_response.json()

    assert new_default["id"] == second_policy_id
    assert new_default["name"] == "Reduced Default Tax"
    assert new_default["tax_rate_basis_points"] == 550
    assert new_default["is_default"] is True

    first_after_update_response = repair_client.get(
        f"{TAX_POLICIES_URL}/{first_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert first_after_update_response.status_code == 200

    first_after_update = first_after_update_response.json()

    assert first_after_update["id"] == first_policy_id
    assert first_after_update["is_default"] is False

    reordered_list_response = repair_client.get(
        TAX_POLICIES_URL,
        headers=OWNER_HEADERS,
    )
    assert reordered_list_response.status_code == 200

    reordered = reordered_list_response.json()

    assert reordered["total"] == 2
    assert reordered["items"][0]["id"] == second_policy_id
    assert reordered["items"][0]["is_default"] is True

    delete_response = repair_client.delete(
        f"{TAX_POLICIES_URL}/{first_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert delete_response.status_code == 204, delete_response.text

    deleted_get_response = repair_client.get(
        f"{TAX_POLICIES_URL}/{first_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert deleted_get_response.status_code == 404

    final_list_response = repair_client.get(
        TAX_POLICIES_URL,
        headers=OWNER_HEADERS,
    )
    assert final_list_response.status_code == 200

    final_list = final_list_response.json()

    assert final_list["total"] == 1
    assert len(final_list["items"]) == 1
    assert final_list["items"][0]["id"] == second_policy_id
    assert final_list["items"][0]["is_default"] is True


def test_tax_policy_owner_isolation_and_missing_resources(
    repair_client: TestClient,
) -> None:
    missing_default_response = repair_client.get(
        f"{TAX_POLICIES_URL}/default",
        headers=OWNER_HEADERS,
    )
    assert missing_default_response.status_code == 404

    owner_policy = create_tax_policy(repair_client)
    owner_policy_id = owner_policy["id"]

    other_owner_list_response = repair_client.get(
        TAX_POLICIES_URL,
        headers=OTHER_HEADERS,
    )
    assert other_owner_list_response.status_code == 200
    assert other_owner_list_response.json() == {
        "items": [],
        "total": 0,
    }

    other_owner_get_response = repair_client.get(
        f"{TAX_POLICIES_URL}/{owner_policy_id}",
        headers=OTHER_HEADERS,
    )
    assert other_owner_get_response.status_code == 404

    other_owner_default_response = repair_client.get(
        f"{TAX_POLICIES_URL}/default",
        headers=OTHER_HEADERS,
    )
    assert other_owner_default_response.status_code == 404

    other_owner_update_response = repair_client.patch(
        f"{TAX_POLICIES_URL}/{owner_policy_id}",
        headers=OTHER_HEADERS,
        json={
            "name": "Unauthorized Change",
            "tax_rate_basis_points": 900,
        },
    )
    assert other_owner_update_response.status_code == 404

    other_owner_delete_response = repair_client.delete(
        f"{TAX_POLICIES_URL}/{owner_policy_id}",
        headers=OTHER_HEADERS,
    )
    assert other_owner_delete_response.status_code == 404

    missing_policy_id = "tax_does_not_exist"

    missing_get_response = repair_client.get(
        f"{TAX_POLICIES_URL}/{missing_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert missing_get_response.status_code == 404

    missing_update_response = repair_client.patch(
        f"{TAX_POLICIES_URL}/{missing_policy_id}",
        headers=OWNER_HEADERS,
        json={
            "name": "Missing Policy",
            "tax_rate_basis_points": 600,
        },
    )
    assert missing_update_response.status_code == 404

    missing_delete_response = repair_client.delete(
        f"{TAX_POLICIES_URL}/{missing_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert missing_delete_response.status_code == 404

    owner_get_response = repair_client.get(
        f"{TAX_POLICIES_URL}/{owner_policy_id}",
        headers=OWNER_HEADERS,
    )
    assert owner_get_response.status_code == 200

    owner_policy_after_attempts = owner_get_response.json()

    assert owner_policy_after_attempts["id"] == owner_policy_id
    assert owner_policy_after_attempts["name"] == "Standard Sales Tax"
    assert owner_policy_after_attempts["tax_rate_basis_points"] == 725
    assert owner_policy_after_attempts["is_default"] is True


def test_tax_policy_validation_and_authentication(
    repair_client: TestClient,
) -> None:
    unauthenticated_list_response = repair_client.get(
        TAX_POLICIES_URL,
    )
    assert unauthenticated_list_response.status_code in {401, 403}

    unauthenticated_create_response = repair_client.post(
        TAX_POLICIES_URL,
        json=tax_policy_payload(),
    )
    assert unauthenticated_create_response.status_code in {401, 403}

    empty_name_response = repair_client.post(
        TAX_POLICIES_URL,
        headers=OWNER_HEADERS,
        json=tax_policy_payload(name="   "),
    )
    assert empty_name_response.status_code == 422

    negative_tax_rate_response = repair_client.post(
        TAX_POLICIES_URL,
        headers=OWNER_HEADERS,
        json=tax_policy_payload(tax_rate_basis_points=-1),
    )
    assert negative_tax_rate_response.status_code == 422

    invalid_effective_at_response = repair_client.post(
        TAX_POLICIES_URL,
        headers=OWNER_HEADERS,
        json=tax_policy_payload(effective_at="not-a-date"),
    )
    assert invalid_effective_at_response.status_code == 422

    missing_name_response = repair_client.post(
        TAX_POLICIES_URL,
        headers=OWNER_HEADERS,
        json={
            "tax_rate_basis_points": 725,
            "is_default": True,
            "effective_at": "2026-07-29T12:00:00Z",
        },
    )
    assert missing_name_response.status_code == 422

    missing_tax_rate_response = repair_client.post(
        TAX_POLICIES_URL,
        headers=OWNER_HEADERS,
        json={
            "name": "Missing Rate Tax",
            "is_default": True,
            "effective_at": "2026-07-29T12:00:00Z",
        },
    )
    assert missing_tax_rate_response.status_code == 422

    valid_policy = create_tax_policy(repair_client)
    policy_id = valid_policy["id"]

    empty_update_name_response = repair_client.patch(
        f"{TAX_POLICIES_URL}/{policy_id}",
        headers=OWNER_HEADERS,
        json={"name": "   "},
    )
    assert empty_update_name_response.status_code == 422

    negative_update_tax_rate_response = repair_client.patch(
        f"{TAX_POLICIES_URL}/{policy_id}",
        headers=OWNER_HEADERS,
        json={"tax_rate_basis_points": -1},
    )
    assert negative_update_tax_rate_response.status_code == 422

    invalid_update_effective_at_response = repair_client.patch(
        f"{TAX_POLICIES_URL}/{policy_id}",
        headers=OWNER_HEADERS,
        json={"effective_at": "not-a-date"},
    )
    assert invalid_update_effective_at_response.status_code == 422

    empty_update_response = repair_client.patch(
        f"{TAX_POLICIES_URL}/{policy_id}",
        headers=OWNER_HEADERS,
        json={},
    )

    assert empty_update_response.status_code in {200, 422}

    final_get_response = repair_client.get(
        f"{TAX_POLICIES_URL}/{policy_id}",
        headers=OWNER_HEADERS,
    )
    assert final_get_response.status_code == 200

    final_policy = final_get_response.json()

    assert final_policy["id"] == policy_id
    assert final_policy["name"] == "Standard Sales Tax"
    assert final_policy["tax_rate_basis_points"] == 725
    assert final_policy["is_default"] is True
