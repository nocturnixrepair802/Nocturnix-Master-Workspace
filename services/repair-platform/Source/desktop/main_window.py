from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from desktop.services.repair_service import RepairService
from desktop.views.checkin_view import CheckinView
from desktop.views.customers_view import CustomersView
from desktop.views.dashboard_view import DashboardView
from desktop.views.repair_queue_view import RepairQueueView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Nocturnix Repair Platform")
        self.resize(1280, 800)
        self.setMinimumSize(1000, 650)

        self.repair_service = RepairService()

        self._build_ui()
        self._show_dashboard()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        header = self._build_header()
        root_layout.addWidget(header)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.navigation = QListWidget()
        self.navigation.setFixedWidth(210)

        for label in (
            "Dashboard",
            "Customers",
            "Repair Queue",
            "Check-In",
        ):
            QListWidgetItem(label, self.navigation)

        self.navigation.currentRowChanged.connect(self._navigation_changed)

        body_layout.addWidget(self.navigation)

        self.stack = QStackedWidget()

        self.dashboard_view = DashboardView(service=self.repair_service)
        self.customers_view = CustomersView(service=self.repair_service)
        self.repair_queue_view = RepairQueueView(service=self.repair_service)
        self.checkin_view = CheckinView(service=self.repair_service)

        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.customers_view)
        self.stack.addWidget(self.repair_queue_view)
        self.stack.addWidget(self.checkin_view)

        body_layout.addWidget(self.stack, 1)

        root_layout.addWidget(body, 1)

        self.setCentralWidget(root)

        status = QStatusBar()
        status.showMessage(f"Offline database: {self.repair_service.database_path}")
        self.setStatusBar(status)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(70)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("Nocturnix Repair Platform")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")

        mode = QLabel("LOCAL / OFFLINE READY")
        mode.setAlignment(Qt.AlignmentFlag.AlignRight)
        mode.setStyleSheet("font-size: 12px; font-weight: 600;")

        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(mode)

        return header

    def _navigation_changed(self, index: int) -> None:
        if index < 0:
            return

        self.stack.setCurrentIndex(index)

        current = self.stack.currentWidget()

        refresh = getattr(current, "refresh", None)
        if callable(refresh):
            refresh()

    def _show_dashboard(self) -> None:
        self.navigation.setCurrentRow(0)
