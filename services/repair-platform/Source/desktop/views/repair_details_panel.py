from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop.services.repair_service import RepairService


class RepairDetailsPanel(QWidget):
    def __init__(
        self,
        service: RepairService,
        *,
        on_edit: Callable[[str], None],
        on_checkin: Callable[[str], None],
        on_customer: Callable[[str], None],
        on_device: Callable[[str, str], None],
    ) -> None:
        super().__init__()

        self.service: RepairService = service

        self.on_edit = on_edit
        self.on_checkin = on_checkin
        self.on_customer = on_customer
        self.on_device = on_device

        self.ticket_id: str | None = None
        self.customer_id: str | None = None
        self.device_id: str | None = None

        self._build_ui()
        self.clear()

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
            22,
            18,
            22,
            22,
        )
        root.setSpacing(16)

        self.title = QLabel("Repair Details")
        self.title.setObjectName("sectionTitle")

        self.subtitle = QLabel("Select a repair from the queue.")
        self.subtitle.setObjectName("mutedText")
        self.subtitle.setWordWrap(True)

        root.addWidget(self.title)
        root.addWidget(self.subtitle)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        self.edit_button = QPushButton("Edit Repair")
        self.edit_button.setObjectName("primaryButton")
        self.edit_button.clicked.connect(self._edit_clicked)

        self.checkin_button = QPushButton("＋ New Check-In")
        self.checkin_button.clicked.connect(self._checkin_clicked)

        self.customer_button = QPushButton("View Customer")
        self.customer_button.clicked.connect(self._customer_clicked)

        self.device_button = QPushButton("View Device")
        self.device_button.clicked.connect(self._device_clicked)

        actions.addWidget(self.edit_button)
        actions.addWidget(self.checkin_button)
        actions.addWidget(self.customer_button)
        actions.addWidget(self.device_button)
        actions.addStretch(1)

        root.addLayout(actions)

        summary_box = QGroupBox("Repair Summary")

        summary_box.setMinimumHeight(360)

        summary_layout = QGridLayout(summary_box)

        summary_layout.setContentsMargins(
            18,
            24,
            18,
            18,
        )

        summary_layout.setHorizontalSpacing(22)

        summary_layout.setVerticalSpacing(10)

        summary_layout.setColumnMinimumWidth(
            0,
            155,
        )

        summary_layout.setColumnStretch(
            0,
            0,
        )

        summary_layout.setColumnStretch(
            1,
            1,
        )

        self.status_value = QLabel()
        self.priority_value = QLabel()
        self.technician_value = QLabel()
        self.intake_value = QLabel()
        self.due_value = QLabel()

        self.customer_value = QLabel()
        self.customer_contact_value = QLabel()

        self.device_value = QLabel()
        self.serial_value = QLabel()
        self.imei_value = QLabel()

        self.estimate_value = QLabel()
        self.final_value = QLabel()
        self.warranty_value = QLabel()

        value_labels = (
            self.status_value,
            self.priority_value,
            self.technician_value,
            self.intake_value,
            self.due_value,
            self.customer_value,
            self.customer_contact_value,
            self.device_value,
            self.serial_value,
            self.imei_value,
            self.estimate_value,
            self.final_value,
            self.warranty_value,
        )

        for label in value_labels:
            label.setWordWrap(True)
            label.setMinimumHeight(24)
            label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )

        summary_rows = [
            (
                "Status",
                self.status_value,
            ),
            (
                "Priority",
                self.priority_value,
            ),
            (
                "Technician",
                self.technician_value,
            ),
            (
                "Intake Date",
                self.intake_value,
            ),
            (
                "Due Date",
                self.due_value,
            ),
            (
                "Customer",
                self.customer_value,
            ),
            (
                "Contact",
                self.customer_contact_value,
            ),
            (
                "Device",
                self.device_value,
            ),
            (
                "Serial",
                self.serial_value,
            ),
            (
                "IMEI / Service Tag",
                self.imei_value,
            ),
            (
                "Estimate",
                self.estimate_value,
            ),
            (
                "Final Cost",
                self.final_value,
            ),
            (
                "Warranty",
                self.warranty_value,
            ),
        ]

        for row_index, (
            field_name,
            field_value,
        ) in enumerate(summary_rows):
            field_label = QLabel(field_name)

            field_label.setMinimumHeight(24)

            field_label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )

            summary_layout.addWidget(
                field_label,
                row_index,
                0,
            )

            summary_layout.addWidget(
                field_value,
                row_index,
                1,
            )

        root.addWidget(summary_box)

        information_box = QGroupBox("Repair Information")

        information_layout = QGridLayout(information_box)

        information_layout.setContentsMargins(
            18,
            24,
            18,
            18,
        )

        information_layout.setHorizontalSpacing(16)

        information_layout.setVerticalSpacing(12)

        information_layout.setColumnMinimumWidth(
            0,
            110,
        )

        information_layout.setColumnStretch(
            1,
            1,
        )

        self.problem_value = QTextEdit()
        self.problem_value.setReadOnly(True)
        self.problem_value.setMinimumHeight(90)
        self.problem_value.setMaximumHeight(130)

        self.diagnosis_value = QTextEdit()
        self.diagnosis_value.setReadOnly(True)
        self.diagnosis_value.setMinimumHeight(90)
        self.diagnosis_value.setMaximumHeight(130)

        self.notes_value = QTextEdit()
        self.notes_value.setReadOnly(True)
        self.notes_value.setMinimumHeight(80)
        self.notes_value.setMaximumHeight(120)

        problem_label = QLabel("Problem")

        diagnosis_label = QLabel("Diagnosis")

        notes_label = QLabel("Notes")

        information_layout.addWidget(
            problem_label,
            0,
            0,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        information_layout.addWidget(
            self.problem_value,
            0,
            1,
        )

        information_layout.addWidget(
            diagnosis_label,
            1,
            0,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        information_layout.addWidget(
            self.diagnosis_value,
            1,
            1,
        )

        information_layout.addWidget(
            notes_label,
            2,
            0,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        information_layout.addWidget(
            self.notes_value,
            2,
            1,
        )

        root.addWidget(information_box)

        history_title = QLabel("Repair Activity")
        history_title.setObjectName("sectionTitle")

        root.addWidget(history_title)

        self.tabs = QTabWidget()
        self.tabs.setMinimumHeight(300)

        self.checkins_table = self._build_checkins_table()

        self.events_table = self._build_events_table()

        self.tabs.addTab(
            self.checkins_table,
            "Check-In History",
        )

        self.tabs.addTab(
            self.events_table,
            "Repair History",
        )

        root.addWidget(self.tabs)

        root.addStretch(1)

        self.scroll_area.setWidget(content)

        outer_layout.addWidget(self.scroll_area)

    @staticmethod
    def _build_checkins_table() -> QTableWidget:
        table = QTableWidget()

        table.setColumnCount(7)

        table.setHorizontalHeaderLabels(
            [
                "Check-In",
                "Date",
                "Technician",
                "Powers On",
                "Battery",
                "Liquid",
                "Notes",
            ]
        )

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        table.setAlternatingRowColors(True)

        return table

    @staticmethod
    def _build_events_table() -> QTableWidget:
        table = QTableWidget()

        table.setColumnCount(6)

        table.setHorizontalHeaderLabels(
            [
                "Date",
                "Type",
                "Old",
                "New",
                "By",
                "Notes",
            ]
        )

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        table.setAlternatingRowColors(True)

        return table

    def clear(self) -> None:
        self.ticket_id = None
        self.customer_id = None
        self.device_id = None

        self.title.setText("Repair Details")

        self.subtitle.setText("Select a repair from the queue.")

        for label in (
            self.status_value,
            self.priority_value,
            self.technician_value,
            self.intake_value,
            self.due_value,
            self.customer_value,
            self.customer_contact_value,
            self.device_value,
            self.serial_value,
            self.imei_value,
            self.estimate_value,
            self.final_value,
            self.warranty_value,
        ):
            label.clear()

        self.problem_value.clear()
        self.diagnosis_value.clear()
        self.notes_value.clear()

        self.checkins_table.setRowCount(0)

        self.events_table.setRowCount(0)

        self._set_actions_enabled(False)

    def _set_actions_enabled(
        self,
        enabled: bool,
    ) -> None:
        self.edit_button.setEnabled(enabled)

        self.checkin_button.setEnabled(enabled)

        self.customer_button.setEnabled(enabled)

        self.device_button.setEnabled(enabled)

    def load_repair(
        self,
        ticket_id: str,
    ) -> None:
        repair = self.service.get_repair_workspace(ticket_id)

        if repair is None:
            self.clear()
            return

        self.ticket_id = str(repair["ticket_id"])

        self.customer_id = str(repair["customer_id"])

        self.device_id = str(repair["device_id"])

        customer_name = self._customer_name(repair)

        device_name = self._device_name(repair)

        self.title.setText(f"Repair {self.ticket_id}")

        self.subtitle.setText(f"{customer_name}  •  {device_name}")

        self.status_value.setText(self._text(repair.get("repair_status")))

        self.priority_value.setText(self._text(repair.get("priority")))

        self.technician_value.setText(self._text(repair.get("technician")))

        self.intake_value.setText(self._text(repair.get("intake_date")))

        self.due_value.setText(self._text(repair.get("due_date")))

        self.customer_value.setText(f"{self.customer_id} — " f"{customer_name}")

        contact_parts = [
            self._text(repair.get("email")),
            self._text(repair.get("mobile_phone")),
        ]

        self.customer_contact_value.setText(
            " | ".join(part for part in contact_parts if part)
        )

        self.device_value.setText(f"{self.device_id} — " f"{device_name}")

        self.serial_value.setText(self._text(repair.get("serial_number")))

        self.imei_value.setText(self._text(repair.get("imei_service_tag")))

        self.estimate_value.setText(self._currency(repair.get("estimated_cost")))

        self.final_value.setText(self._currency(repair.get("final_cost")))

        self.warranty_value.setText("Yes" if bool(repair.get("warranty")) else "No")

        self.problem_value.setPlainText(self._text(repair.get("problem_description")))

        self.diagnosis_value.setPlainText(self._text(repair.get("diagnosis")))

        self.notes_value.setPlainText(self._text(repair.get("notes")))

        self._load_checkins()
        self._load_events()

        self._set_actions_enabled(True)

    @staticmethod
    def _text(
        value: object,
    ) -> str:
        if value is None:
            return ""

        return str(value).strip()

    @staticmethod
    def _currency(
        value: object,
    ) -> str:
        if value is None:
            return ""

        text = str(value).strip()

        if not text:
            return ""

        try:
            amount = float(text)
        except ValueError:
            return text

        return f"${amount:,.2f}"

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

        if business_name:
            return business_name

        return "Unnamed Customer"

    @staticmethod
    def _device_name(
        repair: dict[str, Any],
    ) -> str:
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

        return "Unknown Device"

    def _load_checkins(self) -> None:
        if self.ticket_id is None:
            self.checkins_table.setRowCount(0)
            return

        rows = self.service.list_repair_checkins(self.ticket_id)

        self.checkins_table.setRowCount(len(rows))

        for row_index, checkin in enumerate(rows):
            battery = checkin.get("battery_percentage")

            battery_text = "" if battery is None else f"{battery}%"

            values = [
                checkin.get(
                    "checkin_id",
                    "",
                ),
                checkin.get(
                    "checkin_timestamp",
                    "",
                ),
                checkin.get(
                    "technician",
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
                checkin.get(
                    "intake_notes",
                    "",
                ),
            ]

            for column_index, value in enumerate(values):
                self.checkins_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(str(value or "")),
                )

    def _load_events(self) -> None:
        if self.ticket_id is None:
            self.events_table.setRowCount(0)
            return

        rows = self.service.list_repair_events(self.ticket_id)

        self.events_table.setRowCount(len(rows))

        for row_index, event in enumerate(rows):
            values = [
                event.get(
                    "created_at",
                    "",
                ),
                event.get(
                    "event_type",
                    "",
                ),
                event.get(
                    "old_value",
                    "",
                ),
                event.get(
                    "new_value",
                    "",
                ),
                event.get(
                    "created_by",
                    "",
                ),
                event.get(
                    "notes",
                    "",
                ),
            ]

            for column_index, value in enumerate(values):
                self.events_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(str(value or "")),
                )

    def _edit_clicked(self) -> None:
        if self.ticket_id is None:
            return

        self.on_edit(self.ticket_id)

    def _checkin_clicked(self) -> None:
        if self.ticket_id is None:
            return

        self.on_checkin(self.ticket_id)

    def _customer_clicked(self) -> None:
        if self.customer_id is None:
            return

        self.on_customer(self.customer_id)

    def _device_clicked(self) -> None:
        if self.customer_id is None or self.device_id is None:
            return

        self.on_device(
            self.customer_id,
            self.device_id,
        )
