from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.services.repair_service import RepairService
from desktop.views.customer_devices_dialog import DeviceDialog
from desktop.views.customers_view import CustomerDialog
from desktop.views.repair_dialog import NewRepairDialog


class DevicesView(QWidget):
    def __init__(
        self,
        service: RepairService,
    ) -> None:
        super().__init__()

        self.service: RepairService = service

        self.devices: list[dict[str, Any]] = []

        self.filtered_devices: list[dict[str, Any]] = []

        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        root.setContentsMargins(
            22,
            20,
            22,
            22,
        )

        root.setSpacing(12)

        title = QLabel("Devices")
        title.setObjectName("pageTitle")

        subtitle = QLabel("Search and manage all customer devices.")
        subtitle.setObjectName("mutedText")

        root.addWidget(title)
        root.addWidget(subtitle)

        filters = QHBoxLayout()
        filters.setSpacing(10)

        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(
            "Search device ID, customer, manufacturer, "
            "model, serial, IMEI, color, storage, or carrier..."
        )

        self.search_box.textChanged.connect(self._apply_filters)

        self.active_filter = QComboBox()

        self.active_filter.addItems(
            [
                "All Devices",
                "Active",
                "Inactive",
            ]
        )

        self.active_filter.currentTextChanged.connect(self._apply_filters)

        refresh_button = QPushButton("Refresh")

        refresh_button.clicked.connect(self.refresh)

        filters.addWidget(
            self.search_box,
            1,
        )

        filters.addWidget(self.active_filter)

        filters.addWidget(refresh_button)

        root.addLayout(filters)

        self.result_label = QLabel()
        self.result_label.setObjectName("mutedText")

        root.addWidget(self.result_label)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        self.edit_button = QPushButton("Edit Selected Device")

        self.edit_button.setObjectName("primaryButton")

        self.edit_button.clicked.connect(self._edit_selected_device)

        self.customer_button = QPushButton("View Customer")

        self.customer_button.clicked.connect(self._view_customer)

        self.repair_button = QPushButton("＋ New Repair")

        self.repair_button.clicked.connect(self._new_repair)

        actions.addWidget(self.edit_button)

        actions.addWidget(self.customer_button)

        actions.addWidget(self.repair_button)

        actions.addStretch(1)

        root.addLayout(actions)

        self.table = QTableWidget()

        self.table.setColumnCount(10)

        self.table.setHorizontalHeaderLabels(
            [
                "Device ID",
                "Customer",
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

        self.table.setStyleSheet("""
            QTableWidget {
                font-size: 8pt;
            }

            QTableWidget::item {
                padding: 2px 4px;
            }

            QHeaderView::section {
                font-size: 8pt;
                padding: 4px 5px;
            }
            """)

        self.table.setWordWrap(False)

        self.table.setTextElideMode(Qt.TextElideMode.ElideRight)

        self.table.verticalHeader().setDefaultSectionSize(24)

        self.table.verticalHeader().setMinimumSectionSize(22)

        header = self.table.horizontalHeader()

        for column in range(self.table.columnCount()):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        header.setStretchLastSection(True)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.table.setAlternatingRowColors(True)

        self.table.doubleClicked.connect(self._edit_selected_device)

        root.addWidget(
            self.table,
            1,
        )

    def refresh(self) -> None:
        selected_device = self._selected_device_id()

        self.devices = self.service.list_all_devices()

        self._apply_filters()

        if selected_device is not None:
            self._select_device(selected_device)

    def _apply_filters(
        self,
        *_args: object,
    ) -> None:
        query = self.search_box.text().strip().casefold()

        active_filter = self.active_filter.currentText()

        filtered: list[dict[str, Any]] = []

        for device in self.devices:
            active = bool(
                device.get(
                    "active",
                    0,
                )
            )

            if active_filter == "Active" and not active:
                continue

            if active_filter == "Inactive" and active:
                continue

            if query:
                haystack = " ".join(
                    [
                        str(
                            device.get(
                                "device_id",
                                "",
                            )
                            or ""
                        ),
                        str(
                            device.get(
                                "customer_id",
                                "",
                            )
                            or ""
                        ),
                        str(
                            device.get(
                                "first_name",
                                "",
                            )
                            or ""
                        ),
                        str(
                            device.get(
                                "last_name",
                                "",
                            )
                            or ""
                        ),
                        str(
                            device.get(
                                "business_name",
                                "",
                            )
                            or ""
                        ),
                        str(
                            device.get(
                                "manufacturer",
                                "",
                            )
                            or ""
                        ),
                        str(
                            device.get(
                                "device_family",
                                "",
                            )
                            or ""
                        ),
                        str(
                            device.get(
                                "device_model",
                                "",
                            )
                            or ""
                        ),
                        str(
                            device.get(
                                "serial_number",
                                "",
                            )
                            or ""
                        ),
                        str(
                            device.get(
                                "imei_service_tag",
                                "",
                            )
                            or ""
                        ),
                        str(
                            device.get(
                                "color",
                                "",
                            )
                            or ""
                        ),
                        str(
                            device.get(
                                "storage",
                                "",
                            )
                            or ""
                        ),
                        str(
                            device.get(
                                "carrier",
                                "",
                            )
                            or ""
                        ),
                    ]
                ).casefold()

                if query not in haystack:
                    continue

            filtered.append(device)

        self.filtered_devices = filtered

        self._render_table()

    def _render_table(self) -> None:
        self.table.setRowCount(len(self.filtered_devices))

        for row_index, device in enumerate(self.filtered_devices):
            customer_name = self._customer_name(device)

            values = [
                device.get(
                    "device_id",
                    "",
                ),
                customer_name,
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
                text = str(value or "")

                item = QTableWidgetItem(text)

                if text:
                    item.setToolTip(text)

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.result_label.setText(
            f"{len(self.filtered_devices)} " f"of {len(self.devices)} " "devices shown"
        )

    @staticmethod
    def _customer_name(
        device: dict[str, Any],
    ) -> str:
        first_name = str(
            device.get(
                "first_name",
                "",
            )
            or ""
        ).strip()

        last_name = str(
            device.get(
                "last_name",
                "",
            )
            or ""
        ).strip()

        business_name = str(
            device.get(
                "business_name",
                "",
            )
            or ""
        ).strip()

        name = " ".join(
            part
            for part in (
                first_name,
                last_name,
            )
            if part
        )

        if name:
            return name

        if business_name:
            return business_name

        return str(
            device.get(
                "customer_id",
                "",
            )
            or ""
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

    def _selected_device(
        self,
    ) -> dict[str, Any] | None:
        device_id = self._selected_device_id()

        if device_id is None:
            return None

        for device in self.devices:
            if (
                str(
                    device.get(
                        "device_id",
                        "",
                    )
                )
                == device_id
            ):
                return device

        return None

    def _select_device(
        self,
        device_id: str,
    ) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(
                row,
                0,
            )

            if item is not None and item.text() == device_id:
                self.table.selectRow(row)
                return

    def _edit_selected_device(
        self,
        *_args: object,
    ) -> None:
        device = self._selected_device()

        if device is None:
            QMessageBox.information(
                self,
                "Select Device",
                "Select a device first.",
            )
            return

        device_id = str(device["device_id"])

        customer_id = str(device["customer_id"])

        try:
            dialog = DeviceDialog(
                service=self.service,
                customer_id=customer_id,
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

            self._select_device(device_id)

    def _view_customer(self) -> None:
        device = self._selected_device()

        if device is None:
            QMessageBox.information(
                self,
                "Select Device",
                "Select a device first.",
            )
            return

        customer_id = str(device["customer_id"])

        try:
            dialog = CustomerDialog(
                service=self.service,
                customer_id=customer_id,
                parent=self,
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Open Customer",
                str(exc),
            )
            return

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _new_repair(self) -> None:
        device = self._selected_device()

        if device is None:
            QMessageBox.information(
                self,
                "Select Device",
                "Select a device first.",
            )
            return

        customer_id = str(device["customer_id"])

        device_id = str(device["device_id"])

        try:
            dialog = NewRepairDialog(
                service=self.service,
                customer_id=customer_id,
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
