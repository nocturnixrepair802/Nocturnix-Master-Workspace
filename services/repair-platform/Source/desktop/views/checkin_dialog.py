from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
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


class NewCheckinDialog(QDialog):
    def __init__(
        self,
        service: RepairService,
        repair_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.service = service
        self.repair_id = repair_id

        repair = self.service.get_repair(repair_id)

        if repair is None:
            raise ValueError(f"Repair not found: {repair_id}")

        self.repair = repair

        self.setWindowTitle(f"New Check-In - {repair_id}")
        self.resize(650, 780)

        self._build_ui()

    @staticmethod
    def _yes_no_combo() -> QComboBox:
        combo = QComboBox()
        combo.addItems(
            [
                "",
                "Yes",
                "No",
                "Unknown",
            ]
        )
        return combo

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        heading = QLabel(f"Check-In for {self.repair_id}")
        heading.setObjectName("pageTitle")

        layout.addWidget(heading)

        form = QFormLayout()

        self.technician = QLineEdit(str(self.repair["technician"]))

        self.powers_on = self._yes_no_combo()

        self.battery_percentage = QLineEdit()
        self.battery_percentage.setPlaceholderText("0-100")

        self.screen_condition = QLineEdit()
        self.frame_condition = QLineEdit()
        self.back_glass_condition = QLineEdit()
        self.charging_port_condition = QLineEdit()
        self.camera_condition = QLineEdit()
        self.speaker_condition = QLineEdit()
        self.microphone_condition = QLineEdit()

        self.face_id_touch_id = QLineEdit()

        self.liquid_damage = self._yes_no_combo()

        self.existing_damage = QTextEdit()
        self.existing_damage.setFixedHeight(80)

        self.accessories_received = QTextEdit()
        self.accessories_received.setFixedHeight(70)

        self.passcode_available = self._yes_no_combo()

        self.device_passcode = QLineEdit()
        self.device_passcode.setEchoMode(QLineEdit.EchoMode.Password)

        self.intake_notes = QTextEdit()
        self.intake_notes.setFixedHeight(100)

        form.addRow(
            "Technician",
            self.technician,
        )
        form.addRow(
            "Powers On",
            self.powers_on,
        )
        form.addRow(
            "Battery %",
            self.battery_percentage,
        )
        form.addRow(
            "Screen Condition",
            self.screen_condition,
        )
        form.addRow(
            "Frame Condition",
            self.frame_condition,
        )
        form.addRow(
            "Back Glass Condition",
            self.back_glass_condition,
        )
        form.addRow(
            "Charging Port",
            self.charging_port_condition,
        )
        form.addRow(
            "Camera",
            self.camera_condition,
        )
        form.addRow(
            "Speaker",
            self.speaker_condition,
        )
        form.addRow(
            "Microphone",
            self.microphone_condition,
        )
        form.addRow(
            "Face ID / Touch ID",
            self.face_id_touch_id,
        )
        form.addRow(
            "Liquid Damage",
            self.liquid_damage,
        )
        form.addRow(
            "Existing Damage",
            self.existing_damage,
        )
        form.addRow(
            "Accessories Received",
            self.accessories_received,
        )
        form.addRow(
            "Passcode Available",
            self.passcode_available,
        )
        form.addRow(
            "Device Passcode",
            self.device_passcode,
        )
        form.addRow(
            "Intake Notes",
            self.intake_notes,
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def _values(self) -> dict[str, Any]:
        return {
            "technician": self.technician.text(),
            "powers_on": self.powers_on.currentText(),
            "battery_percentage": self.battery_percentage.text(),
            "screen_condition": self.screen_condition.text(),
            "frame_condition": self.frame_condition.text(),
            "back_glass_condition": self.back_glass_condition.text(),
            "charging_port_condition": self.charging_port_condition.text(),
            "camera_condition": self.camera_condition.text(),
            "speaker_condition": self.speaker_condition.text(),
            "microphone_condition": self.microphone_condition.text(),
            "face_id_touch_id": self.face_id_touch_id.text(),
            "liquid_damage": self.liquid_damage.currentText(),
            "existing_damage": self.existing_damage.toPlainText(),
            "accessories_received": self.accessories_received.toPlainText(),
            "device_passcode": self.device_passcode.text(),
            "passcode_available": self.passcode_available.currentText(),
            "intake_notes": self.intake_notes.toPlainText(),
        }

    def _save(self) -> None:
        try:
            checkin = self.service.create_checkin(
                self.repair_id,
                self._values(),
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Check-In Save Failed",
                str(exc),
            )
            return

        checkin_id = str(checkin["checkin_id"])

        QMessageBox.information(
            self,
            "Check-In Created",
            f"{checkin_id} was created successfully.",
        )

        self.accept()
