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


class RepairQueueView(QWidget):
    def __init__(self, service: RepairService) -> None:
        super().__init__()
        self.service = service

        layout = QVBoxLayout(self)

        title = QLabel("Repair Queue")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        refresh_button = QPushButton("Refresh Repair Queue")
        refresh_button.clicked.connect(self.refresh)
        layout.addWidget(refresh_button)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "Ticket",
                "Status",
                "Customer",
                "Manufacturer",
                "Model",
                "Serial",
                "Priority",
                "Technician",
                "Problem",
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table)

    def refresh(self) -> None:
        repairs = self.service.list_repairs()
        self.table.setRowCount(len(repairs))

        for row_index, repair in enumerate(repairs):
            customer_name = " ".join(
                part
                for part in (
                    str(repair.get("first_name", "") or "").strip(),
                    str(repair.get("last_name", "") or "").strip(),
                )
                if part
            )

            if not customer_name:
                customer_name = str(repair.get("business_name", "") or "")

            model = repair.get("device_model") or repair.get("device_family") or ""

            values = [
                repair.get("ticket_id", ""),
                repair.get("repair_status", ""),
                customer_name,
                repair.get("manufacturer", ""),
                model,
                repair.get("serial_number", ""),
                repair.get("priority", ""),
                repair.get("technician", ""),
                repair.get("problem_description", ""),
            ]

            for column_index, value in enumerate(values):
                self.table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(str(value or "")),
                )

