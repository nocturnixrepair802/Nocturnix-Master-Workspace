from __future__ import annotations
import sqlite3
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from core.database import Database


class PricingReviewPage(QWidget):
    """Review pricing records, margins, approval status, and publish readiness."""

    def __init__(self, database: Database) -> None:
        super().__init__()

        self.database = database

        main_layout = QVBoxLayout(self)

        heading = QLabel("Pricing Review")
        heading.setObjectName("pageHeading")
        main_layout.addWidget(heading)

        description = QLabel(
            "Review imported repair pricing, identify missing costs, "
            "inspect margins, and evaluate publish eligibility."
        )
        description.setWordWrap(True)
        main_layout.addWidget(description)

        filter_layout = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Search by service, device ID, manufacturer, or model..."
        )
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)

        self.cost_filter = QComboBox()
        self.cost_filter.addItems(
            [
                "All cost records",
                "Missing part cost",
                "Has part cost",
            ]
        )
        self.cost_filter.currentTextChanged.connect(self.refresh)

        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(160)
        self.status_filter.currentTextChanged.connect(self.refresh)

        self.eligibility_filter = QComboBox()
        self.eligibility_filter.addItems(
            [
                "All eligibility",
                "Publish eligible",
                "Not publish eligible",
            ]
        )
        self.eligibility_filter.currentTextChanged.connect(self.refresh)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.reload)

        filter_layout.addWidget(self.search, 1)
        filter_layout.addWidget(self.cost_filter)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(self.eligibility_filter)
        filter_layout.addWidget(refresh_button)

        main_layout.addLayout(filter_layout)

        summary_layout = QHBoxLayout()

        self.result_label = QLabel("0 pricing records")
        self.missing_cost_label = QLabel("Missing costs: 0")
        self.eligible_label = QLabel("Publish eligible: 0")

        summary_layout.addWidget(self.result_label)
        summary_layout.addStretch()
        summary_layout.addWidget(self.missing_cost_label)
        summary_layout.addWidget(self.eligible_label)

        main_layout.addLayout(summary_layout)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self.load_selected_record)

        splitter.addWidget(self.table)

        details_group = QGroupBox("Pricing Record Details")
        details_layout = QFormLayout(details_group)

        self.detail_service_id = QLabel("Select a pricing record")
        self.detail_service_name = QLabel("—")
        self.detail_service_type = QLabel("—")
        self.detail_device_id = QLabel("—")
        self.detail_device = QLabel("—")
        self.detail_part_cost = QLabel("—")
        self.detail_retail_price = QLabel("—")
        self.detail_gross_profit = QLabel("—")
        self.detail_margin = QLabel("—")
        self.detail_status = QLabel("—")
        self.detail_eligibility = QLabel("—")

        details_layout.addRow("Service ID:", self.detail_service_id)
        details_layout.addRow("Service name:", self.detail_service_name)
        details_layout.addRow("Service type:", self.detail_service_type)
        details_layout.addRow("Device ID:", self.detail_device_id)
        details_layout.addRow("Device:", self.detail_device)
        details_layout.addRow("Part cost:", self.detail_part_cost)
        details_layout.addRow("Retail price:", self.detail_retail_price)
        details_layout.addRow("Gross profit:", self.detail_gross_profit)
        details_layout.addRow("Gross margin:", self.detail_margin)
        details_layout.addRow("Approval status:", self.detail_status)
        details_layout.addRow(
            "Publish eligibility:",
            self.detail_eligibility,
        )

        approval_button_layout = QHBoxLayout()

        self.approve_button = QPushButton("Approve")
        self.approve_button.clicked.connect(
            lambda: self.set_approval_status("Approved")
        )

        self.reject_button = QPushButton("Reject")
        self.reject_button.clicked.connect(lambda: self.set_approval_status("Rejected"))

        self.approve_button.setEnabled(False)
        self.reject_button.setEnabled(False)

        approval_button_layout.addWidget(self.approve_button)
        approval_button_layout.addWidget(self.reject_button)
        approval_button_layout.addStretch()

        details_layout.addRow("Actions:", approval_button_layout)

        splitter.addWidget(details_group)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([500, 240])

        main_layout.addWidget(splitter, 1)

        self.load_statuses()
        self.refresh()

    def load_statuses(self) -> None:
        """Load distinct approval statuses from pricing records."""

        current_status = self.status_filter.currentText()

        rows = self.database.rows("""
            SELECT DISTINCT approval_status
            FROM pricing_records
            WHERE approval_status IS NOT NULL
              AND TRIM(approval_status) <> ''
            ORDER BY approval_status
            """)

        self.status_filter.blockSignals(True)
        self.status_filter.clear()
        self.status_filter.addItem("All statuses")

        for row in rows:
            value = str(row[0]).strip()

            if value:
                self.status_filter.addItem(value)

        index = self.status_filter.findText(current_status)

        if index >= 0:
            self.status_filter.setCurrentIndex(index)

        self.status_filter.blockSignals(False)

    def reload(self) -> None:
        """Reload filters and pricing data."""

        current_status = self.status_filter.currentText()
        current_cost = self.cost_filter.currentText()
        current_eligibility = self.eligibility_filter.currentText()
        current_search = self.search.text()

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        try:
            self.load_statuses()

            status_index = self.status_filter.findText(current_status)

            if status_index >= 0:
                self.status_filter.setCurrentIndex(status_index)

            self.cost_filter.setCurrentText(current_cost)
            self.eligibility_filter.setCurrentText(current_eligibility)
            self.search.setText(current_search)

            self.refresh()

            self.result_label.setText(
                f"{self.table.rowCount():,} pricing records — refreshed"
            )
        finally:
            QApplication.restoreOverrideCursor()

    def refresh(self) -> None:
        """Apply filters and refresh the pricing review table."""

        search_term = f"%{self.search.text().strip()}%"
        selected_cost = self.cost_filter.currentText()
        selected_status = self.status_filter.currentText()
        selected_eligibility = self.eligibility_filter.currentText()

        conditions = ["""
            (
                p.device_id LIKE ?
                OR s.service_id LIKE ?
                OR s.internal_name LIKE ?
                OR s.service_type_name LIKE ?
                OR d.manufacturer LIKE ?
                OR d.model LIKE ?
            )
            """]

        parameters: list[object] = [
            search_term,
            search_term,
            search_term,
            search_term,
            search_term,
            search_term,
        ]

        if selected_cost == "Missing part cost":
            conditions.append("p.part_cost_cents IS NULL")
        elif selected_cost == "Has part cost":
            conditions.append("p.part_cost_cents IS NOT NULL")

        if selected_status and selected_status != "All statuses":
            conditions.append("p.approval_status = ?")
            parameters.append(selected_status)

        eligibility_expression = """
            (
                p.part_cost_cents IS NOT NULL
                AND p.retail_price_cents IS NOT NULL
                AND p.retail_price_cents > 0
                AND LOWER(COALESCE(p.approval_status, '')) = 'approved'
            )
        """

        if selected_eligibility == "Publish eligible":
            conditions.append(eligibility_expression)
        elif selected_eligibility == "Not publish eligible":
            conditions.append(f"NOT {eligibility_expression}")

        where_clause = " AND ".join(conditions)

        rows = self.database.rows(
            f"""
            SELECT
                s.service_id,
                s.internal_name,
                s.service_type_name,
                p.device_id,
                d.manufacturer,
                d.model,
                p.part_cost_cents,
                p.retail_price_cents,
                p.approval_status
            FROM pricing_records AS p
            JOIN services AS s
              ON s.service_id = p.service_id
            LEFT JOIN devices AS d
              ON d.device_id = p.device_id
            WHERE {where_clause}
            ORDER BY
                CASE
                    WHEN p.part_cost_cents IS NULL THEN 0
                    ELSE 1
                END,
                d.manufacturer,
                d.model,
                s.internal_name
            """,
            tuple(parameters),
        )

        headers = [
            "Service ID",
            "Service",
            "Service Type",
            "Device ID",
            "Manufacturer",
            "Model",
            "Part Cost",
            "Retail",
            "Gross Profit",
            "Margin",
            "Status",
            "Publish Eligible",
        ]

        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))

        eligible_count = 0
        missing_cost_count = 0

        for row_index, row in enumerate(rows):
            part_cost = self.to_int(row[6])
            retail_price = self.to_int(row[7])
            approval_status = "" if row[8] is None else str(row[8])

            if part_cost is None:
                missing_cost_count += 1

            eligible = self.is_publish_eligible(
                part_cost,
                retail_price,
                approval_status,
            )

            if eligible:
                eligible_count += 1

            display_values = [
                self.display_value(row[0]),
                self.display_value(row[1]),
                self.display_value(row[2]),
                self.display_value(row[3]),
                self.display_value(row[4]),
                self.display_value(row[5]),
                self.format_currency(part_cost),
                self.format_currency(retail_price),
                self.format_gross_profit(part_cost, retail_price),
                self.format_margin(part_cost, retail_price),
                self.display_value(approval_status),
                "Yes" if eligible else "No",
            ]

            for column_index, display_value in enumerate(display_values):
                item = QTableWidgetItem(display_value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        header = self.table.horizontalHeader()

        for column in (0, 2, 3, 4, 6, 7, 8, 9, 10, 11):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.Stretch,
        )

        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)

        self.result_label.setText(f"{len(rows):,} pricing records")
        self.missing_cost_label.setText(f"Missing costs: {missing_cost_count:,}")
        self.eligible_label.setText(f"Publish eligible: {eligible_count:,}")

        self.clear_details()

    def load_selected_record(self) -> None:
        """Display details for the selected pricing record."""

        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            self.clear_details()
            return

        row_index = selected_rows[0].row()

        service_item = self.table.item(row_index, 0)
        device_item = self.table.item(row_index, 3)

        if service_item is None or device_item is None:
            self.clear_details()
            return

        service_id = service_item.text()
        device_id = device_item.text()

        rows = self.database.rows(
            """
            SELECT
                s.service_id,
                s.internal_name,
                s.service_type_name,
                p.device_id,
                d.manufacturer,
                d.model,
                p.part_cost_cents,
                p.retail_price_cents,
                p.approval_status
            FROM pricing_records AS p
            JOIN services AS s
              ON s.service_id = p.service_id
            LEFT JOIN devices AS d
              ON d.device_id = p.device_id
            WHERE p.service_id = ?
              AND p.device_id = ?
            LIMIT 1
            """,
            (service_id, device_id),
        )

        if not rows:
            self.clear_details()
            return

        record = rows[0]

        part_cost = self.to_int(record[6])
        retail_price = self.to_int(record[7])
        approval_status = "" if record[8] is None else str(record[8])

        manufacturer = self.display_value(record[4])
        model = self.display_value(record[5])

        if manufacturer == "—" and model == "—":
            device_name = "—"
        else:
            device_name = f"{manufacturer} {model}".strip()

        eligible = self.is_publish_eligible(
            part_cost,
            retail_price,
            approval_status,
        )

        self.detail_service_id.setText(self.display_value(record[0]))
        self.detail_service_name.setText(self.display_value(record[1]))
        self.detail_service_type.setText(self.display_value(record[2]))
        self.detail_device_id.setText(self.display_value(record[3]))
        self.detail_device.setText(device_name)
        self.detail_part_cost.setText(self.format_currency(part_cost))
        self.detail_retail_price.setText(self.format_currency(retail_price))
        self.detail_gross_profit.setText(
            self.format_gross_profit(part_cost, retail_price)
        )
        self.detail_margin.setText(self.format_margin(part_cost, retail_price))
        self.detail_status.setText(self.display_value(approval_status))
        self.detail_eligibility.setText("Eligible" if eligible else "Not eligible")

        self.approve_button.setEnabled(True)
        self.reject_button.setEnabled(True)

    def set_approval_status(self, approval_status: str) -> None:
        """Update the approval status of the selected pricing record."""

        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(
                self,
                "No pricing record selected",
                "Select a pricing record before changing its status.",
            )
            return

        row_index = selected_rows[0].row()

        service_item = self.table.item(row_index, 0)
        device_item = self.table.item(row_index, 3)

        if service_item is None or device_item is None:
            QMessageBox.warning(
                self,
                "Invalid selection",
                "The selected pricing record could not be identified.",
            )
            return

        service_id = service_item.text()
        device_id = device_item.text()

        try:
            affected_rows = self.database.execute(
                """
                UPDATE pricing_records
                SET approval_status = ?
                WHERE service_id = ?
                  AND device_id = ?
                """,
                (
                    approval_status,
                    service_id,
                    device_id,
                ),
            )
        except sqlite3.Error as exc:
            QMessageBox.critical(
                self,
                "Approval update failed",
                str(exc),
            )
            return

        if affected_rows == 0:
            QMessageBox.warning(
                self,
                "Pricing record not updated",
                "No matching pricing record was found.",
            )
            return

        self.refresh()

        QMessageBox.information(
            self,
            "Approval status updated",
            f"The pricing record was marked as {approval_status}.",
        )

    def clear_details(self) -> None:
        """Reset the pricing details panel."""

        self.detail_service_id.setText("Select a pricing record")
        self.detail_service_name.setText("—")
        self.detail_service_type.setText("—")
        self.detail_device_id.setText("—")
        self.detail_device.setText("—")
        self.detail_part_cost.setText("—")
        self.detail_retail_price.setText("—")
        self.detail_gross_profit.setText("—")
        self.detail_margin.setText("—")
        self.detail_status.setText("—")
        self.detail_eligibility.setText("—")

    @staticmethod
    def display_value(value: object) -> str:
        """Convert an optional database value into display text."""

        if value is None or str(value).strip() == "":
            return "—"

        return str(value)

    @staticmethod
    def to_int(value: object) -> int | None:
        """Safely convert a database value to an integer."""

        if value is None:
            return None

        if isinstance(value, bool):
            return int(value)

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return int(value)

        if isinstance(value, str):
            cleaned_value = value.strip()

            if not cleaned_value:
                return None

            try:
                return int(float(cleaned_value))
            except ValueError:
                return None

        return None

    @classmethod
    def format_currency(cls, value: object) -> str:
        """Format a cent-based value as US currency."""

        cents = cls.to_int(value)

        if cents is None:
            return "—"

        return f"${cents / 100:,.2f}"

    @classmethod
    def format_gross_profit(
        cls,
        part_cost_cents: object,
        retail_price_cents: object,
    ) -> str:
        """Calculate gross profit from cost and retail price."""

        cost = cls.to_int(part_cost_cents)
        retail = cls.to_int(retail_price_cents)

        if cost is None or retail is None:
            return "—"

        return cls.format_currency(retail - cost)

    @classmethod
    def format_margin(
        cls,
        part_cost_cents: object,
        retail_price_cents: object,
    ) -> str:
        """Calculate gross margin percentage."""

        cost = cls.to_int(part_cost_cents)
        retail = cls.to_int(retail_price_cents)

        if cost is None or retail is None or retail <= 0:
            return "—"

        margin_percentage = ((retail - cost) / retail) * 100

        return f"{margin_percentage:,.1f}%"

    @staticmethod
    def is_publish_eligible(
        part_cost_cents: int | None,
        retail_price_cents: int | None,
        approval_status: str,
    ) -> bool:
        """Determine whether a pricing record is publish-ready."""

        return (
            part_cost_cents is not None
            and retail_price_cents is not None
            and retail_price_cents > 0
            and approval_status.strip().lower() == "approved"
        )
