from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop.services.repair_service import RepairService

REPAIR_STATUSES = [
    "New Intake",
    "Awaiting Diagnosis",
    "Diagnosing",
    "Awaiting Approval",
    "Approved",
    "In Repair",
    "Awaiting Parts",
    "Repair Complete",
    "Ready for Pickup",
    "Completed",
    "Picked Up",
    "Cancelled",
]

PRIORITIES = [
    "Low",
    "Normal",
    "High",
    "Urgent",
]


class RepairDialog(QDialog):
    def __init__(
        self,
        service: RepairService,
        customer_id: str,
        device_id: str,
        ticket_id: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.service = service
        self.customer_id = customer_id
        self.device_id = device_id
        self.ticket_id = ticket_id

        self.repair: dict[str, Any] | None = None

        if ticket_id is not None:
            repair = self.service.get_repair(ticket_id)

            if repair is None:
                raise ValueError(f"Repair not found: {ticket_id}")

            self.repair = repair

        self.setWindowTitle(
            "New Repair" if ticket_id is None else f"Edit Repair - {ticket_id}"
        )

        self.resize(640, 720)

        self._build_ui()
        self._load_repair()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        heading = QLabel(
            "New Repair" if self.ticket_id is None else f"Repair {self.ticket_id}"
        )
        heading.setObjectName("pageTitle")

        layout.addWidget(heading)

        form = QFormLayout()

        self.repair_status = QComboBox()
        self.repair_status.addItems(REPAIR_STATUSES)

        self.technician = QLineEdit("Ryan Brown")

        self.priority = QComboBox()
        self.priority.addItems(PRIORITIES)
        self.priority.setCurrentText("Normal")

        self.due_date = QLineEdit()
        self.due_date.setPlaceholderText("YYYY-MM-DD")

        self.problem_description = QTextEdit()
        self.problem_description.setFixedHeight(110)

        self.diagnosis = QTextEdit()
        self.diagnosis.setFixedHeight(90)

        self.estimated_cost = QLineEdit()
        self.estimated_cost.setPlaceholderText("0.00")

        self.final_cost = QLineEdit()
        self.final_cost.setPlaceholderText("0.00")

        self.warranty = QCheckBox()

        self.notes = QTextEdit()
        self.notes.setFixedHeight(100)

        form.addRow(
            "Status",
            self.repair_status,
        )
        form.addRow(
            "Technician",
            self.technician,
        )
        form.addRow(
            "Priority",
            self.priority,
        )
        form.addRow(
            "Due Date",
            self.due_date,
        )
        form.addRow(
            "Problem Description",
            self.problem_description,
        )
        form.addRow(
            "Diagnosis",
            self.diagnosis,
        )
        form.addRow(
            "Estimated Cost",
            self.estimated_cost,
        )
        form.addRow(
            "Final Cost",
            self.final_cost,
        )
        form.addRow(
            "Warranty Repair",
            self.warranty,
        )
        form.addRow(
            "Notes",
            self.notes,
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def _load_repair(self) -> None:
        repair = self.repair

        if repair is None:
            return

        self.repair_status.setCurrentText(str(repair["repair_status"]))

        self.technician.setText(str(repair["technician"]))

        self.priority.setCurrentText(str(repair["priority"]))

        self.due_date.setText(str(repair["due_date"] or ""))

        self.problem_description.setPlainText(str(repair["problem_description"] or ""))

        self.diagnosis.setPlainText(str(repair["diagnosis"] or ""))

        self.estimated_cost.setText(
            "" if repair["estimated_cost"] is None else str(repair["estimated_cost"])
        )

        self.final_cost.setText(
            "" if repair["final_cost"] is None else str(repair["final_cost"])
        )

        self.warranty.setChecked(bool(repair["warranty"]))

        self.notes.setPlainText(str(repair["notes"] or ""))

    def _values(self) -> dict[str, Any]:
        return {
            "repair_status": self.repair_status.currentText(),
            "technician": self.technician.text(),
            "priority": self.priority.currentText(),
            "due_date": self.due_date.text(),
            "problem_description": self.problem_description.toPlainText(),
            "diagnosis": self.diagnosis.toPlainText(),
            "estimated_cost": self.estimated_cost.text(),
            "final_cost": self.final_cost.text(),
            "warranty": self.warranty.isChecked(),
            "notes": self.notes.toPlainText(),
        }

    def _save(self) -> None:
        try:
            if self.ticket_id is None:
                repair = self.service.create_repair(
                    customer_id=self.customer_id,
                    device_id=self.device_id,
                    values=self._values(),
                )

                self.ticket_id = str(repair["ticket_id"])
            else:
                self.service.update_repair(
                    self.ticket_id,
                    self._values(),
                )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Repair Save Failed",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Repair Saved",
            f"{self.ticket_id} was saved successfully.",
        )

        self.accept()


class NewRepairDialog(RepairDialog):
    def __init__(
        self,
        service: RepairService,
        customer_id: str,
        device_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            service=service,
            customer_id=customer_id,
            device_id=device_id,
            parent=parent,
        )


class EditRepairDialog(RepairDialog):
    def __init__(
        self,
        service: RepairService,
        ticket_id: str,
        parent: QWidget | None = None,
    ) -> None:
        repair = service.get_repair(ticket_id)

        if repair is None:
            raise ValueError(f"Repair not found: {ticket_id}")

        super().__init__(
            service=service,
            customer_id=str(repair["customer_id"]),
            device_id=str(repair["device_id"]),
            ticket_id=ticket_id,
            parent=parent,
        )
