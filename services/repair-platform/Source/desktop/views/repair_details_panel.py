from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop.services.payment_service import PaymentService
from desktop.services.repair_service import RepairService
from desktop.services.square_service import SquareService


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

        self.service = service
        self.payment_service = PaymentService()

        self.on_edit = on_edit
        self.on_checkin = on_checkin
        self.on_customer = on_customer
        self.on_device = on_device

        self.ticket_id: str | None = None
        self.customer_id: str | None = None
        self.device_id: str | None = None

        self.current_repair: dict[str, Any] | None = None
        self.current_events: list[dict[str, Any]] = []
        self.current_payments: list[dict[str, Any]] = []

        self._build_ui()
        self.clear()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self.root = QVBoxLayout(content)

        self.root.setContentsMargins(
            22,
            18,
            22,
            22,
        )

        self.root.setSpacing(16)

        # -----------------------------------------------------
        # HEADER
        # -----------------------------------------------------

        self.title = QLabel("Repair Details")
        self.title.setObjectName("sectionTitle")

        self.subtitle = QLabel("Select a repair from the queue.")
        self.subtitle.setObjectName("mutedText")
        self.subtitle.setWordWrap(True)

        self.root.addWidget(self.title)
        self.root.addWidget(self.subtitle)

        # -----------------------------------------------------
        # PRIMARY ACTIONS
        # -----------------------------------------------------

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

        self.print_button = QPushButton("Print Repair History")
        self.print_button.clicked.connect(self._print_repair_history)

        actions.addWidget(self.edit_button)
        actions.addWidget(self.checkin_button)
        actions.addWidget(self.customer_button)
        actions.addWidget(self.device_button)
        actions.addStretch(1)
        actions.addWidget(self.print_button)

        self.root.addLayout(actions)

        # -----------------------------------------------------
        # DIRECT LIFECYCLE ACTIONS
        # -----------------------------------------------------

        lifecycle_box = QGroupBox("Repair Lifecycle Actions")

        lifecycle_layout = QHBoxLayout(lifecycle_box)

        lifecycle_layout.setContentsMargins(
            16,
            20,
            16,
            14,
        )

        lifecycle_layout.setSpacing(10)

        self.complete_button = QPushButton("Mark Repair Complete")
        self.complete_button.clicked.connect(self._mark_repair_complete)

        self.ready_button = QPushButton("Ready for Pickup")
        self.ready_button.clicked.connect(self._mark_ready_for_pickup)

        self.picked_up_button = QPushButton("Mark Picked Up")
        self.picked_up_button.clicked.connect(self._mark_picked_up)

        lifecycle_layout.addWidget(self.complete_button)
        lifecycle_layout.addWidget(self.ready_button)
        lifecycle_layout.addWidget(self.picked_up_button)
        lifecycle_layout.addStretch(1)

        self.root.addWidget(lifecycle_box)

        # -----------------------------------------------------
        # REPAIR SUMMARY
        # -----------------------------------------------------

        summary_box = QGroupBox("Repair Summary")
        summary_box.setMinimumHeight(410)

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
        self.completed_value = QLabel()
        self.picked_up_value = QLabel()

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
            self.completed_value,
            self.picked_up_value,
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
            ("Status", self.status_value),
            ("Priority", self.priority_value),
            ("Technician", self.technician_value),
            ("Intake Date", self.intake_value),
            ("Due Date", self.due_value),
            ("Completed At", self.completed_value),
            ("Picked Up At", self.picked_up_value),
            ("Customer", self.customer_value),
            ("Contact", self.customer_contact_value),
            ("Device", self.device_value),
            ("Serial", self.serial_value),
            ("IMEI / Service Tag", self.imei_value),
            ("Estimate", self.estimate_value),
            ("Final Cost", self.final_value),
            ("Warranty", self.warranty_value),
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

        self.root.addWidget(summary_box)

        # -----------------------------------------------------
        # PAYMENT / CLOSEOUT
        # -----------------------------------------------------

        payment_box = QGroupBox("Payment / Closeout")

        payment_layout = QGridLayout(payment_box)

        payment_layout.setContentsMargins(
            18,
            24,
            18,
            18,
        )

        payment_layout.setHorizontalSpacing(18)
        payment_layout.setVerticalSpacing(10)

        payment_layout.setColumnMinimumWidth(
            0,
            145,
        )
        payment_layout.setColumnStretch(
            1,
            1,
        )

        self.payment_final_cost = QLabel()
        self.payment_amount_paid = QLabel()
        self.payment_balance_due = QLabel()
        self.payment_status_value = QLabel()

        payment_values = (
            self.payment_final_cost,
            self.payment_amount_paid,
            self.payment_balance_due,
            self.payment_status_value,
        )

        for label in payment_values:
            label.setMinimumHeight(24)
            label.setWordWrap(True)

        payment_layout.addWidget(
            QLabel("Final Cost"),
            0,
            0,
        )
        payment_layout.addWidget(
            self.payment_final_cost,
            0,
            1,
        )

        payment_layout.addWidget(
            QLabel("Amount Paid"),
            1,
            0,
        )
        payment_layout.addWidget(
            self.payment_amount_paid,
            1,
            1,
        )

        payment_layout.addWidget(
            QLabel("Balance Due"),
            2,
            0,
        )
        payment_layout.addWidget(
            self.payment_balance_due,
            2,
            1,
        )

        payment_layout.addWidget(
            QLabel("Payment Status"),
            3,
            0,
        )
        payment_layout.addWidget(
            self.payment_status_value,
            3,
            1,
        )

        payment_actions = QHBoxLayout()

        self.cash_payment_button = QPushButton("Record Cash Payment")
        self.cash_payment_button.clicked.connect(self._record_cash_payment)

        self.square_payment_button = QPushButton("Take Payment with Square")
        self.square_payment_button.clicked.connect(self._take_square_payment)

        payment_actions.addWidget(self.cash_payment_button)
        payment_actions.addWidget(self.square_payment_button)
        payment_actions.addStretch(1)

        payment_layout.addLayout(
            payment_actions,
            4,
            0,
            1,
            2,
        )

        self.root.addWidget(payment_box)

        # -----------------------------------------------------
        # PAYMENT HISTORY
        # -----------------------------------------------------

        payment_history_title = QLabel("Payment History")
        payment_history_title.setObjectName("sectionTitle")

        self.root.addWidget(payment_history_title)

        self.payments_table = self._build_payments_table()

        self.root.addWidget(self.payments_table)

        # -----------------------------------------------------
        # REPAIR INFORMATION
        # -----------------------------------------------------

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

        information_layout.addWidget(
            QLabel("Problem"),
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
            QLabel("Diagnosis"),
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
            QLabel("Notes"),
            2,
            0,
            alignment=Qt.AlignmentFlag.AlignTop,
        )
        information_layout.addWidget(
            self.notes_value,
            2,
            1,
        )

        self.root.addWidget(information_box)

        # -----------------------------------------------------
        # CHECK-IN HISTORY
        # -----------------------------------------------------

        checkin_title = QLabel("Check-In History")
        checkin_title.setObjectName("sectionTitle")
        self.root.addWidget(checkin_title)

        checkin_note = QLabel(
            "Recorded intake and device-condition " "check-ins for this repair."
        )
        checkin_note.setObjectName("mutedText")
        checkin_note.setWordWrap(True)
        self.root.addWidget(checkin_note)

        self.checkins_table = self._build_checkins_table()
        self.root.addWidget(self.checkins_table)

        # -----------------------------------------------------
        # REPAIR EVENT HISTORY
        # -----------------------------------------------------

        event_header = QHBoxLayout()

        event_title = QLabel("Repair Event History")
        event_title.setObjectName("sectionTitle")

        event_header.addWidget(event_title)
        event_header.addStretch(1)

        self.event_count = QLabel("0 events")
        self.event_count.setObjectName("mutedText")

        event_header.addWidget(self.event_count)

        self.root.addLayout(event_header)

        event_note = QLabel(
            "Each audit event is displayed as a readable "
            "record. Scroll down to review the complete "
            "repair history."
        )

        event_note.setObjectName("mutedText")
        event_note.setWordWrap(True)
        self.root.addWidget(event_note)

        self.events_container = QWidget()

        self.events_layout = QVBoxLayout(self.events_container)

        self.events_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.events_layout.setSpacing(10)

        self.root.addWidget(self.events_container)

        self.root.addStretch(1)

        self.scroll_area.setWidget(content)

        outer_layout.addWidget(self.scroll_area)

    @staticmethod
    def _build_payments_table() -> QTableWidget:
        table = QTableWidget()

        table.setColumnCount(7)

        table.setHorizontalHeaderLabels(
            [
                "Payment",
                "Date",
                "Method",
                "Status",
                "Amount",
                "Reference",
                "Square Payment ID",
            ]
        )

        table.setMinimumHeight(200)
        table.setMaximumHeight(300)
        table.setWordWrap(False)

        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        table.setAlternatingRowColors(True)

        table.verticalHeader().setDefaultSectionSize(24)

        header = table.horizontalHeader()

        for column in range(table.columnCount()):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.Stretch,
        )

        return table

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

        table.setMinimumHeight(220)
        table.setMaximumHeight(320)
        table.setWordWrap(False)

        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        table.setAlternatingRowColors(True)

        table.verticalHeader().setDefaultSectionSize(24)

        header = table.horizontalHeader()

        for column in range(table.columnCount()):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.Stretch,
        )

        return table

    # ---------------------------------------------------------
    # CLEAR / LOAD
    # ---------------------------------------------------------

    def clear(self) -> None:
        self.ticket_id = None
        self.customer_id = None
        self.device_id = None

        self.current_repair = None
        self.current_events = []
        self.current_payments = []

        self.title.setText("Repair Details")

        self.subtitle.setText("Select a repair from the queue.")

        for label in (
            self.status_value,
            self.priority_value,
            self.technician_value,
            self.intake_value,
            self.due_value,
            self.completed_value,
            self.picked_up_value,
            self.customer_value,
            self.customer_contact_value,
            self.device_value,
            self.serial_value,
            self.imei_value,
            self.estimate_value,
            self.final_value,
            self.warranty_value,
            self.payment_final_cost,
            self.payment_amount_paid,
            self.payment_balance_due,
            self.payment_status_value,
        ):
            label.clear()

        self.problem_value.clear()
        self.diagnosis_value.clear()
        self.notes_value.clear()

        self.checkins_table.setRowCount(0)
        self.payments_table.setRowCount(0)

        self._clear_event_widgets()

        self.event_count.setText("0 events")

        self._set_actions_enabled(False)

    def _set_actions_enabled(
        self,
        enabled: bool,
    ) -> None:
        self.edit_button.setEnabled(enabled)
        self.checkin_button.setEnabled(enabled)
        self.customer_button.setEnabled(enabled)
        self.device_button.setEnabled(enabled)
        self.print_button.setEnabled(enabled)

        self.complete_button.setEnabled(enabled)
        self.ready_button.setEnabled(enabled)
        self.picked_up_button.setEnabled(enabled)

        self.cash_payment_button.setEnabled(enabled)
        self.square_payment_button.setEnabled(enabled)

    def load_repair(
        self,
        ticket_id: str,
    ) -> None:
        repair = self.service.get_repair_workspace(ticket_id)

        if repair is None:
            self.clear()
            return

        self.current_repair = repair

        self.ticket_id = str(repair["ticket_id"])

        self.customer_id = str(repair["customer_id"])

        self.device_id = str(repair["device_id"])

        customer_name = self._customer_name(repair)

        device_name = self._device_name(repair)

        self.title.setText(f"Repair {self.ticket_id}")

        self.subtitle.setText(f"{customer_name}  •  " f"{device_name}")

        self.status_value.setText(self._text(repair.get("repair_status")))

        self.priority_value.setText(self._text(repair.get("priority")))

        self.technician_value.setText(self._text(repair.get("technician")))

        self.intake_value.setText(self._format_datetime(repair.get("intake_date")))

        self.due_value.setText(self._text(repair.get("due_date")))

        self.completed_value.setText(
            self._format_datetime(repair.get("date_completed"))
        )

        self.picked_up_value.setText(
            self._format_datetime(repair.get("date_picked_up"))
        )

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

        self._load_payment_summary()
        self._load_payments()
        self._load_checkins()
        self._load_events()

        self._set_actions_enabled(True)

        self._update_lifecycle_buttons()
        self._update_payment_buttons()

    # ---------------------------------------------------------
    # PAYMENTS
    # ---------------------------------------------------------

    def _load_payment_summary(
        self,
    ) -> None:
        if self.ticket_id is None:
            return

        summary = self.payment_service.payment_summary(self.ticket_id)

        self.payment_final_cost.setText(self._currency(summary.get("final_cost")))

        self.payment_amount_paid.setText(self._currency(summary.get("amount_paid")))

        self.payment_balance_due.setText(self._currency(summary.get("balance_due")))

        self.payment_status_value.setText(self._text(summary.get("payment_status")))

    def _load_payments(
        self,
    ) -> None:
        if self.ticket_id is None:
            self.current_payments = []
            self.payments_table.setRowCount(0)
            return

        payments = self.payment_service.list_repair_payments(self.ticket_id)

        self.current_payments = payments

        self.payments_table.setRowCount(len(payments))

        for row_index, payment in enumerate(payments):
            values = [
                payment.get(
                    "payment_id",
                    "",
                ),
                self._format_datetime(
                    payment.get(
                        "payment_timestamp",
                        "",
                    )
                ),
                payment.get(
                    "payment_method",
                    "",
                ),
                payment.get(
                    "payment_status",
                    "",
                ),
                self._currency(payment.get("amount")),
                payment.get(
                    "reference_number",
                    "",
                ),
                payment.get(
                    "square_payment_id",
                    "",
                ),
            ]

            for column_index, value in enumerate(values):
                text = str(value or "")

                item = QTableWidgetItem(text)

                if text:
                    item.setToolTip(text)

                self.payments_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    def _record_cash_payment(
        self,
    ) -> None:
        if self.ticket_id is None:
            return

        summary = self.payment_service.payment_summary(self.ticket_id)

        balance_due = float(
            summary.get(
                "balance_due",
                0.0,
            )
            or 0.0
        )

        if balance_due <= 0:
            QMessageBox.information(
                self,
                "No Balance Due",
                ("This repair currently has " "no outstanding balance."),
            )
            return

        amount, accepted = QInputDialog.getDouble(
            self,
            "Record Cash Payment",
            "Cash amount received:",
            balance_due,
            0.01,
            999999.99,
            2,
        )

        if not accepted:
            return

        if amount > balance_due:
            answer = QMessageBox.question(
                self,
                "Payment Exceeds Balance",
                (
                    f"The payment amount "
                    f"{self._currency(amount)} "
                    f"is greater than the current "
                    f"balance of "
                    f"{self._currency(balance_due)}.\n\n"
                    "Record it anyway?"
                ),
                (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No),
                QMessageBox.StandardButton.No,
            )

            if answer != QMessageBox.StandardButton.Yes:
                return

        try:
            payment = self.payment_service.record_cash_payment(
                self.ticket_id,
                amount=amount,
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Cash Payment Failed",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Cash Payment Recorded",
            (f"{payment['payment_id']} " f"was recorded successfully."),
        )

        self.load_repair(self.ticket_id)


    def _take_square_payment(
        self,
    ) -> None:
        if self.ticket_id is None:
            return

        summary = self.payment_service.payment_summary(self.ticket_id)

        balance_due = float(
            summary.get(
                "balance_due",
                0.0,
            )
            or 0.0
        )

        if balance_due <= 0:
            QMessageBox.information(
                self,
                "No Balance Due",
                ("This repair currently has " "no outstanding balance."),
            )
            return

        amount, accepted = QInputDialog.getDouble(
            self,
            "Square Sandbox Payment",
            "Sandbox payment amount:",
            min(
                balance_due,
                1.00,
            ),
            0.01,
            balance_due,
            2,
        )

        if not accepted:
            return

        answer = QMessageBox.question(
            self,
            "Confirm Square Sandbox Payment",
            (
                f"Create a Square Sandbox card payment "
                f"for {self._currency(amount)}?\n\n"
                f"Repair: {self.ticket_id}\n"
                f"Current balance: "
                f"{self._currency(balance_due)}\n\n"
                "This uses Square's Sandbox test card source. "
                "No real card will be charged."
            ),
            (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No),
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            square_service = SquareService()

            square_payment = square_service.create_sandbox_card_payment(
                amount=amount,
                repair_id=self.ticket_id,
            )

            square_status = square_payment.status.strip().upper()

            if square_status != "COMPLETED":
                QMessageBox.warning(
                    self,
                    "Square Payment Not Completed",
                    (
                        "Square created the Sandbox payment, "
                        "but its status is not COMPLETED.\n\n"
                        f"Square Payment ID: "
                        f"{square_payment.payment_id}\n"
                        f"Status: "
                        f"{square_payment.status}\n\n"
                        "The payment was not recorded as a "
                        "completed local repair payment."
                    ),
                )
                return

            payment = self.payment_service.record_square_payment(
                self.ticket_id,
                amount=square_payment.amount,
                square_payment_id=(square_payment.payment_id),
                square_order_id=(square_payment.order_id),
                square_receipt_url=(square_payment.receipt_url),
                payment_status="Completed",
                reference_number=(square_payment.payment_id),
                notes=("Square Sandbox card payment."),
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Square Payment Failed",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Square Sandbox Payment Complete",
            (
                f"{payment['payment_id']} "
                "was recorded successfully.\n\n"
                f"Amount: "
                f"{self._currency(square_payment.amount)}\n"
                f"Square Payment ID: "
                f"{square_payment.payment_id}"
            ),
        )

        self.load_repair(self.ticket_id)
    def _update_payment_buttons(
        self,
    ) -> None:
        if self.ticket_id is None:
            self.cash_payment_button.setEnabled(False)
            self.square_payment_button.setEnabled(False)
            return

        summary = self.payment_service.payment_summary(self.ticket_id)

        balance_due = float(
            summary.get(
                "balance_due",
                0.0,
            )
            or 0.0
        )

        has_balance = balance_due > 0

        self.cash_payment_button.setEnabled(has_balance)

        self.square_payment_button.setEnabled(has_balance)

    # ---------------------------------------------------------
    # DIRECT LIFECYCLE ACTIONS
    # ---------------------------------------------------------

    def _mark_repair_complete(
        self,
    ) -> None:
        self._change_lifecycle_status(
            "Repair Complete",
            (
                "Mark this repair as Repair Complete?\n\n"
                "The completion timestamp will be recorded "
                "if it has not already been set."
            ),
        )

    def _mark_ready_for_pickup(
        self,
    ) -> None:
        self._change_lifecycle_status(
            "Ready for Pickup",
            (
                "Mark this repair as Ready for Pickup?\n\n"
                "The repair will appear in the "
                "Ready for Pickup workflow."
            ),
        )

    def _mark_picked_up(
        self,
    ) -> None:
        if self.ticket_id is None or self.current_repair is None:
            return

        payment_summary = self.payment_service.payment_summary(self.ticket_id)

        balance_due = float(
            payment_summary.get(
                "balance_due",
                0.0,
            )
            or 0.0
        )

        if balance_due > 0:
            QMessageBox.warning(
                self,
                "Outstanding Balance",
                (
                    "This repair cannot be marked "
                    "Picked Up while a balance remains.\n\n"
                    f"Balance Due: "
                    f"{self._currency(balance_due)}"
                ),
            )
            return

        repair = dict(self.current_repair)

        answer = QMessageBox.question(
            self,
            "Mark Repair Picked Up",
            (
                "Mark this repair as Picked Up?\n\n"
                "The pickup timestamp will be recorded "
                "and the repair will leave the open queue."
            ),
            (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No),
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        repair["repair_status"] = "Picked Up"

        try:
            self.service.update_repair(
                self.ticket_id,
                repair,
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Repair Update Failed",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Repair Updated",
            (f"{self.ticket_id} " "was marked Picked Up."),
        )

        self.load_repair(self.ticket_id)

    def _change_lifecycle_status(
        self,
        status: str,
        confirmation_text: str,
    ) -> None:
        if self.ticket_id is None or self.current_repair is None:
            return

        current_status = self._text(self.current_repair.get("repair_status"))

        if current_status == status:
            QMessageBox.information(
                self,
                "No Change Needed",
                (f"This repair is already " f"{status}."),
            )
            return

        answer = QMessageBox.question(
            self,
            status,
            confirmation_text,
            (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No),
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        values = dict(self.current_repair)

        values["repair_status"] = status

        try:
            self.service.update_repair(
                self.ticket_id,
                values,
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Repair Update Failed",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Repair Updated",
            (f"{self.ticket_id} " f"was marked {status}."),
        )

        self.load_repair(self.ticket_id)

    def _update_lifecycle_buttons(
        self,
    ) -> None:
        if self.current_repair is None:
            self.complete_button.setEnabled(False)
            self.ready_button.setEnabled(False)
            self.picked_up_button.setEnabled(False)
            return

        status = self._text(self.current_repair.get("repair_status"))

        self.complete_button.setEnabled(
            status
            not in {
                "Repair Complete",
                "Ready for Pickup",
                "Completed",
                "Picked Up",
                "Cancelled",
            }
        )

        self.ready_button.setEnabled(
            status
            not in {
                "Ready for Pickup",
                "Picked Up",
                "Cancelled",
            }
        )

        self.picked_up_button.setEnabled(
            status
            not in {
                "Picked Up",
                "Cancelled",
            }
        )

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

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
            return "$0.00"

        text = str(value).strip()

        if not text:
            return "$0.00"

        try:
            amount = float(text)
        except ValueError:
            return text

        return f"${amount:,.2f}"

    @staticmethod
    def _format_datetime(
        value: object,
    ) -> str:
        if value is None:
            return ""

        text = str(value).strip()

        if not text:
            return ""

        try:
            parsed = datetime.fromisoformat(
                text.replace(
                    "Z",
                    "+00:00",
                )
            )

            return parsed.strftime("%Y-%m-%d %I:%M:%S %p")

        except ValueError:
            return text

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

    # ---------------------------------------------------------
    # CHECK-IN HISTORY
    # ---------------------------------------------------------

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
                self._format_datetime(
                    checkin.get(
                        "checkin_timestamp",
                        "",
                    )
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
                text = str(value or "")

                item = QTableWidgetItem(text)

                if text:
                    item.setToolTip(text)

                self.checkins_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    # ---------------------------------------------------------
    # REPAIR EVENT HISTORY
    # ---------------------------------------------------------

    def _load_events(self) -> None:
        self._clear_event_widgets()

        if self.ticket_id is None:
            self.current_events = []
            self.event_count.setText("0 events")
            return

        events = self.service.list_repair_events(self.ticket_id)

        self.current_events = events

        count = len(events)

        self.event_count.setText("1 event" if count == 1 else f"{count} events")

        if not events:
            empty = QLabel("No repair events have been recorded.")
            empty.setObjectName("mutedText")
            empty.setWordWrap(True)

            self.events_layout.addWidget(empty)
            return

        for event in events:
            card = self._build_event_card(event)

            self.events_layout.addWidget(card)

    def _clear_event_widgets(
        self,
    ) -> None:
        while self.events_layout.count():
            item = self.events_layout.takeAt(0)

            if item is None:
                continue

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def _build_event_card(
        self,
        event: dict[str, Any],
    ) -> QFrame:
        card = QFrame()

        card.setFrameShape(QFrame.Shape.StyledPanel)

        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #D7DEE8;
                border-radius: 8px;
            }
            """)

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            16,
            13,
            16,
            13,
        )

        layout.setSpacing(5)

        event_id = self._text(event.get("event_id"))

        created_at = self._format_datetime(event.get("created_at"))

        event_type = self._event_display_name(self._text(event.get("event_type")))

        old_value = self._text(event.get("old_value"))

        new_value = self._text(event.get("new_value"))

        created_by = self._text(event.get("created_by"))

        notes = self._text(event.get("notes"))

        top_line = QLabel(
            created_at if not event_id else (f"{created_at}    " f"{event_id}")
        )

        top_line.setObjectName("mutedText")

        top_line.setWordWrap(True)

        layout.addWidget(top_line)

        title_line = QLabel(event_type)

        title_font = QFont(title_line.font())

        title_font.setBold(True)

        title_line.setFont(title_font)

        title_line.setWordWrap(True)

        layout.addWidget(title_line)

        transition = self._event_transition_text(
            old_value,
            new_value,
        )

        if transition:
            transition_label = QLabel(transition)
            transition_label.setWordWrap(True)
            layout.addWidget(transition_label)

        if created_by:
            by_label = QLabel(f"By: {created_by}")
            by_label.setObjectName("mutedText")
            by_label.setWordWrap(True)
            layout.addWidget(by_label)

        if notes:
            notes_label = QLabel(notes)
            notes_label.setWordWrap(True)
            notes_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            layout.addWidget(notes_label)

        return card

    @staticmethod
    def _event_display_name(
        event_type: str,
    ) -> str:
        names = {
            "repair_created": "Repair Created",
            "repair_status_changed": "Status Changed",
            "checkin_created": "Check-In Created",
            "repair_completed": "Repair Completed",
            "repair_ready_for_pickup": "Ready for Pickup",
            "repair_picked_up": "Repair Picked Up",
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
    def _event_transition_text(
        old_value: str,
        new_value: str,
    ) -> str:
        if old_value and new_value:
            return f"{old_value} → " f"{new_value}"

        if new_value:
            return new_value

        if old_value:
            return old_value

        return ""

    # ---------------------------------------------------------
    # PRINTING
    # ---------------------------------------------------------

    def _print_repair_history(
        self,
    ) -> None:
        if self.ticket_id is None or self.current_repair is None:
            QMessageBox.information(
                self,
                "No Repair Selected",
                "Select a repair before printing.",
            )
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)

        printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))

        printer.setPageOrientation(QPageLayout.Orientation.Portrait)

        dialog = QPrintDialog(
            printer,
            self,
        )

        dialog.setWindowTitle(f"Print Repair History - " f"{self.ticket_id}")

        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return

        document = QTextDocument()

        document.setHtml(self._build_print_html())

        document.print_(printer)

    def _build_print_html(
        self,
    ) -> str:
        repair = self.current_repair or {}

        customer_name = self._customer_name(repair)

        device_name = self._device_name(repair)

        payment_summary: dict[str, Any] = {}

        if self.ticket_id is not None:
            payment_summary = self.payment_service.payment_summary(self.ticket_id)

        html = [
            """
            <html>
            <head>
            <style>
                body {
                    font-family: Aptos, Arial, sans-serif;
                    font-size: 10pt;
                    color: #111827;
                }

                h1 {
                    font-size: 18pt;
                    color: #081630;
                    margin-bottom: 4px;
                }

                h2 {
                    font-size: 12pt;
                    color: #081630;
                    margin-top: 18px;
                    margin-bottom: 6px;
                }

                .subtitle {
                    color: #5F6B7A;
                    margin-bottom: 14px;
                }

                .summary {
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 16px;
                }

                .summary td {
                    padding: 4px 6px;
                    vertical-align: top;
                    border-bottom: 1px solid #E4E9F0;
                }

                .label {
                    font-weight: bold;
                    width: 135px;
                }

                .event {
                    border-top: 1px solid #CBD5E1;
                    padding-top: 8px;
                    margin-top: 10px;
                    page-break-inside: avoid;
                }

                .event-title {
                    font-weight: bold;
                    color: #081630;
                }

                .muted {
                    color: #5F6B7A;
                }

                .notes {
                    margin-top: 4px;
                }
            </style>
            </head>
            <body>
            """,
            (
                f"<h1>Nocturnix Repair History</h1>"
                f"<div class='subtitle'>"
                f"{self._html(self.ticket_id or '')}"
                f" — "
                f"{self._html(customer_name)}"
                f" — "
                f"{self._html(device_name)}"
                f"</div>"
            ),
            "<table class='summary'>",
        ]

        summary_rows = [
            (
                "Repair ID",
                self.ticket_id or "",
            ),
            (
                "Status",
                self._text(repair.get("repair_status")),
            ),
            (
                "Customer",
                customer_name,
            ),
            (
                "Device",
                device_name,
            ),
            (
                "Serial",
                self._text(repair.get("serial_number")),
            ),
            (
                "Technician",
                self._text(repair.get("technician")),
            ),
            (
                "Final Cost",
                self._currency(payment_summary.get("final_cost")),
            ),
            (
                "Amount Paid",
                self._currency(payment_summary.get("amount_paid")),
            ),
            (
                "Balance Due",
                self._currency(payment_summary.get("balance_due")),
            ),
            (
                "Payment Status",
                self._text(payment_summary.get("payment_status")),
            ),
        ]

        for label, value in summary_rows:
            html.append(

                    "<tr>"
                    f"<td class='label'>"
                    f"{self._html(label)}"
                    "</td>"
                    f"<td>"
                    f"{self._html(value)}"
                    "</td>"
                    "</tr>"

            )

        html.append("</table>")

        html.append("<h2>Payment History</h2>")

        if not self.current_payments:
            html.append("<p>No payments recorded.</p>")

        for payment in self.current_payments:
            html.append("<div class='event'>")

            html.append(

                    f"<div class='event-title'>"
                    f"{self._html(payment.get('payment_id', ''))}"
                    f" — "
                    f"{self._html(payment.get('payment_method', ''))}"
                    f" — "
                    f"{self._html(self._currency(payment.get('amount')))}"
                    f"</div>"

            )

            html.append(

                    f"<div class='muted'>"
                    f"{self._html(self._format_datetime(payment.get('payment_timestamp')))}"
                    f" — "
                    f"{self._html(payment.get('payment_status', ''))}"
                    f"</div>"

            )

            square_payment_id = self._text(payment.get("square_payment_id"))

            if square_payment_id:
                html.append(

                        f"<div>"
                        f"Square Payment ID: "
                        f"{self._html(square_payment_id)}"
                        f"</div>"

                )

            html.append("</div>")

        html.append("<h2>Repair Event History</h2>")

        if not self.current_events:
            html.append("<p>No repair events recorded.</p>")

        for event in self.current_events:
            event_id = self._text(event.get("event_id"))

            date_text = self._format_datetime(event.get("created_at"))

            event_name = self._event_display_name(self._text(event.get("event_type")))

            old_value = self._text(event.get("old_value"))

            new_value = self._text(event.get("new_value"))

            created_by = self._text(event.get("created_by"))

            notes = self._text(event.get("notes"))

            transition = self._event_transition_text(
                old_value,
                new_value,
            )

            html.append("<div class='event'>")

            html.append(

                    f"<div class='muted'>"
                    f"{self._html(date_text)}"
                    f" &nbsp;&nbsp; "
                    f"{self._html(event_id)}"
                    f"</div>"

            )

            html.append(
                f"<div class='event-title'>" f"{self._html(event_name)}" f"</div>"
            )

            if transition:
                html.append(f"<div>" f"{self._html(transition)}" f"</div>")

            if created_by:
                html.append(

                        f"<div class='muted'>"
                        f"By: "
                        f"{self._html(created_by)}"
                        f"</div>"

                )

            if notes:
                html.append(f"<div class='notes'>" f"{self._html(notes)}" f"</div>")

            html.append("</div>")

        html.append("</body></html>")

        return "".join(html)

    @staticmethod
    def _html(
        value: object,
    ) -> str:
        text = str(value or "")

        return (
            text.replace(
                "&",
                "&amp;",
            )
            .replace(
                "<",
                "&lt;",
            )
            .replace(
                ">",
                "&gt;",
            )
            .replace(
                '"',
                "&quot;",
            )
            .replace(
                "\n",
                "<br>",
            )
        )

    # ---------------------------------------------------------
    # BUTTON ACTIONS
    # ---------------------------------------------------------

    def _edit_clicked(
        self,
    ) -> None:
        if self.ticket_id is None:
            return

        self.on_edit(self.ticket_id)

    def _checkin_clicked(
        self,
    ) -> None:
        if self.ticket_id is None:
            return

        self.on_checkin(self.ticket_id)

    def _customer_clicked(
        self,
    ) -> None:
        if self.customer_id is None:
            return

        self.on_customer(self.customer_id)

    def _device_clicked(
        self,
    ) -> None:
        if self.customer_id is None or self.device_id is None:
            return

        self.on_device(
            self.customer_id,
            self.device_id,
        )
