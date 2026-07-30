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
            database_url=f"sqlite:///{tmp_path / 'repair_services.db'}",
            database_migration_mode="auto-test-only",
            auth_mode="development_header",
            allow_development_header_auth=True,
            rate_limit_per_minute=500,
        )
    )

    with TestClient(app) as client:
        yield client

    cast(Any, app).state.container.engine.dispose()


def service_payload(
    *,
    name: str = "Screen Replacement",
    category: str = "Display",
    description: str = "Replace cracked LCD assembly",
    default_labor_minutes: int = 45,
    estimated_duration_minutes: int = 60,
    taxable: bool = True,
    is_active: bool = True,
) -> dict[str, Any]:
    return {
        "name": name,
        "category": category,
        "description": description,
        "default_labor_minutes": default_labor_minutes,
        "estimated_duration_minutes": estimated_duration_minutes,
        "taxable": taxable,
        "is_active": is_active,
    }


def create_repair_service(
    client: TestClient,
    *,
    headers: dict[str, str] = OWNER_HEADERS,
    **overrides: Any,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/repair/services",
        headers=headers,
        json=service_payload(**overrides),
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_repair_service_crud(
    repair_client: TestClient,
) -> None:
    first_service = create_repair_service(repair_client)

    assert first_service["owner_user_id"] == "repair-owner-001"
    assert first_service["name"] == "Screen Replacement"
    assert first_service["category"] == "Display"
    assert first_service["description"] == "Replace cracked LCD assembly"
    assert first_service["default_labor_minutes"] == 45
    assert first_service["estimated_duration_minutes"] == 60
    assert first_service["taxable"] is True
    assert first_service["is_active"] is True
    assert first_service["id"]
    assert first_service["created_at"]
    assert first_service["updated_at"]

    first_service_id = first_service["id"]

    get_response = repair_client.get(
        f"/api/v1/repair/services/{first_service_id}",
        headers=OWNER_HEADERS,
    )
    assert get_response.status_code == 200, get_response.text

    retrieved = get_response.json()

    assert retrieved["id"] == first_service_id
    assert retrieved["owner_user_id"] == "repair-owner-001"
    assert retrieved["name"] == "Screen Replacement"
    assert retrieved["category"] == "Display"
    assert retrieved["description"] == "Replace cracked LCD assembly"
    assert retrieved["default_labor_minutes"] == 45
    assert retrieved["estimated_duration_minutes"] == 60
    assert retrieved["taxable"] is True
    assert retrieved["is_active"] is True

    second_service = create_repair_service(
        repair_client,
        name="Battery Replacement",
        category="Battery",
        description="Replace an internal rechargeable battery",
        default_labor_minutes=30,
        estimated_duration_minutes=45,
        taxable=True,
        is_active=True,
    )

    second_service_id = second_service["id"]

    list_response = repair_client.get(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
    )
    assert list_response.status_code == 200, list_response.text

    listed = list_response.json()

    assert listed["total"] == 2
    assert len(listed["items"]) == 2
    assert listed["offset"] == 0
    assert listed["limit"] == 50

    listed_ids = {item["id"] for item in listed["items"]}
    assert listed_ids == {first_service_id, second_service_id}

    update_response = repair_client.patch(
        f"/api/v1/repair/services/{second_service_id}",
        headers=OWNER_HEADERS,
        json={
            "name": "  Premium Battery Replacement  ",
            "category": "Premium Battery",
            "description": "Premium battery replacement and calibration",
            "default_labor_minutes": 75,
            "estimated_duration_minutes": 120,
            "taxable": False,
            "is_active": False,
        },
    )
    assert update_response.status_code == 200, update_response.text

    updated = update_response.json()

    assert updated["id"] == second_service_id
    assert updated["owner_user_id"] == "repair-owner-001"
    assert updated["name"] == "Premium Battery Replacement"
    assert updated["category"] == "Premium Battery"
    assert updated["description"] == ("Premium battery replacement and calibration")
    assert updated["default_labor_minutes"] == 75
    assert updated["estimated_duration_minutes"] == 120
    assert updated["taxable"] is False
    assert updated["is_active"] is False
    assert updated["created_at"]
    assert updated["updated_at"]

    delete_response = repair_client.delete(
        f"/api/v1/repair/services/{first_service_id}",
        headers=OWNER_HEADERS,
    )
    assert delete_response.status_code == 204, delete_response.text

    deleted_get_response = repair_client.get(
        f"/api/v1/repair/services/{first_service_id}",
        headers=OWNER_HEADERS,
    )
    assert deleted_get_response.status_code == 404

    final_list_response = repair_client.get(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
    )
    assert final_list_response.status_code == 200, final_list_response.text

    final_list = final_list_response.json()

    assert final_list["total"] == 1
    assert len(final_list["items"]) == 1
    assert final_list["items"][0]["id"] == second_service_id


def test_repair_service_filters_and_pagination(
    repair_client: TestClient,
) -> None:
    screen_service = create_repair_service(
        repair_client,
        name="Screen Replacement",
        category="Display",
        description="Replace a damaged phone screen",
        default_labor_minutes=45,
        estimated_duration_minutes=60,
        taxable=True,
        is_active=True,
    )

    battery_service = create_repair_service(
        repair_client,
        name="Battery Replacement",
        category="Battery",
        description="Replace an internal battery",
        default_labor_minutes=30,
        estimated_duration_minutes=45,
        taxable=True,
        is_active=True,
    )

    inactive_service = create_repair_service(
        repair_client,
        name="Legacy Charging Port Repair",
        category="Charging Port",
        description="Legacy charging-port repair service",
        default_labor_minutes=90,
        estimated_duration_minutes=120,
        taxable=True,
        is_active=False,
    )

    search_response = repair_client.get(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
        params={"search": "Screen"},
    )
    assert search_response.status_code == 200, search_response.text

    searched = search_response.json()

    assert searched["total"] == 1
    assert len(searched["items"]) == 1
    assert searched["items"][0]["id"] == screen_service["id"]

    category_response = repair_client.get(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
        params={"category": "Battery"},
    )
    assert category_response.status_code == 200, category_response.text

    categorized = category_response.json()

    assert categorized["total"] == 1
    assert len(categorized["items"]) == 1
    assert categorized["items"][0]["id"] == battery_service["id"]

    active_response = repair_client.get(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
        params={"is_active": "true"},
    )
    assert active_response.status_code == 200, active_response.text

    active_services = active_response.json()

    assert active_services["total"] == 2
    assert len(active_services["items"]) == 2
    assert all(item["is_active"] is True for item in active_services["items"])

    inactive_response = repair_client.get(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
        params={"is_active": "false"},
    )
    assert inactive_response.status_code == 200, inactive_response.text

    inactive_services = inactive_response.json()

    assert inactive_services["total"] == 1
    assert len(inactive_services["items"]) == 1
    assert inactive_services["items"][0]["id"] == inactive_service["id"]
    assert inactive_services["items"][0]["is_active"] is False

    page_response = repair_client.get(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
        params={"offset": 1, "limit": 1},
    )
    assert page_response.status_code == 200, page_response.text

    page = page_response.json()

    assert page["total"] == 3
    assert page["offset"] == 1
    assert page["limit"] == 1
    assert len(page["items"]) == 1


def test_repair_service_owner_isolation_and_missing_resources(
    repair_client: TestClient,
) -> None:
    owner_service = create_repair_service(repair_client)
    owner_service_id = owner_service["id"]

    other_owner_list_response = repair_client.get(
        "/api/v1/repair/services",
        headers=OTHER_HEADERS,
    )
    assert other_owner_list_response.status_code == 200

    other_owner_list = other_owner_list_response.json()

    assert other_owner_list["items"] == []
    assert other_owner_list["total"] == 0
    assert other_owner_list["offset"] == 0
    assert other_owner_list["limit"] == 50

    other_owner_get_response = repair_client.get(
        f"/api/v1/repair/services/{owner_service_id}",
        headers=OTHER_HEADERS,
    )
    assert other_owner_get_response.status_code == 404

    other_owner_update_response = repair_client.patch(
        f"/api/v1/repair/services/{owner_service_id}",
        headers=OTHER_HEADERS,
        json={"name": "Unauthorized Change"},
    )
    assert other_owner_update_response.status_code == 404

    other_owner_delete_response = repair_client.delete(
        f"/api/v1/repair/services/{owner_service_id}",
        headers=OTHER_HEADERS,
    )
    assert other_owner_delete_response.status_code == 404

    missing_service_id = "service_does_not_exist"

    missing_get_response = repair_client.get(
        f"/api/v1/repair/services/{missing_service_id}",
        headers=OWNER_HEADERS,
    )
    assert missing_get_response.status_code == 404

    missing_update_response = repair_client.patch(
        f"/api/v1/repair/services/{missing_service_id}",
        headers=OWNER_HEADERS,
        json={"name": "Missing Service"},
    )
    assert missing_update_response.status_code == 404

    missing_delete_response = repair_client.delete(
        f"/api/v1/repair/services/{missing_service_id}",
        headers=OWNER_HEADERS,
    )
    assert missing_delete_response.status_code == 404

    owner_get_response = repair_client.get(
        f"/api/v1/repair/services/{owner_service_id}",
        headers=OWNER_HEADERS,
    )
    assert owner_get_response.status_code == 200
    assert owner_get_response.json()["name"] == "Screen Replacement"


def test_repair_service_validation_and_authentication(
    repair_client: TestClient,
) -> None:
    unauthenticated_list_response = repair_client.get(
        "/api/v1/repair/services",
    )
    assert unauthenticated_list_response.status_code in {401, 403}

    unauthenticated_create_response = repair_client.post(
        "/api/v1/repair/services",
        json=service_payload(),
    )
    assert unauthenticated_create_response.status_code in {401, 403}

    empty_name_response = repair_client.post(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
        json=service_payload(name="   "),
    )
    assert empty_name_response.status_code == 422

    empty_category_response = repair_client.post(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
        json=service_payload(category="   "),
    )
    assert empty_category_response.status_code == 422

    negative_labor_response = repair_client.post(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
        json=service_payload(default_labor_minutes=-1),
    )
    assert negative_labor_response.status_code == 422

    negative_duration_response = repair_client.post(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
        json=service_payload(estimated_duration_minutes=-1),
    )
    assert negative_duration_response.status_code == 422

    valid_service = create_repair_service(repair_client)
    service_id = valid_service["id"]

    empty_update_name_response = repair_client.patch(
        f"/api/v1/repair/services/{service_id}",
        headers=OWNER_HEADERS,
        json={"name": "   "},
    )
    assert empty_update_name_response.status_code == 422

    empty_update_category_response = repair_client.patch(
        f"/api/v1/repair/services/{service_id}",
        headers=OWNER_HEADERS,
        json={"category": "   "},
    )
    assert empty_update_category_response.status_code == 422

    negative_update_labor_response = repair_client.patch(
        f"/api/v1/repair/services/{service_id}",
        headers=OWNER_HEADERS,
        json={"default_labor_minutes": -1},
    )
    assert negative_update_labor_response.status_code == 422

    negative_update_duration_response = repair_client.patch(
        f"/api/v1/repair/services/{service_id}",
        headers=OWNER_HEADERS,
        json={"estimated_duration_minutes": -1},
    )
    assert negative_update_duration_response.status_code == 422

    invalid_offset_response = repair_client.get(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
        params={"offset": -1},
    )
    assert invalid_offset_response.status_code == 422

    invalid_limit_response = repair_client.get(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
        params={"limit": 0},
    )
    assert invalid_limit_response.status_code == 422

    excessive_limit_response = repair_client.get(
        "/api/v1/repair/services",
        headers=OWNER_HEADERS,
        params={"limit": 101},
    )
    assert excessive_limit_response.status_code == 422
