from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd


def json_value(
    value: Any,
) -> Any:
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except TypeError, ValueError:
        pass

    if isinstance(
        value,
        datetime | date,
    ):
        return value.isoformat()

    if hasattr(value, "item"):
        try:
            return value.item()
        except TypeError, ValueError:
            pass

    return value


def record_from_series(
    row: pd.Series,
) -> dict[str, Any]:
    return {str(key): json_value(value) for key, value in row.items()}


def records_from_dataframe(
    table: pd.DataFrame,
) -> list[dict[str, Any]]:
    return [
        {str(key): json_value(value) for key, value in row.items()}
        for row in table.to_dict(orient="records")
    ]
