from __future__ import annotations

from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from desktop.services.repair_service import RepairService


class DashboardView(QWidget):
    def __init__(self, service: RepairService) -> None:
        super().__init__()
        self.service = service

        layout = QVBoxLayout(self)

        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        grid = QGridLayout()

        self.customers_box = self._make_card("Customers")
        self.devices_box = self._make_card("Devices")
        self.repairs_box = self._make_card("Total Repairs")
        self.open_repairs_box = self._make_card("Open Repairs")

        grid.addWidget(self.customers_box[0], 0, 0)
        grid.addWidget(self.devices_box[0], 0, 1)
        grid.addWidget(self.repairs_box[0], 1, 0)
        grid.addWidget(self.open_repairs_box[0], 1, 1)

        layout.addLayout(grid)

        refresh_button = QPushButton("Refresh Dashboard")
        refresh_button.clicked.connect(self.refresh)
        layout.addWidget(refresh_button)

        layout.addStretch(1)

    def _make_card(self, label: str) -> tuple[QGroupBox, QLabel]:
        box = QGroupBox(label)
        box_layout = QVBoxLayout(box)

        value = QLabel("0")
        value.setStyleSheet("font-size: 32px; font-weight: 700;")

        box_layout.addWidget(value)
        return box, value

    def refresh(self) -> None:
        counts = self.service.dashboard_counts()

        self.customers_box[1].setText(str(counts["customers"]))
        self.devices_box[1].setText(str(counts["devices"]))
        self.repairs_box[1].setText(str(counts["repairs"]))
        self.open_repairs_box[1].setText(str(counts["open_repairs"]))
