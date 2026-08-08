import pandas as pd

from repositories.repository_base import RepositoryBase


class CompatibilitySchemaError(ValueError):
    """The loaded compatibility table does not satisfy its adapter contract."""


class DuplicateCompatibilityError(ValueError):
    """A device-family/service lookup matched more than one workbook row."""


class CompatibilityRepository(RepositoryBase):

    REQUIRED_COLUMNS = ("Device Family", "Service Name", "Supported")

    def __init__(self, database):

        super().__init__(database, "compatibility")

    # ======================================================
    # Collections
    # ======================================================

    def all(self):

        return super().all()

    # ======================================================
    # Single Record
    # ======================================================

    def get(self, compatibility_id):

        return self.first("Compatibility ID", compatibility_id)

    # ======================================================
    # Search
    # ======================================================

    def find_service(
        self,
        device_family_code: str,
        service_id: str,
    ) -> pd.Series | None:
        """Find one service using the current workbook's legacy column names."""

        missing = [
            column for column in self.REQUIRED_COLUMNS if column not in self.table
        ]
        if missing:
            columns = ", ".join(f"'{column}'" for column in missing)
            raise CompatibilitySchemaError(
                "Compatibility table is missing required column(s): " + columns
            )

        matches = self.table[
            (self.table["Device Family"] == device_family_code)
            & (self.table["Service Name"] == service_id)
        ]

        if len(matches) > 1:
            raise DuplicateCompatibilityError(
                "Compatibility lookup matched multiple rows for "
                f"device family '{device_family_code}' and service '{service_id}'."
            )

        if matches.empty:
            return None

        return matches.iloc[0]

    def find_repair(self, device_family, service_id):
        # TODO (Phase 2): Remove compatibility shim after canonical workbook migration.

        record = self.find_service(device_family, service_id)
        if record is None:
            return self.table.iloc[0:0].copy()
        return record.to_frame().T

    def services_for_family(self, family_code):

        return self.filter("Device Family", family_code)

    def supported_services(self, family_code):

        df = self.services_for_family(family_code)

        return df[df["Supported"].fillna(False)]
