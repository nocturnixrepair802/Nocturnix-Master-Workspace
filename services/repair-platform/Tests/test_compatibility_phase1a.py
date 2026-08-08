import warnings

import pandas as pd
import pytest

from engines.compatibility_engine import (
    CompatibilityEngine,
    CompatibilityValueError,
)
from engines.quote_engine import QuoteEngine
from engines.results import CompatibilityResult
from managers.repair_manager import RepairManager
from repositories.compatibility_repository import (
    CompatibilityRepository,
    CompatibilitySchemaError,
    DuplicateCompatibilityError,
)


def compatibility_database(*rows: dict[str, object]) -> dict[str, pd.DataFrame]:
    return {"compatibility": pd.DataFrame(rows)}


def row(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "Device Family": "PHN",
        "Service Name": "SVC000001",
        "Supported": True,
        "Notes": None,
        "Requires Capability": None,
    }
    values.update(overrides)
    return values


def full_database(*compatibility_rows: dict[str, object]) -> dict[str, pd.DataFrame]:
    return {
        **compatibility_database(*compatibility_rows),
        "labor_rates": pd.DataFrame([{"Hourly Rate": 100.0}]),
        "retail_pricing": pd.DataFrame([{"Markup": 1.5}]),
        "parts_catalog": pd.DataFrame(columns=["SKU", "Quantity"]),
    }


class TestCompatibilityRepository:
    def test_current_workbook_aliases_support_canonical_lookup(self) -> None:
        repository = CompatibilityRepository(compatibility_database(row()))

        match = repository.find_service("PHN", "SVC000001")

        assert match is not None
        assert match["Service Name"] == "SVC000001"

    def test_missing_required_column_is_descriptive(self) -> None:
        repository = CompatibilityRepository(
            compatibility_database({"Device Family": "PHN", "Supported": True})
        )

        with pytest.raises(CompatibilitySchemaError, match="'Service Name'"):
            repository.find_service("PHN", "SVC000001")

    def test_duplicate_rows_are_rejected(self) -> None:
        repository = CompatibilityRepository(compatibility_database(row(), row()))

        with pytest.raises(DuplicateCompatibilityError, match="multiple rows"):
            repository.find_service("PHN", "SVC000001")


class TestCompatibilityEngine:
    @pytest.mark.parametrize("supported", [True, False])
    def test_matching_row_honors_supported(self, supported: bool) -> None:
        engine = CompatibilityEngine(
            CompatibilityRepository(compatibility_database(row(Supported=supported)))
        )

        result = engine.validate("PHN", "SVC000001")

        assert result.supported is supported

    def test_missing_row_is_unsupported(self) -> None:
        engine = CompatibilityEngine(
            CompatibilityRepository(compatibility_database(row()))
        )

        assert engine.validate("TAB", "SVC000001") == CompatibilityResult(
            supported=False,
            reason="Repair not supported.",
        )

    def test_notes_are_used_as_reason(self) -> None:
        engine = CompatibilityEngine(
            CompatibilityRepository(
                compatibility_database(row(Notes="Requires inspection"))
            )
        )

        assert engine.validate("PHN", "SVC000001").reason == "Requires inspection"

    def test_required_capability_is_preserved(self) -> None:
        engine = CompatibilityEngine(
            CompatibilityRepository(
                compatibility_database(row(**{"Requires Capability": "MICRO"}))
            )
        )

        result = engine.validate("PHN", "SVC000001")

        assert result.requires_capability == "MICRO"

    @pytest.mark.parametrize("value", [None, "Yes", 1, ""])
    def test_malformed_supported_value_is_rejected(self, value: object) -> None:
        engine = CompatibilityEngine(
            CompatibilityRepository(
                compatibility_database(row(Supported=value))
            )
        )

        with pytest.raises(CompatibilityValueError, match="non-null boolean"):
            engine.validate("PHN", "SVC000001")


class TestCompatibilityComposition:
    def test_validate_service_manager_contract(self) -> None:
        manager = RepairManager(full_database(row()))

        result = manager.validate_service("PHN", "SVC000001")

        assert isinstance(result, CompatibilityResult)
        assert result.supported is True

    def test_validate_part_delegates_with_deprecation_warning(self) -> None:
        manager = RepairManager(full_database(row()))

        with pytest.warns(DeprecationWarning, match="validate_service"):
            result = manager.validate_part("PHN", "SVC000001")

        assert result == manager.validate_service("PHN", "SVC000001")

    def test_quote_uses_injected_shared_compatibility_engine(self) -> None:
        database = full_database(row(Supported=False, Notes="Not offered"))
        compatibility = CompatibilityEngine(CompatibilityRepository(database))
        quote = QuoteEngine(database, compatibility)

        result = quote.generate("PHN", "SVC000001", 1.0, 25.0)

        assert quote.compatibility is compatibility
        assert result == {
            "supported": False,
            "reason": "Not offered",
            "requires_capability": None,
        }

    def test_manager_quote_and_validation_share_engine(self) -> None:
        manager = RepairManager(full_database(row()))

        assert manager.quote.compatibility is manager.compatibility

    def test_validate_part_emits_no_warning_until_called(self) -> None:
        manager = RepairManager(full_database(row()))

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

        assert manager.compatibility is manager.quote.compatibility
        assert caught == []
