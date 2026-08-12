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

from desktop.services.api_client import (
    ApiClient,
)
from desktop.services.read_service import ReadService
from desktop.services.repair_service import RepairService
from desktop.services.settings_service import (
    SettingsService,
)
from desktop.views.checkin_view import CheckinView
from desktop.views.customers_view import CustomersView
from desktop.views.dashboard_view import DashboardView
from desktop.views.devices_view import DevicesView
from desktop.views.repair_queue_view import RepairQueueView


class MainWindow(QMainWindow):
    ROUTES = {
        "dashboard": 0,
        "customers": 1,
        "devices": 2,
        "repair_queue": 3,
        "checkins": 4,
    }

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Nocturnix Repair Platform")

        self.resize(
            1380,
            860,
        )

        self.setMinimumSize(
            1100,
            700,
        )

        self.repair_service = RepairService()
        self.settings = SettingsService().load()

        self.api_client = ApiClient(
            self.settings
        )

        self.api_health = (
            self.api_client.health()
        )

        self.read_service = ReadService(
            local_service=self.repair_service,
            api_client=self.api_client,
            settings=self.settings,
            api_available=self.api_health.available,
        )

        self._build_ui()
        self._show_dashboard()

    def _build_ui(self) -> None:
        root = QWidget()

        root_layout = QVBoxLayout(root)

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root_layout.setSpacing(0)

        header = self._build_header()

        root_layout.addWidget(header)

        body = QWidget()

        body_layout = QHBoxLayout(body)

        body_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        body_layout.setSpacing(0)

        self.navigation = QListWidget()

        self.navigation.setObjectName("mainNavigation")

        self.navigation.setFixedWidth(220)

        for label in (
            "Dashboard",
            "Customers",
            "Devices",
            "Repair Queue",
            "Check-Ins",
        ):
            QListWidgetItem(
                label,
                self.navigation,
            )

        self.navigation.currentRowChanged.connect(self._navigation_changed)

        body_layout.addWidget(self.navigation)

        self.stack = QStackedWidget()

        self.dashboard_view = DashboardView(
            service=self.repair_service,
            read_service=self.read_service,
        )

        self.customers_view = CustomersView(service=self.repair_service)

        self.devices_view = DevicesView(service=self.repair_service)

        self.repair_queue_view = RepairQueueView(
            service=self.repair_service,
            read_service=self.read_service,
        )

        self.checkin_view = CheckinView(service=self.repair_service)

        self.dashboard_view.navigate_requested.connect(self._navigate_to)

        self.dashboard_view.repair_queue_requested.connect(
            self._open_filtered_repair_queue
        )

        self.stack.addWidget(self.dashboard_view)

        self.stack.addWidget(self.customers_view)

        self.stack.addWidget(self.devices_view)

        self.stack.addWidget(self.repair_queue_view)

        self.stack.addWidget(self.checkin_view)

        body_layout.addWidget(
            self.stack,
            1,
        )

        root_layout.addWidget(
            body,
            1,
        )

        self.setCentralWidget(root)

        self.status_bar = QStatusBar()

        self.status_bar.showMessage(
            self._connection_status_text()
        )

        self.setStatusBar(
            self.status_bar
        )

    def _build_header(
        self,
    ) -> QWidget:
        header = QWidget()

        header.setObjectName("appHeader")

        header.setFixedHeight(76)

        layout = QHBoxLayout(header)

        layout.setContentsMargins(
            22,
            0,
            22,
            0,
        )

        title = QLabel("NOCTURNIX MOBILE REPAIR")

        title.setObjectName("appTitle")

        subtitle = QLabel("Repair Platform")

        subtitle.setObjectName("appSubtitle")

        title_block = QWidget()

        title_layout = QVBoxLayout(title_block)

        title_layout.setContentsMargins(
            0,
            10,
            0,
            10,
        )

        title_layout.setSpacing(2)

        title_layout.addWidget(title)

        title_layout.addWidget(subtitle)

        self.mode_label = QLabel(
            self._connection_mode_text()
        )

        self.mode_label.setObjectName(
            "appSubtitle"
        )

        self.mode_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addWidget(title_block)

        layout.addStretch(1)

        layout.addWidget(self.mode_label)

        return header

    def _navigation_changed(
        self,
        index: int,
    ) -> None:
        if index < 0:
            return

        self.stack.setCurrentIndex(index)

        current = self.stack.currentWidget()

        refresh = getattr(
            current,
            "refresh",
            None,
        )

        if callable(refresh):
            refresh()

    def _navigate_to(
        self,
        route: str,
    ) -> None:
        index = self.ROUTES.get(route)

        if index is None:
            return

        self.navigation.setCurrentRow(index)

    def _open_filtered_repair_queue(
        self,
        mode: str,
        value: str,
    ) -> None:
        repair_index = self.ROUTES["repair_queue"]

        self.navigation.setCurrentRow(repair_index)

        if mode == "all":
            self.repair_queue_view.show_all_repairs()
            return

        if mode == "open":
            self.repair_queue_view.show_open_repairs()
            return

        if mode == "status":
            self.repair_queue_view.show_status(value)
            return

        if mode == "priority":
            self.repair_queue_view.show_priority(value)
            return

        if mode == "ticket":
            self.repair_queue_view.show_ticket(value)
            return

        self.repair_queue_view.show_all_repairs()

    def _show_dashboard(
        self,
    ) -> None:
        self.navigation.setCurrentRow(0)

    def _connection_mode_text(
        self,
    ) -> str:
        mode = self.settings.connection_mode

        if mode == "offline":
            return "LOCAL / OFFLINE READY"

        if self.api_health.available:
            if mode == "online":
                return "ONLINE READY"

            return "AUTO / ONLINE"

        if mode == "online":
            return "ONLINE UNAVAILABLE"

        return "AUTO / OFFLINE FALLBACK"

    def _connection_status_text(
        self,
    ) -> str:
        mode_text = self._connection_mode_text()

        if self.api_health.available:
            return f"{mode_text}" f"  |  " f"{self.settings.api_base_url}"

        return f"{mode_text}" f"  |  " f"{self.repair_service.database_path}"
