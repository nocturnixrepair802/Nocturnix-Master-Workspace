from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.services.payment_service import PaymentService
from desktop.services.read_service import ReadService
from desktop.services.repair_service import RepairService
from desktop.views.checkin_dialog import NewCheckinDialog
from desktop.views.customer_devices_dialog import DeviceDialog
from desktop.views.customers_view import CustomerDialog
from desktop.views.repair_details_panel import RepairDetailsPanel
from desktop.views.repair_dialog import (
    PRIORITIES,
    REPAIR_STATUSES,
    EditRepairDialog,
)


class RepairQueueView(QWidget):

    def __init__(
        self,
        service: RepairService,
        read_service: ReadService,
        payment_service: PaymentService,
    ) -> None:
        super().__init__()

        self.service: RepairService = service
        self.read_service = read_service
        self.payment_service = payment_service

        self.repairs: list[dict[str, Any]] = []
        self.filtered_repairs: list[dict[str, Any]] = []

        self.only_open_repairs = False
        self.pending_ticket_id: str | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        root.setContentsMargins(
            22,
            20,
            22,
            22,
        )

        root.setSpacing(12)

        title = QLabel("Repair Queue")
        title.setObjectName("pageTitle")

        subtitle = QLabel("Search, filter, and manage active repairs.")
        subtitle.setObjectName("mutedText")

        root.addWidget(title)
        root.addWidget(subtitle)

        filters = QHBoxLayout()
        filters.setSpacing(10)

        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(
            "Search ticket, customer, device, " "serial number, or problem..."
        )

        self.search_box.textChanged.connect(self._apply_filters)

        self.status_filter = QComboBox()

        self.status_filter.addItem("All Statuses")

        self.status_filter.addItems(REPAIR_STATUSES)

        self.status_filter.currentTextChanged.connect(self._filter_changed)

        self.priority_filter = QComboBox()

        self.priority_filter.addItem("All Priorities")

        self.priority_filter.addItems(PRIORITIES)

        self.priority_filter.currentTextChanged.connect(self._filter_changed)

        clear_button = QPushButton("Clear Filters")

        clear_button.clicked.connect(self.clear_filters)

        refresh_button = QPushButton("Refresh")

        refresh_button.clicked.connect(self.refresh)

        filters.addWidget(
            self.search_box,
            1,
        )

        filters.addWidget(self.status_filter)

        filters.addWidget(self.priority_filter)

        filters.addWidget(clear_button)

        filters.addWidget(refresh_button)

        root.addLayout(filters)

        self.result_label = QLabel()

        self.result_label.setObjectName("mutedText")

        root.addWidget(self.result_label)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.splitter.setChildrenCollapsible(False)

        self.table = QTableWidget()

        self.table.setColumnCount(8)

        self.table.setHorizontalHeaderLabels(
            [
                "Ticket",
                "Status",
                "Customer",
                "Manufacturer",
                "Model",
                "Serial",
                "Priority",
                "Problem",
            ]
        )

        self.table.setStyleSheet("""
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

        self.table.setWordWrap(False)

        self.table.setTextElideMode(Qt.TextElideMode.ElideRight)

        self.table.verticalHeader().setDefaultSectionSize(24)

        self.table.verticalHeader().setMinimumSectionSize(22)

        header = self.table.horizontalHeader()

        for column in range(7):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        header.setSectionResizeMode(
            7,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setMinimumSectionSize(60)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.table.setAlternatingRowColors(True)

        self.table.itemSelectionChanged.connect(self._selection_changed)

        self.table.doubleClicked.connect(self._edit_selected_repair)

        self.table.setMinimumWidth(480)

        self.splitter.addWidget(self.table)

        self.details_panel = RepairDetailsPanel(
            service=self.service,
            read_service=self.read_service,
            payment_service=self.payment_service,
            on_edit=self._edit_repair,
            on_checkin=self._new_checkin_for,
            on_customer=self._view_customer,
            on_device=self._view_device,
        )

        self.details_panel.setMinimumWidth(620)

        self.splitter.addWidget(self.details_panel)

        self.splitter.setStretchFactor(
            0,
            4,
        )

        self.splitter.setStretchFactor(
            1,
            6,
        )

        self.splitter.setSizes(
            [
                620,
                850,
            ]
        )

        root.addWidget(
            self.splitter,
            1,
        )

    # ---------------------------------------------------------
    # PUBLIC DASHBOARD / NAVIGATION METHODS
    # ---------------------------------------------------------

    def show_all_repairs(
        self,
    ) -> None:
        self.clear_filters()

    def show_open_repairs(
        self,
    ) -> None:
        self.search_box.clear()

        self.status_filter.setCurrentText("All Statuses")

        self.priority_filter.setCurrentText("All Priorities")

        self.only_open_repairs = True

        self.refresh()

    def show_status(
        self,
        status: str,
    ) -> None:
        self.search_box.clear()

        self.priority_filter.setCurrentText("All Priorities")

        self.only_open_repairs = False

        index = self.status_filter.findText(status)

        if index >= 0:
            self.status_filter.setCurrentIndex(index)

        self.refresh()

    def show_priority(
        self,
        priority: str,
    ) -> None:
        self.search_box.clear()

        self.status_filter.setCurrentText("All Statuses")

        self.only_open_repairs = False

        index = self.priority_filter.findText(priority)

        if index >= 0:
            self.priority_filter.setCurrentIndex(index)

        self.refresh()

    def show_ticket(
        self,
        ticket_id: str,
    ) -> None:
        self.search_box.clear()

        self.status_filter.setCurrentText("All Statuses")

        self.priority_filter.setCurrentText("All Priorities")

        self.only_open_repairs = False

        self.pending_ticket_id = ticket_id

        self.refresh()

    def clear_filters(
        self,
    ) -> None:
        self.only_open_repairs = False
        self.pending_ticket_id = None

        self.search_box.clear()

        self.status_filter.setCurrentText("All Statuses")

        self.priority_filter.setCurrentText("All Priorities")

        self.refresh()

    # ---------------------------------------------------------
    # REFRESH / FILTER
    # ---------------------------------------------------------

    def refresh(self) -> None:
        selected_ticket = (
            self.pending_ticket_id
            or self._selected_ticket_id()
        )

        self.repairs = (
            self.read_service.list_repairs()
        )

        self._apply_filters()

        if selected_ticket is not None:
            selected = self._select_ticket(
                selected_ticket
            )

            if selected:
                self.details_panel.load_repair(
                    selected_ticket
                )

        self.pending_ticket_id = None

    def _filter_changed(
        self,
        *_args: object,
    ) -> None:
        self.only_open_repairs = False
        self._apply_filters()

    def _apply_filters(
        self,
        *_args: object,
    ) -> None:
        query = self.search_box.text().strip().casefold()

        status = self.status_filter.currentText()

        priority = self.priority_filter.currentText()

        closed_statuses = {
            "Completed",
            "Picked Up",
            "Cancelled",
        }

        filtered: list[dict[str, Any]] = []

        for repair in self.repairs:
            repair_status = str(
                repair.get(
                    "repair_status",
                    "",
                )
                or ""
            )

            repair_priority = str(
                repair.get(
                    "priority",
                    "",
                )
                or ""
            )

            if self.only_open_repairs and repair_status in closed_statuses:
                continue

            if status != "All Statuses" and repair_status != status:
                continue

            if priority != "All Priorities" and repair_priority != priority:
                continue

            if query:
                haystack = " ".join(
                    [
                        str(
                            repair.get(
                                "ticket_id",
                                "",
                            )
                            or ""
                        ),
                        repair_status,
                        str(
                            repair.get(
                                "first_name",
                                "",
                            )
                            or ""
                        ),
                        str(
                            repair.get(
                                "last_name",
                                "",
                            )
                            or ""
                        ),
                        str(
                            repair.get(
                                "business_name",
                                "",
                            )
                            or ""
                        ),
                        str(
                            repair.get(
                                "manufacturer",
                                "",
                            )
                            or ""
                        ),
                        str(
                            repair.get(
                                "device_family",
                                "",
                            )
                            or ""
                        ),
                        str(
                            repair.get(
                                "device_model",
                                "",
                            )
                            or ""
                        ),
                        str(
                            repair.get(
                                "serial_number",
                                "",
                            )
                            or ""
                        ),
                        repair_priority,
                        str(
                            repair.get(
                                "technician",
                                "",
                            )
                            or ""
                        ),
                        str(
                            repair.get(
                                "problem_description",
                                "",
                            )
                            or ""
                        ),
                    ]
                ).casefold()

                if query not in haystack:
                    continue

            filtered.append(repair)

        self.filtered_repairs = filtered

        self._render_table()

    def _render_table(self) -> None:
        self.table.setRowCount(len(self.filtered_repairs))

        for row_index, repair in enumerate(self.filtered_repairs):
            customer_name = self._customer_name(repair)

            model = repair.get("device_model") or repair.get("device_family") or ""

            values = [
                repair.get(
                    "ticket_id",
                    "",
                ),
                repair.get(
                    "repair_status",
                    "",
                ),
                customer_name,
                repair.get(
                    "manufacturer",
                    "",
                ),
                model,
                repair.get(
                    "serial_number",
                    "",
                ),
                repair.get(
                    "priority",
                    "",
                ),
                repair.get(
                    "problem_description",
                    "",
                ),
            ]

            for column_index, value in enumerate(values):
                text = str(value or "")

                item = QTableWidgetItem(text)

                if text:
                    item.setToolTip(text)

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        prefix = ""

        if self.only_open_repairs:
            prefix = "Open Repairs — "

        self.result_label.setText(
            f"{prefix}"
            f"{len(self.filtered_repairs)} "
            f"of {len(self.repairs)} "
            "repairs shown"
        )

        if not self.filtered_repairs:
            self.details_panel.clear()

    @staticmethod
    def _customer_name(
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

    # ---------------------------------------------------------
    # SELECTION
    # ---------------------------------------------------------

    def _selected_ticket_id(
        self,
    ) -> str | None:
        row = self.table.currentRow()

        if row < 0:
            return None

        item = self.table.item(
            row,
            0,
        )

        if item is None:
            return None

        ticket_id = item.text().strip()

        return ticket_id or None

    def _selection_changed(
        self,
    ) -> None:
        ticket_id = self._selected_ticket_id()

        if ticket_id is None:
            self.details_panel.clear()
            return

        self.details_panel.load_repair(ticket_id)

    def _select_ticket(
        self,
        ticket_id: str,
    ) -> bool:
        for row in range(self.table.rowCount()):
            item = self.table.item(
                row,
                0,
            )

            if item is not None and item.text() == ticket_id:
                self.table.selectRow(row)

                self.table.scrollToItem(item)

                return True

        return False

    # ---------------------------------------------------------
    # ACTIONS
    # ---------------------------------------------------------

    def _edit_selected_repair(
        self,
        *_args: object,
    ) -> None:
        ticket_id = self._selected_ticket_id()

        if ticket_id is None:
            QMessageBox.information(
                self,
                "Select Repair",
                "Select a repair first.",
            )
            return

        self._edit_repair(ticket_id)

    def _edit_repair(
        self,
        ticket_id: str,
    ) -> None:
        try:
            dialog = EditRepairDialog(
                service=self.service,
                ticket_id=ticket_id,
                parent=self,
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Open Repair",
                str(exc),
            )
            return

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.pending_ticket_id = ticket_id

            self.refresh()

    def _new_checkin_for(
        self,
        ticket_id: str,
    ) -> None:
        try:
            dialog = NewCheckinDialog(
                service=self.service,
                repair_id=ticket_id,
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
            self.pending_ticket_id = ticket_id

            self.refresh()

    def _view_customer(
        self,
        customer_id: str,
    ) -> None:
        try:
            dialog = CustomerDialog(
                service=self.service,
                customer_id=customer_id,
                parent=self,
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Open Customer",
                str(exc),
            )
            return

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _view_device(
        self,
        customer_id: str,
        device_id: str,
    ) -> None:
        try:
            dialog = DeviceDialog(
                service=self.service,
                customer_id=customer_id,
                device_id=device_id,
                parent=self,
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Open Device",
                str(exc),
            )
            return

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()
