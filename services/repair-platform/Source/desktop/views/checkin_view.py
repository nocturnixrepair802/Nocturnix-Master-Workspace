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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.services.repair_service import RepairService
from desktop.views.checkin_dialog import NewCheckinDialog
from desktop.views.repair_dialog import EditRepairDialog


class CheckinView(QWidget):
    def __init__(
        self,
        service: RepairService,
    ) -> None:
        super().__init__()

        self.service: RepairService = service

        self.checkins: list[dict[str, Any]] = []

        self.filtered_checkins: list[dict[str, Any]] = []

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

        title = QLabel("Check-Ins")

        title.setObjectName("pageTitle")

        subtitle = QLabel("Search and review repair check-ins.")

        subtitle.setObjectName("mutedText")

        root.addWidget(title)

        root.addWidget(subtitle)

        filters = QHBoxLayout()
        filters.setSpacing(10)

        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(
            "Search check-in, repair, customer, "
            "device, manufacturer, model, or serial..."
        )

        self.search_box.textChanged.connect(self._apply_filters)

        self.powers_filter = QComboBox()

        self.powers_filter.addItems(
            [
                "All Power States",
                "Yes",
                "No",
                "Unknown",
            ]
        )

        self.powers_filter.currentTextChanged.connect(self._apply_filters)

        self.liquid_filter = QComboBox()

        self.liquid_filter.addItems(
            [
                "All Liquid States",
                "Yes",
                "No",
                "Unknown",
            ]
        )

        self.liquid_filter.currentTextChanged.connect(self._apply_filters)

        self.passcode_filter = QComboBox()

        self.passcode_filter.addItems(
            [
                "All Passcode States",
                "Yes",
                "No",
                "Unknown",
            ]
        )

        self.passcode_filter.currentTextChanged.connect(self._apply_filters)

        refresh_button = QPushButton("Refresh")

        refresh_button.clicked.connect(self.refresh)

        filters.addWidget(
            self.search_box,
            1,
        )

        filters.addWidget(self.powers_filter)

        filters.addWidget(self.liquid_filter)

        filters.addWidget(self.passcode_filter)

        filters.addWidget(refresh_button)

        root.addLayout(filters)

        self.result_label = QLabel()

        self.result_label.setObjectName("mutedText")

        root.addWidget(self.result_label)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        new_checkin_button = QPushButton("＋ New Check-In")

        new_checkin_button.setObjectName("primaryButton")

        new_checkin_button.clicked.connect(self._new_checkin)

        repair_button = QPushButton("Open Linked Repair")

        repair_button.clicked.connect(self._open_repair)

        actions.addWidget(new_checkin_button)

        actions.addWidget(repair_button)

        actions.addStretch(1)

        root.addLayout(actions)

        self.table = QTableWidget()

        self.table.setColumnCount(10)

        self.table.setHorizontalHeaderLabels(
            [
                "Check-In",
                "Repair",
                "Date",
                "Customer",
                "Manufacturer",
                "Model",
                "Serial",
                "Powers On",
                "Battery",
                "Liquid Damage",
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

        for column in range(self.table.columnCount()):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        header.setStretchLastSection(True)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.table.setAlternatingRowColors(True)

        self.table.doubleClicked.connect(self._open_repair)

        root.addWidget(
            self.table,
            1,
        )

    def refresh(self) -> None:
        selected_checkin = self._selected_checkin_id()

        self.checkins = self.service.list_checkins()

        self._apply_filters()

        if selected_checkin is not None:
            self._select_checkin(selected_checkin)

    def _apply_filters(
        self,
        *_args: object,
    ) -> None:
        query = self.search_box.text().strip().casefold()

        powers_filter = self.powers_filter.currentText()

        liquid_filter = self.liquid_filter.currentText()

        passcode_filter = self.passcode_filter.currentText()

        filtered: list[dict[str, Any]] = []

        for checkin in self.checkins:
            powers_on = str(
                checkin.get(
                    "powers_on",
                    "",
                )
                or ""
            )

            liquid_damage = str(
                checkin.get(
                    "liquid_damage",
                    "",
                )
                or ""
            )

            passcode_available = str(
                checkin.get(
                    "passcode_available",
                    "",
                )
                or ""
            )

            if powers_filter != "All Power States" and powers_on != powers_filter:
                continue

            if liquid_filter != "All Liquid States" and liquid_damage != liquid_filter:
                continue

            if (
                passcode_filter != "All Passcode States"
                and passcode_available != passcode_filter
            ):
                continue

            if query:
                haystack = " ".join(
                    [
                        str(
                            checkin.get(
                                "checkin_id",
                                "",
                            )
                            or ""
                        ),
                        str(
                            checkin.get(
                                "repair_id",
                                "",
                            )
                            or ""
                        ),
                        str(
                            checkin.get(
                                "first_name",
                                "",
                            )
                            or ""
                        ),
                        str(
                            checkin.get(
                                "last_name",
                                "",
                            )
                            or ""
                        ),
                        str(
                            checkin.get(
                                "business_name",
                                "",
                            )
                            or ""
                        ),
                        str(
                            checkin.get(
                                "manufacturer",
                                "",
                            )
                            or ""
                        ),
                        str(
                            checkin.get(
                                "device_model",
                                "",
                            )
                            or ""
                        ),
                        str(
                            checkin.get(
                                "serial_number",
                                "",
                            )
                            or ""
                        ),
                        powers_on,
                        liquid_damage,
                        passcode_available,
                    ]
                ).casefold()

                if query not in haystack:
                    continue

            filtered.append(checkin)

        self.filtered_checkins = filtered

        self._render_table()

    def _render_table(self) -> None:
        self.table.setRowCount(len(self.filtered_checkins))

        for row_index, checkin in enumerate(self.filtered_checkins):
            customer_name = self._customer_name(checkin)

            battery = checkin.get("battery_percentage")

            battery_text = "" if battery is None else f"{battery}%"

            values = [
                checkin.get(
                    "checkin_id",
                    "",
                ),
                checkin.get(
                    "repair_id",
                    "",
                ),
                checkin.get(
                    "checkin_timestamp",
                    "",
                ),
                customer_name,
                checkin.get(
                    "manufacturer",
                    "",
                ),
                checkin.get(
                    "device_model",
                    "",
                ),
                checkin.get(
                    "serial_number",
                    "",
                ),
                checkin.get(
                    "powers_on",
                    "",
                ),
                battery_text,
                checkin.get(
                    "liquid_damage",
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

        self.result_label.setText(
            f"{len(self.filtered_checkins)} "
            f"of {len(self.checkins)} "
            "check-ins shown"
        )

    @staticmethod
    def _customer_name(
        checkin: dict[str, Any],
    ) -> str:
        first_name = str(
            checkin.get(
                "first_name",
                "",
            )
            or ""
        ).strip()

        last_name = str(
            checkin.get(
                "last_name",
                "",
            )
            or ""
        ).strip()

        business_name = str(
            checkin.get(
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

    def _selected_checkin_id(
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

        value = item.text().strip()

        return value or None

    def _selected_repair_id(
        self,
    ) -> str | None:
        row = self.table.currentRow()

        if row < 0:
            return None

        item = self.table.item(
            row,
            1,
        )

        if item is None:
            return None

        value = item.text().strip()

        return value or None

    def _select_checkin(
        self,
        checkin_id: str,
    ) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(
                row,
                0,
            )

            if item is not None and item.text() == checkin_id:
                self.table.selectRow(row)
                return

    def _open_repair(
        self,
        *_args: object,
    ) -> None:
        repair_id = self._selected_repair_id()

        if repair_id is None:
            QMessageBox.information(
                self,
                "Select Check-In",
                "Select a check-in first.",
            )
            return

        try:
            dialog = EditRepairDialog(
                service=self.service,
                ticket_id=repair_id,
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

            customer_name = self._repair_customer_name(repair)

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

            status = str(
                repair.get(
                    "repair_status",
                    "",
                )
                or ""
            ).strip()

            displays.append(
                f"{ticket_id} — "
                f"{customer_name} — "
                f"{manufacturer} {model} — "
                f"{status}"
            )

        selected, accepted = QComboBoxDialog.get_item(
            self,
            displays,
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


class QComboBoxDialog:
    @staticmethod
    def get_item(
        parent: QWidget,
        items: list[str],
    ) -> tuple[str, bool]:
        from PySide6.QtWidgets import QInputDialog

        selected, accepted = QInputDialog.getItem(
            parent,
            "Select Repair",
            "Repair",
            items,
            0,
            False,
        )

        return selected, accepted
