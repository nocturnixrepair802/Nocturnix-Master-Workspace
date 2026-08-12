from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

import desktop.services.square_service as square_service_module
from desktop.services.settings_service import DesktopSettings


class FakeSquareClient:
    def __init__(
        self,
        *,
        token: str,
        environment: object,
    ) -> None:
        self.token = token
        self.environment = environment


@pytest.fixture
def square_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "SQUARE_ACCESS_TOKEN",
        "test-token",
    )
    monkeypatch.setenv(
        "SQUARE_LOCATION_ID",
        "test-location",
    )

    monkeypatch.setattr(
        square_service_module,
        "Square",
        FakeSquareClient,
    )


def test_square_service_uses_sandbox_environment(
    square_environment: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        square_service_module.SettingsService,
        "load",
        lambda self: DesktopSettings(
            square_environment="sandbox",
            default_currency="USD",
        ),
    )

    service = square_service_module.SquareService()

    client = cast(
        FakeSquareClient,
        service.client,
    )

    assert client.environment == square_service_module.SquareEnvironment.SANDBOX

    assert service.default_currency == "USD"


def test_square_service_uses_production_environment(
    square_environment: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        square_service_module.SettingsService,
        "load",
        lambda self: DesktopSettings(
            square_environment="production",
            default_currency="USD",
        ),
    )

    service = square_service_module.SquareService()

    client = cast(
        FakeSquareClient,
        service.client,
    )

    assert client.environment == square_service_module.SquareEnvironment.PRODUCTION


def test_money_currency_uses_configured_default(
    square_environment: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        square_service_module.SettingsService,
        "load",
        lambda self: DesktopSettings(
            square_environment="sandbox",
            default_currency="CAD",
        ),
    )

    service = square_service_module.SquareService()

    assert service._money_currency(None) == "CAD"

    money = SimpleNamespace(
        currency=None,
    )

    assert service._money_currency(money) == "CAD"


def test_money_currency_prefers_square_value(
    square_environment: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        square_service_module.SettingsService,
        "load",
        lambda self: DesktopSettings(
            square_environment="sandbox",
            default_currency="CAD",
        ),
    )

    service = square_service_module.SquareService()

    money = SimpleNamespace(
        currency="USD",
    )

    assert service._money_currency(money) == "USD"
