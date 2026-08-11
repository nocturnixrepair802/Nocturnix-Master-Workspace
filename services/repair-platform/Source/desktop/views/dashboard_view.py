from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QMouseEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.services.repair_service import RepairService
from desktop.views.checkin_dialog import NewCheckinDialog
from desktop.views.customer_devices_dialog import DeviceDialog
from desktop.views.customers_view import CustomerDialog
from desktop.views.repair_dialog import NewRepairDialog


class ClickableStatCard(QFrame):
    def __init__(
        self,
        label: str,
        callback: Callable[[], None],
    ) -> None:
        super().__init__()

        self.callback = callback

        self.setObjectName("statCard")

        self.setMinimumHeight(86)

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.setStyleSheet("""
            QFrame#statCard {
                background-color: white;
                border: 1px solid #D7DEE8;
                border-radius: 10px;
            }

            QFrame#statCard:hover {
                border: 2px solid #00B4E7;
                background-color: #F8FBFD;
            }
            """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        self.value = QLabel("0")

        self.value.setObjectName("statValue")

        self.name = QLabel(label)

        self.name.setObjectName("statLabel")

        self.name.setWordWrap(True)

        layout.addWidget(self.value)

        layout.addWidget(self.name)

    def mousePressEvent(
        self,
        event: QMouseEvent,
    ) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback()

        super().mousePressEvent(event)


class DashboardView(QWidget):
    navigate_requested: ClassVar[Any] = Signal(str)

    repair_queue_requested: ClassVar[Any] = Signal(
        str,
        str,
    )

    def __init__(
        self,
        service: RepairService,
    ) -> None:
        super().__init__()

        self.service: RepairService = service

        self.activity_repairs: list[str] = []

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(True)

        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()

        root = QVBoxLayout(content)

        root.setContentsMargins(
            28,
            24,
            28,
            28,
        )

        root.setSpacing(20)

        title = QLabel("Dashboard")

        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Local repair operations, workflow status, " "and recent activity."
        )

        subtitle.setObjectName("mutedText")

        root.addWidget(title)

        root.addWidget(subtitle)

        # -----------------------------------------------------
        # OVERVIEW
        # -----------------------------------------------------

        overview_title = QLabel("Overview")

        overview_title.setObjectName("sectionTitle")

        root.addWidget(overview_title)

        overview_grid = QGridLayout()

        overview_grid.setSpacing(14)

        self.customers_card = ClickableStatCard(
            "Customers",
            self._open_customers,
        )

        self.devices_card = ClickableStatCard(
            "Devices",
            self._open_devices,
        )

        self.repairs_card = ClickableStatCard(
            "Total Repairs",
            self._show_all_repairs,
        )

        self.open_repairs_card = ClickableStatCard(
            "Open Repairs",
            self._show_open_repairs,
        )

        overview_grid.addWidget(
            self.customers_card,
            0,
            0,
        )

        overview_grid.addWidget(
            self.devices_card,
            0,
            1,
        )

        overview_grid.addWidget(
            self.repairs_card,
            0,
            2,
        )

        overview_grid.addWidget(
            self.open_repairs_card,
            0,
            3,
        )

        root.addLayout(overview_grid)

        # -----------------------------------------------------
        # WORKFLOW
        # -----------------------------------------------------

        workflow_title = QLabel("Repair Workflow")

        workflow_title.setObjectName("sectionTitle")

        root.addWidget(workflow_title)

        workflow_grid = QGridLayout()

        workflow_grid.setSpacing(14)

        self.awaiting_diagnosis_card = ClickableStatCard(
            "Awaiting Diagnosis",
            lambda: self._show_status("Awaiting Diagnosis"),
        )

        self.awaiting_approval_card = ClickableStatCard(
            "Awaiting Approval",
            lambda: self._show_status("Awaiting Approval"),
        )

        self.in_repair_card = ClickableStatCard(
            "In Repair",
            lambda: self._show_status("In Repair"),
        )

        self.awaiting_parts_card = ClickableStatCard(
            "Awaiting Parts",
            lambda: self._show_status("Awaiting Parts"),
        )

        self.ready_pickup_card = ClickableStatCard(
            "Ready for Pickup",
            lambda: self._show_status("Ready for Pickup"),
        )

        self.urgent_card = ClickableStatCard(
            "Urgent Repairs",
            self._show_urgent_repairs,
        )

        workflow_grid.addWidget(
            self.awaiting_diagnosis_card,
            0,
            0,
        )

        workflow_grid.addWidget(
            self.awaiting_approval_card,
            0,
            1,
        )

        workflow_grid.addWidget(
            self.in_repair_card,
            0,
            2,
        )

        workflow_grid.addWidget(
            self.awaiting_parts_card,
            1,
            0,
        )

        workflow_grid.addWidget(
            self.ready_pickup_card,
            1,
            1,
        )

        workflow_grid.addWidget(
            self.urgent_card,
            1,
            2,
        )

        root.addLayout(workflow_grid)

        # -----------------------------------------------------
        # QUICK ACTIONS
        # -----------------------------------------------------

        quick_title = QLabel("Quick Actions")

        quick_title.setObjectName("sectionTitle")

        root.addWidget(quick_title)

        quick_grid = QGridLayout()

        quick_grid.setSpacing(12)

        new_customer_button = self._button(
            "＋ New Customer",
            self._new_customer,
            primary=True,
        )

        new_device_button = self._button(
            "＋ New Device",
            self._new_device,
            primary=True,
        )

        new_repair_button = self._button(
            "＋ New Repair",
            self._new_repair,
            primary=True,
        )

        new_checkin_button = self._button(
            "＋ New Check-In",
            self._new_checkin,
            primary=True,
        )

        customers_button = self._button(
            "Customers",
            self._open_customers,
        )

        devices_button = self._button(
            "Devices",
            self._open_devices,
        )

        repair_queue_button = self._button(
            "Repair Queue",
            self._open_repair_queue,
        )

        checkins_button = self._button(
            "Check-Ins",
            self._open_checkins,
        )

        refresh_button = self._button(
            "Refresh Dashboard",
            self.refresh,
            secondary=True,
        )

        quick_grid.addWidget(
            new_customer_button,
            0,
            0,
        )

        quick_grid.addWidget(
            new_device_button,
            0,
            1,
        )

        quick_grid.addWidget(
            new_repair_button,
            0,
            2,
        )

        quick_grid.addWidget(
            new_checkin_button,
            0,
            3,
        )

        quick_grid.addWidget(
            customers_button,
            1,
            0,
        )

        quick_grid.addWidget(
            devices_button,
            1,
            1,
        )

        quick_grid.addWidget(
            repair_queue_button,
            1,
            2,
        )

        quick_grid.addWidget(
            checkins_button,
            1,
            3,
        )

        quick_grid.addWidget(
            refresh_button,
            2,
            0,
        )

        root.addLayout(quick_grid)

        # -----------------------------------------------------
        # RECENT ACTIVITY
        # -----------------------------------------------------

        activity_title = QLabel("Recent Repair Activity")

        activity_title.setObjectName("sectionTitle")

        root.addWidget(activity_title)

        activity_note = QLabel("Double-click an activity to open " "that exact repair.")

        activity_note.setObjectName("mutedText")

        root.addWidget(activity_note)

        self.activity_table = QTableWidget()

        self.activity_table.setColumnCount(6)

        self.activity_table.setHorizontalHeaderLabels(
            [
                "Date",
                "Repair",
                "Activity",
                "Change",
                "Customer",
                "Device",
            ]
        )

        self.activity_table.setStyleSheet("""
            QTableWidget {
                font-size: 8pt;
            }

            QTableWidget::item {
                padding: 2px 4px;
            }

            QHeaderView::section {
                font-size: 8pt;
                padding: 4px 5px;
            }
            """)

        self.activity_table.setWordWrap(False)

        self.activity_table.setTextElideMode(Qt.TextElideMode.ElideRight)

        self.activity_table.verticalHeader().setDefaultSectionSize(24)

        self.activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.activity_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.activity_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.activity_table.setAlternatingRowColors(True)

        self.activity_table.setMinimumHeight(260)

        header = self.activity_table.horizontalHeader()

        for column in range(self.activity_table.columnCount()):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.Stretch,
        )

        self.activity_table.doubleClicked.connect(self._open_activity_repair)

        root.addWidget(self.activity_table)

        root.addStretch(1)

        self.scroll_area.setWidget(content)

        outer_layout.addWidget(self.scroll_area)

    @staticmethod
    def _button(
        text: str,
        callback: Callable[[], None],
        *,
        primary: bool = False,
        secondary: bool = False,
    ) -> QPushButton:
        button = QPushButton(text)

        button.setMinimumHeight(48)

        if primary:
            button.setObjectName("primaryButton")

        elif secondary:
            button.setObjectName("secondaryButton")

        button.clicked.connect(callback)

        return button

    # ---------------------------------------------------------
    # REFRESH
    # ---------------------------------------------------------

    def refresh(self) -> None:
        counts = self.service.dashboard_counts()

        operational = self.service.dashboard_operational_counts()

        self.customers_card.value.setText(str(counts["customers"]))

        self.devices_card.value.setText(str(counts["devices"]))

        self.repairs_card.value.setText(str(counts["repairs"]))

        self.open_repairs_card.value.setText(str(counts["open_repairs"]))

        self.awaiting_diagnosis_card.value.setText(
            str(operational["awaiting_diagnosis"])
        )

        self.awaiting_approval_card.value.setText(str(operational["awaiting_approval"]))

        self.in_repair_card.value.setText(str(operational["in_repair"]))

        self.awaiting_parts_card.value.setText(str(operational["awaiting_parts"]))

        self.ready_pickup_card.value.setText(str(operational["ready_for_pickup"]))

        self.urgent_card.value.setText(str(operational["urgent_repairs"]))

        self._refresh_activity()

    def _refresh_activity(
        self,
    ) -> None:
        activity = self.service.recent_repair_activity(limit=12)

        self.activity_repairs = []

        self.activity_table.setRowCount(len(activity))

        for row_index, event in enumerate(activity):
            repair_id = str(
                event.get(
                    "repair_id",
                    "",
                )
                or ""
            )

            self.activity_repairs.append(repair_id)

            customer_name = self._activity_customer_name(event)

            device_name = self._activity_device_name(event)

            change = self._activity_change(event)

            activity_name = self._activity_name(
                str(
                    event.get(
                        "event_type",
                        "",
                    )
                    or ""
                )
            )

            values = [
                event.get(
                    "created_at",
                    "",
                ),
                repair_id,
                activity_name,
                change,
                customer_name,
                device_name,
            ]

            for column_index, value in enumerate(values):
                text = str(value or "")

                item = QTableWidgetItem(text)

                if text:
                    item.setToolTip(text)

                self.activity_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    @staticmethod
    def _activity_name(
        event_type: str,
    ) -> str:
        names = {
            "repair_created": "Repair Created",
            "repair_status_changed": "Status Changed",
            "checkin_created": "Check-In Created",
        }

        if event_type in names:
            return names[event_type]

        return (
            event_type.replace(
                "_",
                " ",
            )
            .strip()
            .title()
        )

    @staticmethod
    def _activity_change(
        event: dict[str, Any],
    ) -> str:
        old_value = str(
            event.get(
                "old_value",
                "",
            )
            or ""
        ).strip()

        new_value = str(
            event.get(
                "new_value",
                "",
            )
            or ""
        ).strip()

        if old_value and new_value:
            return f"{old_value} → " f"{new_value}"

        if new_value:
            return new_value

        return old_value

    @staticmethod
    def _activity_customer_name(
        event: dict[str, Any],
    ) -> str:
        first_name = str(
            event.get(
                "first_name",
                "",
            )
            or ""
        ).strip()

        last_name = str(
            event.get(
                "last_name",
                "",
            )
            or ""
        ).strip()

        business_name = str(
            event.get(
                "business_name",
                "",
            )
            or ""
        ).strip()

        name = " ".join(
            part
            for part in (
                first_name,
                last_name,
            )
            if part
        )

        if name:
            return name

        if business_name:
            return business_name

        return str(
            event.get(
                "customer_id",
                "",
            )
            or ""
        )

    @staticmethod
    def _activity_device_name(
        event: dict[str, Any],
    ) -> str:
        manufacturer = str(
            event.get(
                "manufacturer",
                "",
            )
            or ""
        ).strip()

        model = str(
            event.get(
                "device_model",
                "",
            )
            or event.get(
                "device_family",
                "",
            )
            or ""
        ).strip()

        name = " ".join(
            part
            for part in (
                manufacturer,
                model,
            )
            if part
        )

        if name:
            return name

        return str(
            event.get(
                "device_id",
                "",
            )
            or ""
        )

    # ---------------------------------------------------------
    # CLICKABLE DASHBOARD ROUTING
    # ---------------------------------------------------------

    def _show_all_repairs(
        self,
    ) -> None:
        self.repair_queue_requested.emit(
            "all",
            "",
        )

    def _show_open_repairs(
        self,
    ) -> None:
        self.repair_queue_requested.emit(
            "open",
            "",
        )

    def _show_status(
        self,
        status: str,
    ) -> None:
        self.repair_queue_requested.emit(
            "status",
            status,
        )

    def _show_urgent_repairs(
        self,
    ) -> None:
        self.repair_queue_requested.emit(
            "priority",
            "Urgent",
        )

    def _open_activity_repair(
        self,
        *_args: object,
    ) -> None:
        row = self.activity_table.currentRow()

        if row < 0:
            return

        item = self.activity_table.item(
            row,
            1,
        )

        if item is None:
            return

        repair_id = item.text().strip()

        if not repair_id:
            return

        self.repair_queue_requested.emit(
            "ticket",
            repair_id,
        )

    # ---------------------------------------------------------
    # NORMAL NAVIGATION
    # ---------------------------------------------------------

    def _open_customers(
        self,
    ) -> None:
        self.navigate_requested.emit("customers")

    def _open_devices(
        self,
    ) -> None:
        self.navigate_requested.emit("devices")

    def _open_repair_queue(
        self,
    ) -> None:
        self.navigate_requested.emit("repair_queue")

    def _open_checkins(
        self,
    ) -> None:
        self.navigate_requested.emit("checkins")

    # ---------------------------------------------------------
    # CUSTOMER / DEVICE HELPERS
    # ---------------------------------------------------------

    @staticmethod
    def _customer_display(
        customer: dict[str, object],
    ) -> str:
        customer_id = str(
            customer.get(
                "customer_id",
                "",
            )
        )

        first_name = str(
            customer.get(
                "first_name",
                "",
            )
            or ""
        ).strip()

        last_name = str(
            customer.get(
                "last_name",
                "",
            )
            or ""
        ).strip()

        business_name = str(
            customer.get(
                "business_name",
                "",
            )
            or ""
        ).strip()

        name = " ".join(
            part
            for part in (
                first_name,
                last_name,
            )
            if part
        )

        if not name:
            name = business_name

        if not name:
            name = "Unnamed Customer"

        return f"{customer_id} — " f"{name}"

    def _choose_customer(
        self,
    ) -> str | None:
        customers = self.service.list_customers()

        if not customers:
            QMessageBox.information(
                self,
                "No Customers",
                "Create a customer first.",
            )

            return None

        displays = [self._customer_display(customer) for customer in customers]

        selected, accepted = QInputDialog.getItem(
            self,
            "Select Customer",
            "Customer",
            displays,
            0,
            False,
        )

        if not accepted:
            return None

        index = displays.index(selected)

        return str(customers[index]["customer_id"])

    def _choose_device(
        self,
        customer_id: str,
    ) -> str | None:
        devices = self.service.list_customer_devices(customer_id)

        if not devices:
            QMessageBox.information(
                self,
                "No Devices",
                "This customer has no devices yet.",
            )

            return None

        displays: list[str] = []

        for device in devices:
            device_id = str(
                device.get(
                    "device_id",
                    "",
                )
            )

            manufacturer = str(
                device.get(
                    "manufacturer",
                    "",
                )
                or ""
            ).strip()

            model = str(
                device.get(
                    "device_model",
                    "",
                )
                or device.get(
                    "device_family",
                    "",
                )
                or ""
            ).strip()

            serial_number = str(
                device.get(
                    "serial_number",
                    "",
                )
                or ""
            ).strip()

            display = (f"{device_id} — " f"{manufacturer} {model}").strip()

            if serial_number:
                display += f" — {serial_number}"

            displays.append(display)

        selected, accepted = QInputDialog.getItem(
            self,
            "Select Device",
            "Device",
            displays,
            0,
            False,
        )

        if not accepted:
            return None

        index = displays.index(selected)

        return str(devices[index]["device_id"])

    # ---------------------------------------------------------
    # QUICK ACTIONS
    # ---------------------------------------------------------

    def _new_customer(
        self,
    ) -> None:
        dialog = CustomerDialog(
            service=self.service,
            parent=self,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _new_device(
        self,
    ) -> None:
        customer_id = self._choose_customer()

        if customer_id is None:
            return

        dialog = DeviceDialog(
            service=self.service,
            customer_id=customer_id,
            parent=self,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _new_repair(
        self,
    ) -> None:
        customer_id = self._choose_customer()

        if customer_id is None:
            return

        device_id = self._choose_device(customer_id)

        if device_id is None:
            return

        try:
            dialog = NewRepairDialog(
                service=self.service,
                customer_id=customer_id,
                device_id=device_id,
                parent=self,
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Create Repair",
                str(exc),
            )

            return

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _new_checkin(
        self,
    ) -> None:
        repairs = self.service.list_repairs()

        if not repairs:
            QMessageBox.information(
                self,
                "No Repairs",
                "Create a repair first.",
            )

            return

        displays: list[str] = []

        for repair in repairs:
            ticket_id = str(
                repair.get(
                    "ticket_id",
                    "",
                )
            )

            status = str(
                repair.get(
                    "repair_status",
                    "",
                )
                or ""
            ).strip()

            manufacturer = str(
                repair.get(
                    "manufacturer",
                    "",
                )
                or ""
            ).strip()

            model = str(
                repair.get(
                    "device_model",
                    "",
                )
                or repair.get(
                    "device_family",
                    "",
                )
                or ""
            ).strip()

            customer_name = self._repair_customer_name(repair)

            displays.append(
                f"{ticket_id} — "
                f"{customer_name} — "
                f"{manufacturer} "
                f"{model} — "
                f"{status}"
            )

        selected, accepted = QInputDialog.getItem(
            self,
            "Select Repair",
            "Repair",
            displays,
            0,
            False,
        )

        if not accepted:
            return

        index = displays.index(selected)

        repair_id = str(repairs[index]["ticket_id"])

        try:
            dialog = NewCheckinDialog(
                service=self.service,
                repair_id=repair_id,
                parent=self,
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Create Check-In",
                str(exc),
            )

            return

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    @staticmethod
    def _repair_customer_name(
        repair: dict[str, Any],
    ) -> str:
        first_name = str(
            repair.get(
                "first_name",
                "",
            )
            or ""
        ).strip()

        last_name = str(
            repair.get(
                "last_name",
                "",
            )
            or ""
        ).strip()

        business_name = str(
            repair.get(
                "business_name",
                "",
            )
            or ""
        ).strip()

        name = " ".join(
            part
            for part in (
                first_name,
                last_name,
            )
            if part
        )

        if name:
            return name

        return business_name
