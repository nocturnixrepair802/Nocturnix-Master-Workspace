from __future__ import annotations

from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.services.repair_service import RepairService


class CustomersView(QWidget):
    def __init__(self, service: RepairService) -> None:
        super().__init__()
        self.service = service

        layout = QVBoxLayout(self)

        title = QLabel("Customers")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        refresh_button = QPushButton("Refresh Customers")
        refresh_button.clicked.connect(self.refresh)
        layout.addWidget(refresh_button)

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

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table)

    def refresh(self) -> None:
        customers = self.service.list_customers()
        self.table.setRowCount(len(customers))

        for row_index, customer in enumerate(customers):
            values = [
                customer.get("customer_id", ""),
                customer.get("first_name", ""),
                customer.get("last_name", ""),
                customer.get("business_name", ""),
                customer.get("email", ""),
                customer.get("mobile_phone", ""),
                customer.get("customer_type", ""),
            ]

            for column_index, value in enumerate(values):
                self.table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(str(value or "")),
                )
