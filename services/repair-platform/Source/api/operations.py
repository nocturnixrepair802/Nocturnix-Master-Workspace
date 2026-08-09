from __future__ import annotations

from datetime import (
    UTC,
    datetime,
)
from typing import Any

from api.schemas import (
    CustomerCreateRequest,
    CustomerDeviceCreateRequest,
    RepairCreateRequest,
)
from persistence.operations_db import (
    OperationsDatabase,
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class RepairApiOperations:
    def __init__(
        self,
        database: OperationsDatabase,
    ) -> None:
        self.database = database

    def create_customer(
        self,
        request: CustomerCreateRequest,
    ) -> dict[str, Any]:
        customer_id = self.database.next_id(
            table="customers",
            column="customer_id",
            prefix="CUS",
            width=6,
        )

        now = utc_now()

        record: dict[str, Any] = {
            "customer_id": customer_id,
            "customer_type": request.customer_type,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "business_name": request.business_name,
            "email": request.email,
            "mobile_phone": request.mobile_phone,
            "home_phone": "",
            "work_phone": "",
            "preferred_contact": "Mobile Phone",
            "billing_address": "",
            "shipping_address": "",
            "tax_exempt": 0,
            "active": 1,
            "date_created": now,
            "last_modified": now,
            "notes": request.notes,
        }

        return self.database.create_customer(record)

    def create_customer_device(
        self,
        request: CustomerDeviceCreateRequest,
    ) -> dict[str, Any]:
        customer_id = str(request.customer_id)

        customer = self.database.get_customer(customer_id)

        if customer is None:
            raise LookupError(f"Customer {customer_id!r} does not exist.")

        device_id = self.database.next_id(
            table=("customer_devices"),
            column="device_id",
            prefix="CDEV",
            width=6,
        )

        record: dict[str, Any] = {
            "device_id": device_id,
            "customer_id": customer_id,
            "catalog_device_id": request.catalog_device_id,
            "manufacturer": request.manufacturer,
            "device_family": request.device_type,
            "device_model": request.model,
            "serial_number": request.serial_number,
            "imei_service_tag": request.serial_number,
            "color": "",
            "storage": "",
            "carrier": "",
            "purchase_date": None,
            "warranty_expiration": None,
            "active": 1,
            "notes": request.notes,
        }

        return self.database.create_customer_device(record)

    def create_repair(
        self,
        request: RepairCreateRequest,
    ) -> dict[str, Any]:
        customer_id = str(request.customer_id)

        device_id = str(request.device_id)

        customer = self.database.get_customer(customer_id)

        if customer is None:
            raise LookupError(f"Customer {customer_id!r} does not exist.")

        device = self.database.get_customer_device(device_id)

        if device is None:
            raise LookupError(f"Device {device_id!r} does not exist.")

        if str(device["customer_id"]) != customer_id:
            raise ValueError(
                "The selected device does not belong to the selected customer."
            )

        ticket_id = self.database.next_id(
            table="repair_tickets",
            column="ticket_id",
            prefix="RPR",
            width=6,
        )

        now = utc_now()

        record: dict[str, Any] = {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "device_id": device_id,
            "repair_status": request.repair_status,
            "intake_date": now,
            "technician": "Ryan Brown",
            "priority": "Normal",
            "due_date": "",
            "problem_description": request.problem_description,
            "diagnosis": "",
            "estimated_cost": request.estimated_cost,
            "final_cost": None,
            "date_completed": None,
            "date_picked_up": None,
            "warranty": 0,
            "notes": request.technician_notes,
            "last_modified": now,
        }

        return self.database.create_repair(record)
