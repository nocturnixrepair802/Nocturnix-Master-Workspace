from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from api.schemas import (
    CustomerCreateRequest,
    CustomerDeviceCreateRequest,
    RepairCreateRequest,
)
from app import Application


def _next_numeric_id(
    table: pd.DataFrame,
    column: str,
    *,
    start: int,
) -> int:
    if table.empty or column not in table.columns:
        return start

    raw_values = table.loc[:, column]

    if isinstance(raw_values, pd.DataFrame):
        raw_values = raw_values.iloc[:, 0]

    source = pd.Series(
        raw_values,
        index=table.index,
        dtype="object",
    )

    numeric = pd.to_numeric(
        source,
        errors="coerce",
    )

    numeric_series = pd.Series(
        numeric,
        index=source.index,
        dtype="float64",
    ).dropna()

    if numeric_series.empty:
        return start

    maximum = float(numeric_series.max())

    return int(maximum) + 1


class RepairApiOperations:
    def __init__(
        self,
        application: Application,
    ) -> None:
        self.application = application

    def create_customer(
        self,
        request: CustomerCreateRequest,
    ) -> dict[str, Any]:
        repository = self.application.repositories.customers

        customer_id = _next_numeric_id(
            repository.table,
            "Customer ID",
            start=1000,
        )

        now = datetime.now()

        record: dict[str, Any] = {
            "Customer ID": customer_id,
            "Customer Type": request.customer_type,
            "First Name": request.first_name,
            "Last Name": request.last_name,
            "Business Name": request.business_name,
            "Email": request.email,
            "Mobile Phone": request.mobile_phone,
            "Home Phone": "",
            "Work Phone": "",
            "Preferred Contact": "Mobile Phone",
            "Billing Address": "",
            "Shipping Address": "",
            "Tax Exempt": False,
            "Active": True,
            "Date Created": now,
            "Last Modified": now,
            "Notes": request.notes,
        }

        repository.append(record)

        return record

    def create_customer_device(
        self,
        request: CustomerDeviceCreateRequest,
    ) -> dict[str, Any]:
        customer = self.application.services.customers.get(request.customer_id)

        if customer is None:
            raise LookupError(f"Customer {request.customer_id!r} does not exist.")

        repository = self.application.repositories.customer_devices

        device_id = _next_numeric_id(
            repository.table,
            "Device ID",
            start=1000,
        )

        record: dict[str, Any] = {
            "Device ID": device_id,
            "Customer ID": request.customer_id,
            "Device Type": request.device_type,
            "Manufacturer": request.manufacturer,
            "Model": request.model,
            "Serial Number": request.serial_number,
            "IMEI / Serial Number": request.serial_number,
            "Notes": request.notes,
        }

        repository.append(record)

        return record

    def create_repair(
        self,
        request: RepairCreateRequest,
    ) -> dict[str, Any]:
        customer = self.application.services.customers.get(request.customer_id)

        if customer is None:
            raise LookupError(f"Customer {request.customer_id!r} does not exist.")

        device = self.application.services.customer_devices.get(request.device_id)

        if device is None:
            raise LookupError(f"Device {request.device_id!r} does not exist.")

        device_customer_id = device.get("Customer ID")

        if device_customer_id != request.customer_id:
            raise ValueError(
                "The selected device does not belong to the selected customer."
            )

        repository = self.application.repositories.repairs

        ticket_id = _next_numeric_id(
            repository.table,
            "Ticket ID",
            start=1000,
        )

        now = datetime.now()

        record: dict[str, Any] = {
            "Ticket ID": ticket_id,
            "Customer ID": request.customer_id,
            "Device ID": request.device_id,
            "Repair Status": request.repair_status,
            "Problem Description": (request.problem_description),
            "Technician Notes": (request.technician_notes),
            "Estimated Cost": (request.estimated_cost),
            "Date Created": now,
            "Last Modified": now,
        }

        repository.append(record)

        return record
