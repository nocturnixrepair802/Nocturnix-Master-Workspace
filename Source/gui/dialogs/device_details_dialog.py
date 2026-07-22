from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
)


class DeviceDetailsDialog(QDialog):

    def __init__(
        self,
        application,
        device,
        repair_count=0,
        repairs=None,
        parent=None,
    ):

        super().__init__(parent)

        self.application = application
        self.device = device
        self.repair_count = repair_count
        self.repairs = repairs if repairs is not None else []

        self.setWindowTitle("Device Details")

        self.resize(900, 700)

        self.build_ui()

    # ==========================================================
    # UI
    # ==========================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        # ------------------------------------------------------
        # Title
        # ------------------------------------------------------

        title = QLabel("Device Details")

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
            padding:10px;
        """)

        layout.addWidget(title)

        # ------------------------------------------------------
        # Device Information
        # ------------------------------------------------------

        info_group = QGroupBox("Device Information")

        info_layout = QFormLayout(info_group)

        info_layout.addRow(
            "Device ID",
            QLabel(str(self.device.get("Device ID", ""))),
        )

        info_layout.addRow(
            "Manufacturer",
            QLabel(str(self.device.get("Manufacturer", ""))),
        )

        info_layout.addRow(
            "Device Family",
            QLabel(str(self.device.get("Device Family", ""))),
        )

        info_layout.addRow(
            "Device Model",
            QLabel(str(self.device.get("Device Model", ""))),
        )

        info_layout.addRow(
            "Model Number",
            QLabel(str(self.device.get("Model Number", ""))),
        )

        year = self.device.get("Release Year", "")

        try:
            if year != "":
                year = str(int(year))
        except Exception:
            pass

        info_layout.addRow(
            "Release Year",
            QLabel(str(year)),
        )

        layout.addWidget(info_group)

        # ------------------------------------------------------
        # Repair Information
        # ------------------------------------------------------

        repair_group = QGroupBox("Repair Information")

        repair_layout = QVBoxLayout(repair_group)

        repair_layout.addWidget(QLabel(f"Available Repair Guides: {self.repair_count}"))

        self.repair_list = QListWidget()

        self.repair_list.addItems(self.repairs)

        repair_layout.addWidget(self.repair_list)

        layout.addWidget(repair_group)

        # ------------------------------------------------------
        # Buttons
        # ------------------------------------------------------

        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Repair")

        self.edit_button = QPushButton("Edit")

        self.close_button = QPushButton("Close")

        self.close_button.clicked.connect(self.accept)

        button_layout.addStretch()

        button_layout.addWidget(self.start_button)

        button_layout.addWidget(self.edit_button)

        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)
