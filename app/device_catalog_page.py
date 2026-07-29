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


class DeviceCatalogPage(QWidget):
    """Searchable device catalog with a selected-device details panel."""

    def __init__(self, database: Database) -> None:
        super().__init__()

        self.database = database

        main_layout = QVBoxLayout(self)

        heading = QLabel("Device Catalog")
        heading.setObjectName("pageHeading")
        main_layout.addWidget(heading)

        description = QLabel(
            "Browse imported devices and select a row to view additional details."
        )
        description.setWordWrap(True)
        main_layout.addWidget(description)

        filter_layout = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by device ID, manufacturer, or model...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)

        self.manufacturer_filter = QComboBox()
        self.manufacturer_filter.setMinimumWidth(180)
        self.manufacturer_filter.currentTextChanged.connect(self.refresh)

        self.status_filter = QComboBox()
        self.status_filter.addItems(
            [
                "All statuses",
                "Active",
                "Inactive",
            ]
        )
        self.status_filter.currentTextChanged.connect(self.refresh)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.reload)

        filter_layout.addWidget(self.search, 1)
        filter_layout.addWidget(self.manufacturer_filter)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(refresh_button)

        main_layout.addLayout(filter_layout)

        self.result_label = QLabel("0 devices")
        main_layout.addWidget(self.result_label)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self.load_selected_device)

        splitter.addWidget(self.table)

        details_group = QGroupBox("Device Details")
        details_layout = QFormLayout(details_group)

        self.detail_device_id = QLabel("Select a device")
        self.detail_manufacturer = QLabel("—")
        self.detail_model = QLabel("—")
        self.detail_family_id = QLabel("—")
        self.detail_type_id = QLabel("—")
        self.detail_active = QLabel("—")
        self.detail_service_count = QLabel("—")
        self.detail_pricing_count = QLabel("—")

        details_layout.addRow("Device ID:", self.detail_device_id)
        details_layout.addRow("Manufacturer:", self.detail_manufacturer)
        details_layout.addRow("Model:", self.detail_model)
        details_layout.addRow("Device Family ID:", self.detail_family_id)
        details_layout.addRow("Device Type ID:", self.detail_type_id)
        details_layout.addRow("Active:", self.detail_active)
        details_layout.addRow(
            "Associated services:",
            self.detail_service_count,
        )
        details_layout.addRow(
            "Pricing records:",
            self.detail_pricing_count,
        )

        splitter.addWidget(details_group)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([500, 220])

        main_layout.addWidget(splitter, 1)

        self.load_manufacturers()
        self.refresh()

    def load_manufacturers(self) -> None:
        """Load distinct manufacturers into the filter."""

        current_value = self.manufacturer_filter.currentText()

        rows = self.database.rows("""
            SELECT DISTINCT manufacturer
            FROM devices
            WHERE manufacturer IS NOT NULL
              AND TRIM(manufacturer) <> ''
            ORDER BY manufacturer
            """)

        self.manufacturer_filter.blockSignals(True)
        self.manufacturer_filter.clear()
        self.manufacturer_filter.addItem("All manufacturers")

        for row in rows:
            manufacturer = str(row[0]).strip()

            if manufacturer:
                self.manufacturer_filter.addItem(manufacturer)

        index = self.manufacturer_filter.findText(current_value)

        if index >= 0:
            self.manufacturer_filter.setCurrentIndex(index)

        self.manufacturer_filter.blockSignals(False)

    def reload(self) -> None:
        """Reload filters and table data from the database."""

        current_manufacturer = self.manufacturer_filter.currentText()
        current_status = self.status_filter.currentText()
        current_search = self.search.text()

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        try:
            self.load_manufacturers()

            manufacturer_index = self.manufacturer_filter.findText(current_manufacturer)

            if manufacturer_index >= 0:
                self.manufacturer_filter.setCurrentIndex(manufacturer_index)

            self.status_filter.setCurrentText(current_status)
            self.search.setText(current_search)

            self.refresh()
            self.result_label.setText(f"{self.table.rowCount():,} devices — refreshed")
        finally:
            QApplication.restoreOverrideCursor()
    def refresh(self) -> None:
        """Apply filters and reload the device table."""

        search_text = self.search.text().strip()
        search_term = f"%{search_text}%"

        manufacturer = self.manufacturer_filter.currentText()
        status = self.status_filter.currentText()

        conditions = ["""
            (
                device_id LIKE ?
                OR manufacturer LIKE ?
                OR model LIKE ?
            )
            """]

        parameters: list[object] = [
            search_term,
            search_term,
            search_term,
        ]

        if manufacturer and manufacturer != "All manufacturers":
            conditions.append("manufacturer = ?")
            parameters.append(manufacturer)

        if status == "Active":
            conditions.append("active = 1")
        elif status == "Inactive":
            conditions.append("active = 0")

        where_clause = " AND ".join(conditions)

        rows = self.database.rows(
            f"""
            SELECT
                device_id,
                manufacturer,
                model,
                device_family_id,
                device_type_id,
                active
            FROM devices
            WHERE {where_clause}
            ORDER BY manufacturer, model
            """,
            tuple(parameters),
        )

        headers = [
            "Device ID",
            "Manufacturer",
            "Model",
            "Family ID",
            "Type ID",
            "Active",
        ]

        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                if column_index == 5:
                    display_value = "Yes" if value else "No"
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
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
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

        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)

        self.result_label.setText(f"{len(rows):,} devices")
        self.clear_details()

    def load_selected_device(self) -> None:
        """Load details for the selected table row."""

        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            self.clear_details()
            return

        row_index = selected_rows[0].row()
        device_item = self.table.item(row_index, 0)

        if device_item is None:
            self.clear_details()
            return

        device_id = device_item.text()

        rows = self.database.rows(
            """
            SELECT
                device_id,
                manufacturer,
                model,
                device_family_id,
                device_type_id,
                active
            FROM devices
            WHERE device_id = ?
            LIMIT 1
            """,
            (device_id,),
        )

        if not rows:
            self.clear_details()
            return

        device = rows[0]

        pricing_count = (
            self.database.scalar(
                """
            SELECT COUNT(*)
            FROM pricing_records
            WHERE device_id = ?
            """,
                (device_id,),
            )
            or 0
        )

        service_count = (
            self.database.scalar(
                """
            SELECT COUNT(DISTINCT service_id)
            FROM pricing_records
            WHERE device_id = ?
            """,
                (device_id,),
            )
            or 0
        )

        self.detail_device_id.setText(self.display_value(device[0]))
        self.detail_manufacturer.setText(self.display_value(device[1]))
        self.detail_model.setText(self.display_value(device[2]))
        self.detail_family_id.setText(self.display_value(device[3]))
        self.detail_type_id.setText(self.display_value(device[4]))
        self.detail_active.setText("Yes" if device[5] else "No")
        self.detail_service_count.setText(f"{int(service_count):,}")
        self.detail_pricing_count.setText(f"{int(pricing_count):,}")

    def clear_details(self) -> None:
        """Reset the details panel when nothing is selected."""

        self.detail_device_id.setText("Select a device")
        self.detail_manufacturer.setText("—")
        self.detail_model.setText("—")
        self.detail_family_id.setText("—")
        self.detail_type_id.setText("—")
        self.detail_active.setText("—")
        self.detail_service_count.setText("—")
        self.detail_pricing_count.setText("—")

    @staticmethod
    def display_value(value: object) -> str:
        """Convert nullable database values into display text."""

        if value is None or str(value).strip() == "":
            return "—"

        return str(value)
