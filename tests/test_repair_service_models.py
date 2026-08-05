from typing import Any

import pytest
from pydantic import ValidationError

from nocturnix.repair_models import (
    RepairServiceCreateRequest,
    RepairServiceUpdateRequest,
)


def valid_service_payload(
    **overrides: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": "Screen Replacement",
        "category": "Display",
        "description": "Replace cracked LCD assembly",
        "default_labor_minutes": 45,
        "estimated_duration_minutes": 60,
        "taxable": True,
        "is_active": True,
    }
    payload.update(overrides)
    return payload


def test_repair_service_create_request_accepts_valid_values() -> None:
    request = RepairServiceCreateRequest(
        name="Screen Replacement",
        category="Display",
        description="Replace cracked LCD assembly",
        default_labor_minutes=45,
        estimated_duration_minutes=60,
        taxable=True,
        is_active=True,
    )

    assert request.name == "Screen Replacement"
    assert request.category == "Display"
    assert request.description == "Replace cracked LCD assembly"
    assert request.default_labor_minutes == 45
    assert request.estimated_duration_minutes == 60
    assert request.taxable is True
    assert request.is_active is True


def test_repair_service_create_request_uses_expected_defaults() -> None:
    request = RepairServiceCreateRequest(
        name="Diagnostic Service",
        category="Diagnostics",
        description="Perform a complete diagnostic inspection",
        default_labor_minutes=30,
    )

    assert request.name == "Diagnostic Service"
    assert request.category == "Diagnostics"
    assert request.description == "Perform a complete diagnostic inspection"
    assert request.default_labor_minutes == 30
    assert request.estimated_duration_minutes is None
    assert request.taxable is True
    assert request.is_active is True


def test_repair_service_create_request_parses_external_input() -> None:
    request = RepairServiceCreateRequest.model_validate(
        {
            "name": "Screen Replacement",
            "category": "Display",
            "description": "Replace cracked LCD assembly",
            "default_labor_minutes": "45",
            "estimated_duration_minutes": "60",
            "taxable": "true",
            "is_active": "true",
        }
    )

    assert request.default_labor_minutes == 45
    assert isinstance(request.default_labor_minutes, int)

    assert request.estimated_duration_minutes == 60
    assert isinstance(request.estimated_duration_minutes, int)

    assert request.taxable is True
    assert isinstance(request.taxable, bool)

    assert request.is_active is True
    assert isinstance(request.is_active, bool)


def test_repair_service_create_request_trims_text_fields() -> None:
    request = RepairServiceCreateRequest(
        name="  Screen Replacement  ",
        category="  Display  ",
        description="  Replace cracked LCD assembly  ",
        default_labor_minutes=45,
        estimated_duration_minutes=60,
        taxable=True,
        is_active=True,
    )

    assert request.name == "Screen Replacement"
    assert request.category == "Display"
    assert request.description == "Replace cracked LCD assembly"


@pytest.mark.parametrize(
    "field_name",
    [
        "name",
        "category",
    ],
)
def test_repair_service_create_request_rejects_blank_required_text(
    field_name: str,
) -> None:
    payload = valid_service_payload()
    payload[field_name] = "   "

    with pytest.raises(ValidationError):
        RepairServiceCreateRequest.model_validate(payload)


def test_repair_service_create_request_rejects_negative_labor_minutes() -> None:
    with pytest.raises(ValidationError):
        RepairServiceCreateRequest.model_validate(valid_service_payload(default_labor_minutes=-1))


def test_repair_service_create_request_rejects_negative_duration() -> None:
    with pytest.raises(ValidationError):
        RepairServiceCreateRequest.model_validate(
            valid_service_payload(estimated_duration_minutes=-1)
        )


def test_repair_service_create_request_allows_missing_estimated_duration() -> None:
    request = RepairServiceCreateRequest.model_validate(
        valid_service_payload(estimated_duration_minutes=None)
    )

    assert request.estimated_duration_minutes is None


def test_repair_service_create_request_rejects_unknown_fields() -> None:
    payload = valid_service_payload()
    payload["unexpected_field"] = "not allowed"

    with pytest.raises(ValidationError):
        RepairServiceCreateRequest.model_validate(payload)


def test_repair_service_update_request_accepts_partial_update() -> None:
    request = RepairServiceUpdateRequest(
        name="Premium Screen Replacement",
    )

    assert request.name == "Premium Screen Replacement"

    assert request.model_fields_set == {"name"}


def test_repair_service_update_request_accepts_all_fields() -> None:
    request = RepairServiceUpdateRequest(
        name="Premium Screen Replacement",
        category="Premium Display",
        description="Replace and calibrate premium OLED display",
        default_labor_minutes=75,
        estimated_duration_minutes=120,
        taxable=False,
        is_active=False,
    )

    assert request.name == "Premium Screen Replacement"
    assert request.category == "Premium Display"
    assert request.description == "Replace and calibrate premium OLED display"
    assert request.default_labor_minutes == 75
    assert request.estimated_duration_minutes == 120
    assert request.taxable is False
    assert request.is_active is False


def test_repair_service_update_request_parses_external_input() -> None:
    request = RepairServiceUpdateRequest.model_validate(
        {
            "default_labor_minutes": "75",
            "estimated_duration_minutes": "120",
            "taxable": "false",
            "is_active": "false",
        }
    )

    assert request.default_labor_minutes == 75
    assert request.estimated_duration_minutes == 120
    assert request.taxable is False
    assert request.is_active is False


def test_repair_service_update_request_trims_text_fields() -> None:
    request = RepairServiceUpdateRequest(
        name="  Premium Screen Replacement  ",
        category="  Premium Display  ",
        description="  Replace and calibrate OLED display  ",
    )

    assert request.name == "Premium Screen Replacement"
    assert request.category == "Premium Display"
    assert request.description == "Replace and calibrate OLED display"


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("name", "   "),
        ("category", "   "),
    ],
)
def test_repair_service_update_request_rejects_blank_required_text(
    field_name: str,
    field_value: str,
) -> None:
    with pytest.raises(ValidationError):
        RepairServiceUpdateRequest.model_validate(
            {
                field_name: field_value,
            }
        )


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("default_labor_minutes", -1),
        ("estimated_duration_minutes", -1),
    ],
)
def test_repair_service_update_request_rejects_negative_minutes(
    field_name: str,
    field_value: int,
) -> None:
    with pytest.raises(ValidationError):
        RepairServiceUpdateRequest.model_validate(
            {
                field_name: field_value,
            }
        )


def test_repair_service_update_request_distinguishes_omitted_and_null_fields() -> None:
    omitted_request = RepairServiceUpdateRequest()
    null_request = RepairServiceUpdateRequest(
        description=None,
        estimated_duration_minutes=None,
    )

    assert omitted_request.model_fields_set == set()

    assert null_request.model_fields_set == {
        "description",
        "estimated_duration_minutes",
    }
    assert null_request.description is None
    assert null_request.estimated_duration_minutes is None


def test_repair_service_update_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        RepairServiceUpdateRequest.model_validate(
            {
                "unexpected_field": "not allowed",
            }
        )
