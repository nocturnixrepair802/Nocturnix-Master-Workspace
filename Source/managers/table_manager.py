"""
============================================================
Nocturnix Repair Platform
Table Manager
============================================================

Author: Nocturnix Mobile Repair
Version: 2.0.0 Alpha

Purpose:
    Central manager responsible for locating,
    reading, validating, and manipulating Excel
    Tables within the Nocturnix Master Database.

Responsibilities
----------------
• Locate Excel Tables
• Validate Table Names
• Read Table Records
• Search Records
• Count Records
• Append Records
• Clear Tables
• Save Workbook

Repositories should communicate with Excel
through this class.

============================================================
"""

from typing import Any

from openpyxl.worksheet.table import Table
from openpyxl.utils.cell import range_boundaries
from openpyxl.worksheet.worksheet import Worksheet

from managers.workbook_manager import WorkbookManager
from managers.worksheet_manager import WorksheetManager


class TableManager:
    """
    Central manager responsible for all Excel
    Table operations.
    """

    def __init__(
        self,
        workbook_manager: WorkbookManager,
        worksheet_manager: WorksheetManager,
    ):

        self.workbook_manager = workbook_manager

        self.worksheet_manager = worksheet_manager

    # ======================================================
    # Table Discovery
    # ======================================================

    def get_table(
        self,
        table_name: str,
    ) -> Table | None:
        """
        Returns an Excel Table object.
        """

        workbook = self.workbook_manager.workbook_instance

        for worksheet in workbook.worksheets:

            if table_name in worksheet.tables:

                return worksheet.tables[table_name]

        return None

    def get_table_and_sheet(
        self,
        table_name: str,
    ) -> tuple[Worksheet, Table]:
        """
        Returns the worksheet and table together.

        Raises
        ------
        ValueError
            If the table cannot be located.
        """

        workbook = self.workbook_manager.workbook_instance

        for worksheet in workbook.worksheets:

            if table_name in worksheet.tables:

                table = worksheet.tables[table_name]

                return worksheet, table

        raise ValueError(f"Table '{table_name}' was not found.")

    def exists(
        self,
        table_name: str,
    ) -> bool:

        return self.get_table(table_name) is not None

    def list_tables(
        self,
    ) -> list[str]:

        workbook = self.workbook_manager.workbook_instance

        tables: list[str] = []

        for worksheet in workbook.worksheets:

            tables.extend(worksheet.tables.keys())

        return sorted(tables)

    def count(self) -> int:

        return len(self.list_tables())

    # ======================================================
    # Table Information
    # ======================================================

    def validate_table(
        self,
        table_name: str,
    ) -> bool:
        """
        Validates that a table exists.
        """

        if not self.exists(table_name):

            raise ValueError(f"Table '{table_name}' does not exist.")

        return True

    def get_table_range(
        self,
        table_name: str,
    ) -> str:
        """
        Returns the Excel range occupied by a table.
        """

        _, table = self.get_table_and_sheet(table_name)

        return table.ref

    def get_headers(
        self,
        table_name: str,
    ) -> list[str]:
        """
        Returns the table headers.
        """

        worksheet, table = self.get_table_and_sheet(table_name)

        min_col, min_row, max_col, _ = range_boundaries(table.ref)

        assert min_col is not None
        assert min_row is not None
        assert max_col is not None

        start_row = min_row
        start_col = min_col
        end_col = max_col

        headers: list[str] = []

        for column in range(
            start_col,
            end_col + 1,
        ):

            value = worksheet.cell(
                row=start_row,
                column=column,
            ).value

            headers.append("" if value is None else str(value))
        return headers

    def get_data_rows(
        self,
        table_name: str,
    ) -> list[tuple]:
        """
        Returns every data row from the table.
        Header row is excluded.
        """

        worksheet, table = self.get_table_and_sheet(table_name)

        min_col, min_row, max_col, max_row = range_boundaries(
            table.ref
        )

        assert min_col is not None
        assert min_row is not None
        assert max_col is not None
        assert max_row is not None

        first_row = min_row + 1
        last_row = max_row

        first_col = min_col
        last_col = max_col

        rows = list(
            worksheet.iter_rows(
                min_row=first_row,
                max_row=last_row,
                min_col=first_col,
                max_col=last_col,
                values_only=True,
            )
        )

        return rows

    def read_table(
        self,
        table_name: str,
    ) -> list[dict[str, Any]]:
        """
        Reads an Excel table into dictionaries.
        """

        headers = self.get_headers(table_name)

        rows = self.get_data_rows(table_name)

        records: list[dict[str, Any]] = []

        for row in rows:

            records.append(
                dict(
                    zip(
                        headers,
                        row,
                    )
                )
            )

        return records

    # ======================================================
    # Table Search
    # ======================================================
    def find_by_value(
        self,
        table_name: str,
        column_name: str,
        value: Any,
    ) -> dict[str, Any] | None:
        """
        Returns the first matching record.
        """

        records = self.read_table(table_name)

        for record in records:

            if record.get(column_name) == value:
                return record

        return None

    def filter_by_value(
        self,
        table_name: str,
        column_name: str,
        value: Any,
    ) -> list[dict[str, Any]]:
        """
        Returns every matching record.
        """

        records = self.read_table(table_name)

        return [record for record in records if record.get(column_name) == value]

    def record_exists(
        self,
        table_name: str,
        column_name: str,
        value: Any,
    ) -> bool:
        """
        Determines whether a record exists.
        """

        return (
            self.find_by_value(
                table_name,
                column_name,
                value,
            )
            is not None
        )

    def row_count(
        self,
        table_name: str,
    ) -> int:
        """
        Returns the number of data rows.
        """

        return len(self.get_data_rows(table_name))

    # ======================================================
    # Table Write Operations
    # ======================================================

    def append_row(
        self,
        table_name: str,
        data: dict[str, Any],
    ) -> None:
        """
        Appends a row to an Excel table.
        """

        worksheet, _ = self.get_table_and_sheet(table_name)

        headers = self.get_headers(table_name)

        row = [data.get(header) for header in headers]

        worksheet.append(row)

        self.workbook_manager.mark_modified()

    def clear_table(
        self,
        table_name: str,
    ) -> None:
        """
        Removes every data row while preserving headers.
        """

        worksheet, table = self.get_table_and_sheet(table_name)

        min_col, min_row, max_col, max_row = range_boundaries(table.ref)

        assert min_row is not None
        assert max_row is not None

        first_data_row = min_row + 1

        for row in range(
            max_row,
            first_data_row - 1,
            -1,
        ):
            worksheet.delete_rows(row)

        self.workbook_manager.mark_modified()

    # ======================================================
    # Utilities
    # ======================================================

    def refresh(
        self,
    ) -> None:
        """
        Reserved for future workbook refresh logic.
        """

        pass

    def save(
        self,
    ) -> None:

        self.workbook_manager.save()

    def save_as(
        self,
        file_path: str,
    ) -> None:

        self.workbook_manager.save_as(file_path)

    def close(
        self,
    ) -> None:

        self.workbook_manager.close()
