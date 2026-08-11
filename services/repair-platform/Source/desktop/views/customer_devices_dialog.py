from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop.services.repair_service import RepairService
from desktop.views.repair_dialog import (
    NewRepairDialog,
)


class DeviceDialog(QDialog):
    def __init__(
        self,
        service: RepairService,
        customer_id: str,
        device_id: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.service: RepairService = service
        self.customer_id: str = customer_id
        self.device_id: str | None = device_id
        self.device: dict[str, Any] | None = None

        if self.device_id is not None:
            device = self.service.get_device(self.device_id)

            if device is None:
                raise ValueError(f"Device not found: " f"{self.device_id}")

            if str(device["customer_id"]) != self.customer_id:
                raise ValueError(
                    "The selected device does not " "belong to this customer."
                )

            self.device = device

        if self.device_id is None:
            self.setWindowTitle(f"New Device - {customer_id}")
        else:
            self.setWindowTitle(f"Edit Device - {self.device_id}")

        self.resize(560, 650)

        self._build_ui()
        self._load_device()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        if self.device_id is None:
            heading_text = f"New Device for {self.customer_id}"
        else:
            heading_text = f"Device {self.device_id}"

        heading = QLabel(heading_text)
        heading.setStyleSheet("font-size: 20px; font-weight: 700;")

        layout.addWidget(heading)

        form = QFormLayout()

        self.manufacturer = QLineEdit()
        self.device_family = QLineEdit()
        self.device_model = QLineEdit()
        self.serial_number = QLineEdit()
        self.imei_service_tag = QLineEdit()
        self.color = QLineEdit()
        self.storage = QLineEdit()
        self.carrier = QLineEdit()
        self.purchase_date = QLineEdit()
        self.warranty_expiration = QLineEdit()
        self.catalog_device_id = QLineEdit()

        self.active = QCheckBox()
        self.active.setChecked(True)

        self.notes = QTextEdit()
        self.notes.setFixedHeight(100)

        self.purchase_date.setPlaceholderText("YYYY-MM-DD")

        self.warranty_expiration.setPlaceholderText("YYYY-MM-DD")

        form.addRow(
            "Manufacturer",
            self.manufacturer,
        )
        form.addRow(
            "Device Family",
            self.device_family,
        )
        form.addRow(
            "Device Model",
            self.device_model,
        )
        form.addRow(
            "Serial Number",
            self.serial_number,
        )
        form.addRow(
            "IMEI / Service Tag",
            self.imei_service_tag,
        )
        form.addRow(
            "Color",
            self.color,
        )
        form.addRow(
            "Storage",
            self.storage,
        )
        form.addRow(
            "Carrier",
            self.carrier,
        )
        form.addRow(
            "Purchase Date",
            self.purchase_date,
        )
        form.addRow(
            "Warranty Expiration",
            self.warranty_expiration,
        )
        form.addRow(
            "Catalog Device ID",
            self.catalog_device_id,
        )
        form.addRow(
            "Active",
            self.active,
        )
        form.addRow(
            "Notes",
            self.notes,
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self._save)

        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def _load_device(self) -> None:
        device = self.device

        if device is None:
            return

        self.manufacturer.setText(
            str(
                device.get(
                    "manufacturer",
                    "",
                )
                or ""
            )
        )

        self.device_family.setText(
            str(
                device.get(
                    "device_family",
                    "",
                )
                or ""
            )
        )

        self.device_model.setText(
            str(
                device.get(
                    "device_model",
                    "",
                )
                or ""
            )
        )

        self.serial_number.setText(
            str(
                device.get(
                    "serial_number",
                    "",
                )
                or ""
            )
        )

        self.imei_service_tag.setText(
            str(
                device.get(
                    "imei_service_tag",
                    "",
                )
                or ""
            )
        )

        self.color.setText(
            str(
                device.get(
                    "color",
                    "",
                )
                or ""
            )
        )

        self.storage.setText(
            str(
                device.get(
                    "storage",
                    "",
                )
                or ""
            )
        )

        self.carrier.setText(
            str(
                device.get(
                    "carrier",
                    "",
                )
                or ""
            )
        )

        self.purchase_date.setText(
            str(
                device.get(
                    "purchase_date",
                    "",
                )
                or ""
            )
        )

        self.warranty_expiration.setText(
            str(
                device.get(
                    "warranty_expiration",
                    "",
                )
                or ""
            )
        )

        self.catalog_device_id.setText(
            str(
                device.get(
                    "catalog_device_id",
                    "",
                )
                or ""
            )
        )

        self.active.setChecked(
            bool(
                device.get(
                    "active",
                    1,
                )
            )
        )

        self.notes.setPlainText(
            str(
                device.get(
                    "notes",
                    "",
                )
                or ""
            )
        )

    def _values(self) -> dict[str, Any]:
        return {
            "manufacturer": self.manufacturer.text(),
            "device_family": self.device_family.text(),
            "device_model": self.device_model.text(),
            "serial_number": self.serial_number.text(),
            "imei_service_tag": self.imei_service_tag.text(),
            "color": self.color.text(),
            "storage": self.storage.text(),
            "carrier": self.carrier.text(),
            "purchase_date": self.purchase_date.text(),
            "warranty_expiration": self.warranty_expiration.text(),
            "catalog_device_id": self.catalog_device_id.text(),
            "active": self.active.isChecked(),
            "notes": self.notes.toPlainText(),
        }

    def _save(self) -> None:
        try:
            if self.device_id is None:
                device = self.service.create_device(
                    self.customer_id,
                    self._values(),
                )

                self.device_id = str(device["device_id"])

                message = f"{self.device_id} was " "created successfully."
            else:
                self.service.update_device(
                    self.device_id,
                    self._values(),
                )

                message = f"{self.device_id} was " "saved successfully."

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Device Save Failed",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Device Saved",
            message,
        )

        self.accept()


class CustomerDevicesDialog(QDialog):
    def __init__(
        self,
        service: RepairService,
        customer_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.service: RepairService = service
        self.customer_id: str = customer_id

        customer = self.service.get_customer(self.customer_id)

        if customer is None:
            raise ValueError(f"Customer not found: " f"{self.customer_id}")

        self.customer: dict[str, Any] = customer

        self.setWindowTitle(f"Customer Devices - {customer_id}")
        self.resize(1050, 600)

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        customer_name = " ".join(
            part
            for part in (
                str(
                    self.customer.get(
                        "first_name",
                        "",
                    )
                    or ""
                ).strip(),
                str(
                    self.customer.get(
                        "last_name",
                        "",
                    )
                    or ""
                ).strip(),
            )
            if part
        )

        if not customer_name:
            customer_name = str(
                self.customer.get(
                    "business_name",
                    "",
                )
                or self.customer_id
            )

        heading = QLabel(f"Devices — {customer_name}")
        heading.setStyleSheet("font-size: 22px; font-weight: 700;")

        layout.addWidget(heading)

        actions = QHBoxLayout()

        new_button = QPushButton("New Device")
        new_button.clicked.connect(self._new_device)
        actions.addWidget(new_button)

        edit_button = QPushButton("Edit Selected Device")
        edit_button.clicked.connect(self._edit_selected_device)
        actions.addWidget(edit_button)

        repair_button = QPushButton(
        "New Repair"
        )
        repair_button.clicked.connect(
            self._new_repair
        )
        actions.addWidget(repair_button)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        actions.addWidget(refresh_button)

        actions.addStretch(1)

        layout.addLayout(actions)

        self.table = QTableWidget()
        self.table.setColumnCount(9)

        self.table.setHorizontalHeaderLabels(
            [
                "Device ID",
                "Manufacturer",
                "Family",
                "Model",
                "Serial",
                "IMEI / Service Tag",
                "Color",
                "Storage",
                "Carrier",
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.table.doubleClicked.connect(self._edit_selected_device)

        layout.addWidget(self.table)

        close_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)

        close_buttons.rejected.connect(self.reject)

        layout.addWidget(close_buttons)

    def refresh(self) -> None:
        devices = self.service.list_customer_devices(self.customer_id)

        self.table.setRowCount(len(devices))

        for row_index, device in enumerate(devices):
            values = [
                device.get(
                    "device_id",
                    "",
                ),
                device.get(
                    "manufacturer",
                    "",
                ),
                device.get(
                    "device_family",
                    "",
                ),
                device.get(
                    "device_model",
                    "",
                ),
                device.get(
                    "serial_number",
                    "",
                ),
                device.get(
                    "imei_service_tag",
                    "",
                ),
                device.get(
                    "color",
                    "",
                ),
                device.get(
                    "storage",
                    "",
                ),
                device.get(
                    "carrier",
                    "",
                ),
            ]

            for column_index, value in enumerate(values):
                self.table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(str(value or "")),
                )

    def _selected_device_id(
        self,
    ) -> str | None:
        row = self.table.currentRow()

        if row < 0:
            return None

        item = self.table.item(
            row,
            0,
        )

        if item is None:
            return None

        value = item.text().strip()

        return value or None

    def _new_device(self) -> None:
        dialog = DeviceDialog(
            service=self.service,
            customer_id=self.customer_id,
            parent=self,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit_selected_device(
        self,
        *_args: object,
    ) -> None:
        device_id = self._selected_device_id()

        if device_id is None:
            QMessageBox.information(
                self,
                "Select Device",
                "Select a device first.",
            )
            return

        try:
            dialog = DeviceDialog(
                service=self.service,
                customer_id=self.customer_id,
                device_id=device_id,
                parent=self,
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Open Device",
                str(exc),
            )
            return

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _new_repair(self) -> None:
        device_id = self._selected_device_id()

        if device_id is None:
            QMessageBox.information(
                self,
                "Select Device",
                "Select a device first.",
            )
            return

        try:
            dialog = NewRepairDialog(
                service=self.service,
                customer_id=self.customer_id,
                device_id=device_id,
                parent=self,
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Create Repair",
                str(exc),
            )
            return

        dialog.exec()
