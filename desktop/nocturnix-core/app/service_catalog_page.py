from __future__ import annotations

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
)

from core.database import Database


class ServiceCatalogPage(QWidget):
    """Searchable service catalog with filters and service details."""

    def __init__(self, database: Database) -> None:
        super().__init__()

        self.database = database

        main_layout = QVBoxLayout(self)

        heading = QLabel("Service Catalog")
        heading.setObjectName("pageHeading")
        main_layout.addWidget(heading)

        description = QLabel(
            "Browse imported repair services, pricing records, and approval status."
        )
        description.setWordWrap(True)
        main_layout.addWidget(description)

        filter_layout = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Search by service ID, service name, service type, or device ID..."
        )
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)

        self.service_type_filter = QComboBox()
        self.service_type_filter.setMinimumWidth(190)
        self.service_type_filter.currentTextChanged.connect(self.refresh)

        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(160)
        self.status_filter.currentTextChanged.connect(self.refresh)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.reload)

        filter_layout.addWidget(self.search, 1)
        filter_layout.addWidget(self.service_type_filter)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(refresh_button)

        main_layout.addLayout(filter_layout)

        self.result_label = QLabel("0 pricing records")
        main_layout.addWidget(self.result_label)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self.load_selected_service)

        splitter.addWidget(self.table)

        details_group = QGroupBox("Service Details")
        details_layout = QFormLayout(details_group)

        self.detail_service_id = QLabel("Select a service")
        self.detail_name = QLabel("—")
        self.detail_type = QLabel("—")
        self.detail_device_id = QLabel("—")
        self.detail_part_cost = QLabel("—")
        self.detail_retail_price = QLabel("—")
        self.detail_margin = QLabel("—")
        self.detail_status = QLabel("—")

        details_layout.addRow("Service ID:", self.detail_service_id)
        details_layout.addRow("Service name:", self.detail_name)
        details_layout.addRow("Service type:", self.detail_type)
        details_layout.addRow("Device ID:", self.detail_device_id)
        details_layout.addRow("Part cost:", self.detail_part_cost)
        details_layout.addRow("Retail price:", self.detail_retail_price)
        details_layout.addRow("Gross margin:", self.detail_margin)
        details_layout.addRow("Approval status:", self.detail_status)

        splitter.addWidget(details_group)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([500, 220])

        main_layout.addWidget(splitter, 1)

        self.load_filters()
        self.refresh()

    def load_filters(self) -> None:
        """Load available service types and approval statuses."""

        current_type = self.service_type_filter.currentText()
        current_status = self.status_filter.currentText()

        service_type_rows = self.database.rows("""
            SELECT DISTINCT service_type_name
            FROM services
            WHERE service_type_name IS NOT NULL
              AND TRIM(service_type_name) <> ''
            ORDER BY service_type_name
            """)

        status_rows = self.database.rows("""
            SELECT DISTINCT approval_status
            FROM pricing_records
            WHERE approval_status IS NOT NULL
              AND TRIM(approval_status) <> ''
            ORDER BY approval_status
            """)

        self.service_type_filter.blockSignals(True)
        self.service_type_filter.clear()
        self.service_type_filter.addItem("All service types")

        for row in service_type_rows:
            value = str(row[0]).strip()

            if value:
                self.service_type_filter.addItem(value)

        type_index = self.service_type_filter.findText(current_type)

        if type_index >= 0:
            self.service_type_filter.setCurrentIndex(type_index)

        self.service_type_filter.blockSignals(False)

        self.status_filter.blockSignals(True)
        self.status_filter.clear()
        self.status_filter.addItem("All statuses")

        for row in status_rows:
            value = str(row[0]).strip()

            if value:
                self.status_filter.addItem(value)

        status_index = self.status_filter.findText(current_status)

        if status_index >= 0:
            self.status_filter.setCurrentIndex(status_index)

        self.status_filter.blockSignals(False)

    def reload(self) -> None:
        """Reload filters and table data from the database."""

        current_type = self.service_type_filter.currentText()
        current_status = self.status_filter.currentText()
        current_search = self.search.text()

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        try:
            self.load_filters()

            type_index = self.service_type_filter.findText(current_type)

            if type_index >= 0:
                self.service_type_filter.setCurrentIndex(type_index)

            status_index = self.status_filter.findText(current_status)

            if status_index >= 0:
                self.status_filter.setCurrentIndex(status_index)

            self.search.setText(current_search)
            self.refresh()

            self.result_label.setText(
                f"{self.table.rowCount():,} pricing records — refreshed"
            )
        finally:
            QApplication.restoreOverrideCursor()

    def refresh(self) -> None:
        """Apply filters and reload the service table."""

        search_term = f"%{self.search.text().strip()}%"
        selected_type = self.service_type_filter.currentText()
        selected_status = self.status_filter.currentText()

        conditions = ["""
            (
                s.service_id LIKE ?
                OR s.internal_name LIKE ?
                OR s.service_type_name LIKE ?
                OR p.device_id LIKE ?
            )
            """]

        parameters: list[object] = [
            search_term,
            search_term,
            search_term,
            search_term,
        ]

        if selected_type and selected_type != "All service types":
            conditions.append("s.service_type_name = ?")
            parameters.append(selected_type)

        if selected_status and selected_status != "All statuses":
            conditions.append("p.approval_status = ?")
            parameters.append(selected_status)

        where_clause = " AND ".join(conditions)

        rows = self.database.rows(
            f"""
            SELECT
                s.service_id,
                s.internal_name,
                s.service_type_name,
                p.device_id,
                p.part_cost_cents,
                p.retail_price_cents,
                p.approval_status
            FROM services AS s
            JOIN pricing_records AS p
              ON p.service_id = s.service_id
            WHERE {where_clause}
            ORDER BY s.internal_name, p.device_id
            """,
            tuple(parameters),
        )

        headers = [
            "Service ID",
            "Service Name",
            "Service Type",
            "Device ID",
            "Part Cost",
            "Retail",
            "Status",
        ]

        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                if column_index in (4, 5):
                    display_value = self.format_currency(value)
                else:
                    display_value = "" if value is None else str(value)

                item = QTableWidgetItem(display_value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)

        self.result_label.setText(f"{len(rows):,} pricing records")
        self.clear_details()

    def load_selected_service(self) -> None:
        """Load details from the selected service-pricing row."""

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
                p.part_cost_cents,
                p.retail_price_cents,
                p.approval_status
            FROM services AS s
            JOIN pricing_records AS p
              ON p.service_id = s.service_id
            WHERE s.service_id = ?
              AND p.device_id = ?
            LIMIT 1
            """,
            (service_id, device_id),
        )

        if not rows:
            self.clear_details()
            return

        service = rows[0]
        part_cost = service[4]
        retail_price = service[5]

        self.detail_service_id.setText(self.display_value(service[0]))
        self.detail_name.setText(self.display_value(service[1]))
        self.detail_type.setText(self.display_value(service[2]))
        self.detail_device_id.setText(self.display_value(service[3]))
        self.detail_part_cost.setText(self.format_currency(part_cost))
        self.detail_retail_price.setText(self.format_currency(retail_price))
        self.detail_margin.setText(self.format_margin(part_cost, retail_price))
        self.detail_status.setText(self.display_value(service[6]))

    def clear_details(self) -> None:
        """Reset the details panel."""

        self.detail_service_id.setText("Select a service")
        self.detail_name.setText("—")
        self.detail_type.setText("—")
        self.detail_device_id.setText("—")
        self.detail_part_cost.setText("—")
        self.detail_retail_price.setText("—")
        self.detail_margin.setText("—")
        self.detail_status.setText("—")

    @staticmethod
    def display_value(value: object) -> str:
        if value is None or str(value).strip() == "":
            return "—"

        return str(value)


    @staticmethod
    def to_int(value: object) -> int | None:
        """Safely convert a database value into an integer."""

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
        cents = cls.to_int(value)

        if cents is None:
            return "—"

        return f"${cents / 100:,.2f}"


    @classmethod
    def format_margin(
        cls,
        part_cost_cents: object,
        retail_price_cents: object,
    ) -> str:
        cost = cls.to_int(part_cost_cents)
        retail = cls.to_int(retail_price_cents)

        if cost is None or retail is None or retail <= 0:
            return "—"

        margin_percentage = ((retail - cost) / retail) * 100

        return f"{margin_percentage:,.1f}%"
