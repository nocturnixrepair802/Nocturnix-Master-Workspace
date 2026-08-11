from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
from desktop.views.customer_devices_dialog import CustomerDevicesDialog


class CustomerDialog(QDialog):
    def __init__(
        self,
        service: RepairService,
        customer_id: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.service: RepairService = service
        self.customer_id: str | None = customer_id
        self.customer: dict[str, Any] | None = None

        if self.customer_id is not None:
            customer = self.service.get_customer(self.customer_id)

            if customer is None:
                raise ValueError(f"Customer not found: " f"{self.customer_id}")

            self.customer = customer

        if self.customer_id is None:
            self.setWindowTitle("New Customer")
        else:
            self.setWindowTitle(f"Edit Customer - " f"{self.customer_id}")

        self.resize(
            620,
            720,
        )

        self._build_ui()
        self._load_customer()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        if self.customer_id is None:
            heading_text = "New Customer"
        else:
            heading_text = f"Customer " f"{self.customer_id}"

        heading = QLabel(heading_text)

        heading.setObjectName("pageTitle")

        layout.addWidget(heading)

        form = QFormLayout()

        self.customer_type = QComboBox()

        self.customer_type.addItems(
            [
                "Individual",
                "Business",
            ]
        )

        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.business_name = QLineEdit()
        self.email = QLineEdit()
        self.mobile_phone = QLineEdit()
        self.home_phone = QLineEdit()
        self.work_phone = QLineEdit()

        self.preferred_contact = QComboBox()

        self.preferred_contact.addItems(
            [
                "Mobile Phone",
                "Home Phone",
                "Work Phone",
                "Email",
            ]
        )

        self.billing_address = QTextEdit()
        self.billing_address.setFixedHeight(80)

        self.shipping_address = QTextEdit()
        self.shipping_address.setFixedHeight(80)

        self.tax_exempt = QCheckBox()

        self.active = QCheckBox()
        self.active.setChecked(True)

        self.notes = QTextEdit()
        self.notes.setFixedHeight(120)

        form.addRow(
            "Customer Type",
            self.customer_type,
        )

        form.addRow(
            "First Name",
            self.first_name,
        )

        form.addRow(
            "Last Name",
            self.last_name,
        )

        form.addRow(
            "Business Name",
            self.business_name,
        )

        form.addRow(
            "Email",
            self.email,
        )

        form.addRow(
            "Mobile Phone",
            self.mobile_phone,
        )

        form.addRow(
            "Home Phone",
            self.home_phone,
        )

        form.addRow(
            "Work Phone",
            self.work_phone,
        )

        form.addRow(
            "Preferred Contact",
            self.preferred_contact,
        )

        form.addRow(
            "Billing Address",
            self.billing_address,
        )

        form.addRow(
            "Shipping Address",
            self.shipping_address,
        )

        form.addRow(
            "Tax Exempt",
            self.tax_exempt,
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

    def _load_customer(self) -> None:
        customer = self.customer

        if customer is None:
            return

        self._select_combo_value(
            self.customer_type,
            str(
                customer.get(
                    "customer_type",
                    "Individual",
                )
                or "Individual"
            ),
        )

        self.first_name.setText(
            str(
                customer.get(
                    "first_name",
                    "",
                )
                or ""
            )
        )

        self.last_name.setText(
            str(
                customer.get(
                    "last_name",
                    "",
                )
                or ""
            )
        )

        self.business_name.setText(
            str(
                customer.get(
                    "business_name",
                    "",
                )
                or ""
            )
        )

        self.email.setText(
            str(
                customer.get(
                    "email",
                    "",
                )
                or ""
            )
        )

        self.mobile_phone.setText(
            str(
                customer.get(
                    "mobile_phone",
                    "",
                )
                or ""
            )
        )

        self.home_phone.setText(
            str(
                customer.get(
                    "home_phone",
                    "",
                )
                or ""
            )
        )

        self.work_phone.setText(
            str(
                customer.get(
                    "work_phone",
                    "",
                )
                or ""
            )
        )

        self._select_combo_value(
            self.preferred_contact,
            str(
                customer.get(
                    "preferred_contact",
                    "Mobile Phone",
                )
                or "Mobile Phone"
            ),
        )

        self.billing_address.setPlainText(
            str(
                customer.get(
                    "billing_address",
                    "",
                )
                or ""
            )
        )

        self.shipping_address.setPlainText(
            str(
                customer.get(
                    "shipping_address",
                    "",
                )
                or ""
            )
        )

        self.tax_exempt.setChecked(
            bool(
                customer.get(
                    "tax_exempt",
                    0,
                )
            )
        )

        self.active.setChecked(
            bool(
                customer.get(
                    "active",
                    1,
                )
            )
        )

        self.notes.setPlainText(
            str(
                customer.get(
                    "notes",
                    "",
                )
                or ""
            )
        )

    @staticmethod
    def _select_combo_value(
        combo: QComboBox,
        value: str,
    ) -> None:
        index = combo.findText(
            value,
            Qt.MatchFlag.MatchFixedString,
        )

        if index >= 0:
            combo.setCurrentIndex(index)

    def _values(
        self,
    ) -> dict[str, Any]:
        return {
            "customer_type": self.customer_type.currentText(),
            "first_name": self.first_name.text(),
            "last_name": self.last_name.text(),
            "business_name": self.business_name.text(),
            "email": self.email.text(),
            "mobile_phone": self.mobile_phone.text(),
            "home_phone": self.home_phone.text(),
            "work_phone": self.work_phone.text(),
            "preferred_contact": self.preferred_contact.currentText(),
            "billing_address": self.billing_address.toPlainText(),
            "shipping_address": self.shipping_address.toPlainText(),
            "tax_exempt": self.tax_exempt.isChecked(),
            "active": self.active.isChecked(),
            "notes": self.notes.toPlainText(),
        }

    def _save(self) -> None:
        try:
            if self.customer_id is None:
                customer = self.service.create_customer(self._values())

                self.customer_id = str(customer["customer_id"])

                message = f"{self.customer_id} " "was created successfully."
            else:
                self.service.update_customer(
                    self.customer_id,
                    self._values(),
                )

                message = f"{self.customer_id} " "was saved successfully."

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Customer Save Failed",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Customer Saved",
            message,
        )

        self.accept()


class CustomersView(QWidget):
    def __init__(
        self,
        service: RepairService,
    ) -> None:
        super().__init__()

        self.service: RepairService = service

        self.customers: list[dict[str, Any]] = []

        self.filtered_customers: list[dict[str, Any]] = []

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

        title = QLabel("Customers")

        title.setObjectName("pageTitle")

        subtitle = QLabel("Search and manage customer records.")

        subtitle.setObjectName("mutedText")

        root.addWidget(title)

        root.addWidget(subtitle)

        filters = QHBoxLayout()
        filters.setSpacing(10)

        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(
            "Search customer ID, name, business, " "email, or phone..."
        )

        self.search_box.textChanged.connect(self._apply_filters)

        self.active_filter = QComboBox()

        self.active_filter.addItems(
            [
                "All Customers",
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

        new_button = QPushButton("＋ New Customer")

        new_button.setObjectName("primaryButton")

        new_button.clicked.connect(self._new_customer)

        edit_button = QPushButton("Edit Selected Customer")

        edit_button.clicked.connect(self._edit_selected_customer)

        devices_button = QPushButton("View Devices")

        devices_button.clicked.connect(self._view_devices)

        actions.addWidget(new_button)

        actions.addWidget(edit_button)

        actions.addWidget(devices_button)

        actions.addStretch(1)

        root.addLayout(actions)

        self.table = QTableWidget()

        self.table.setColumnCount(7)

        self.table.setHorizontalHeaderLabels(
            [
                "Customer ID",
                "First Name",
                "Last Name",
                "Business",
                "Email",
                "Mobile Phone",
                "Type",
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

        self.table.doubleClicked.connect(self._edit_selected_customer)

        root.addWidget(
            self.table,
            1,
        )

    def refresh(self) -> None:
        selected_customer = self._selected_customer_id()

        self.customers = self.service.list_customers()

        self._apply_filters()

        if selected_customer is not None:
            self._select_customer(selected_customer)

    def _apply_filters(
        self,
        *_args: object,
    ) -> None:
        query = self.search_box.text().strip().casefold()

        active_filter = self.active_filter.currentText()

        filtered: list[dict[str, Any]] = []

        for customer in self.customers:
            active = bool(
                customer.get(
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
                            customer.get(
                                "customer_id",
                                "",
                            )
                            or ""
                        ),
                        str(
                            customer.get(
                                "first_name",
                                "",
                            )
                            or ""
                        ),
                        str(
                            customer.get(
                                "last_name",
                                "",
                            )
                            or ""
                        ),
                        str(
                            customer.get(
                                "business_name",
                                "",
                            )
                            or ""
                        ),
                        str(
                            customer.get(
                                "email",
                                "",
                            )
                            or ""
                        ),
                        str(
                            customer.get(
                                "mobile_phone",
                                "",
                            )
                            or ""
                        ),
                    ]
                ).casefold()

                if query not in haystack:
                    continue

            filtered.append(customer)

        self.filtered_customers = filtered

        self._render_table()

    def _render_table(self) -> None:
        self.table.setRowCount(len(self.filtered_customers))

        for row_index, customer in enumerate(self.filtered_customers):
            values = [
                customer.get(
                    "customer_id",
                    "",
                ),
                customer.get(
                    "first_name",
                    "",
                ),
                customer.get(
                    "last_name",
                    "",
                ),
                customer.get(
                    "business_name",
                    "",
                ),
                customer.get(
                    "email",
                    "",
                ),
                customer.get(
                    "mobile_phone",
                    "",
                ),
                customer.get(
                    "customer_type",
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
            f"{len(self.filtered_customers)} "
            f"of {len(self.customers)} "
            "customers shown"
        )

    def _selected_customer_id(
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

    def _select_customer(
        self,
        customer_id: str,
    ) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(
                row,
                0,
            )

            if item is not None and item.text() == customer_id:
                self.table.selectRow(row)
                return

    def _new_customer(
        self,
    ) -> None:
        dialog = CustomerDialog(
            service=self.service,
            parent=self,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit_selected_customer(
        self,
        *_args: object,
    ) -> None:
        customer_id = self._selected_customer_id()

        if customer_id is None:
            QMessageBox.information(
                self,
                "Select Customer",
                "Select a customer first.",
            )
            return

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

            self._select_customer(customer_id)

    def _view_devices(
        self,
    ) -> None:
        customer_id = self._selected_customer_id()

        if customer_id is None:
            QMessageBox.information(
                self,
                "Select Customer",
                "Select a customer first.",
            )
            return

        try:
            dialog = CustomerDevicesDialog(
                service=self.service,
                customer_id=customer_id,
                parent=self,
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Open Devices",
                str(exc),
            )
            return

        dialog.exec()

        self.refresh()

        self._select_customer(customer_id)
