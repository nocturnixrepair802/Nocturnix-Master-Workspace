from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.database import Database


class DeviceCatalogPage(QWidget):
    """Searchable and filterable view of the imported device catalog."""

    def __init__(self, database: Database) -> None:
        super().__init__()

        self.database = database

        main_layout = QVBoxLayout(self)

        heading = QLabel("Device Catalog")
        heading.setObjectName("pageHeading")
        main_layout.addWidget(heading)

        description = QLabel(
            "Browse imported devices by manufacturer, model, family, and status."
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

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        main_layout.addWidget(self.table, 1)

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

        self.load_manufacturers()
        self.refresh()

    def refresh(self) -> None:
        """Apply the selected filters and reload the device table."""

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
        self.result_label.setText(f"{len(rows):,} devices")
