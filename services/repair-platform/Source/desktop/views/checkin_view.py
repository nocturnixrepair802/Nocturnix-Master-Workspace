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


class CheckinView(QWidget):
    def __init__(self, service: RepairService) -> None:
        super().__init__()

        self.service = service

        layout = QVBoxLayout(self)

        title = QLabel("Device Check-Ins")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        refresh_button = QPushButton("Refresh Check-Ins")
        refresh_button.clicked.connect(self.refresh)
        layout.addWidget(refresh_button)

        self.table = QTableWidget()
        self.table.setColumnCount(10)

        self.table.setHorizontalHeaderLabels(
            [
                "Check-In",
                "Repair",
                "Customer",
                "Manufacturer",
                "Model",
                "Serial",
                "Powers On",
                "Battery %",
                "Liquid Damage",
                "Passcode",
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table)

    def refresh(self) -> None:
        checkins = self.service.list_checkins()

        self.table.setRowCount(len(checkins))

        for row_index, checkin in enumerate(checkins):
            customer_name = " ".join(
                part
                for part in [
                    str(checkin.get("first_name", "") or "").strip(),
                    str(checkin.get("last_name", "") or "").strip(),
                ]
                if part
            )

            if not customer_name:
                customer_name = str(checkin.get("business_name", "") or "")

            values = [
                checkin.get("checkin_id", ""),
                checkin.get("repair_id", ""),
                customer_name,
                checkin.get("manufacturer", ""),
                checkin.get("device_model", ""),
                checkin.get("serial_number", ""),
                checkin.get("powers_on", ""),
                checkin.get("battery_percentage", ""),
                checkin.get("liquid_damage", ""),
                checkin.get("passcode_available", ""),
            ]

            for column_index, value in enumerate(values):
                self.table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(str(value or "")),
                )
