"""Read Excel tables without rewriting workbook formatting."""

from __future__ import annotations

from typing import Any

from openpyxl.utils import range_boundaries
from openpyxl.worksheet.worksheet import Worksheet

from .normalization import normalize_header


def table_headers(ws: Worksheet, ref: str) -> tuple[int, dict[str, int], dict[str, str]]:
    """Return table header row, normalized header map, and display names."""
    min_col, min_row, max_col, _ = range_boundaries(ref)
    columns: dict[str, int] = {}
    display: dict[str, str] = {}
    for col in range(min_col, max_col + 1):
        value = ws.cell(min_row, col).value
        key = normalize_header(value)
        if key:
            columns[key] = col
            display[key] = str(value)
    return min_row, columns, display


def row_values(ws: Worksheet, row_number: int, columns: dict[str, int]) -> dict[str, Any]:
    """Read a row by normalized column names."""
    return {key: ws.cell(row_number, col).value for key, col in columns.items()}
