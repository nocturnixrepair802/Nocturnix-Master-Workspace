from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)

from gui.services.device_catalog_service import DeviceCatalogService


class DeviceDialog(QDialog):

    def __init__(self, application, parent=None):

        super().__init__(parent)

        self.catalog = DeviceCatalogService(application)

        self.setWindowTitle("Customer Device")

        self.resize(700, 700)

        self.build_ui()

        self.load_manufacturers()

    # ==========================================================
    # UI
    # ==========================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.manufacturer = QComboBox()

        self.family = QComboBox()

        self.device = QComboBox()

        self.color = QLineEdit()

        self.storage = QLineEdit()

        self.serial = QLineEdit()

        self.imei = QLineEdit()

        self.passcode = QLineEdit()

        self.condition = QTextEdit()

        form.addRow("Manufacturer", self.manufacturer)

        form.addRow("Device Family", self.family)

        form.addRow("Device", self.device)

        form.addRow("Color", self.color)

        form.addRow("Storage", self.storage)

        form.addRow("Serial Number", self.serial)

        form.addRow("IMEI", self.imei)

        form.addRow("Passcode", self.passcode)

        form.addRow("Condition", self.condition)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        buttons.accepted.connect(self.accept)

        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        # ----------------------------------

        self.manufacturer.currentTextChanged.connect(self.load_families)

        self.family.currentTextChanged.connect(self.load_devices)

    # ==========================================================
    # Manufacturers
    # ==========================================================

    def load_manufacturers(self):

        self.manufacturer.clear()

        self.manufacturer.addItems(self.catalog.manufacturers())

    # ==========================================================
    # Families
    # ==========================================================

    def load_families(self):

        manufacturer = self.manufacturer.currentText()

        self.family.clear()

        self.family.addItems(self.catalog.families(manufacturer))

    # ==========================================================
    # Devices
    # ==========================================================

    def load_devices(self):

        manufacturer = self.manufacturer.currentText()

        family = self.family.currentText()

        self.device.clear()

        self.device.addItems(self.catalog.devices(manufacturer, family))

    # ==========================================================
    # Return Data
    # ==========================================================

    def device_data(self):

        return {
            "Manufacturer": self.manufacturer.currentText(),
            "Device Family": self.family.currentText(),
            "Device": self.device.currentText(),
            "Color": self.color.text(),
            "Storage": self.storage.text(),
            "Serial Number": self.serial.text(),
            "IMEI": self.imei.text(),
            "Passcode": self.passcode.text(),
            "Condition": self.condition.toPlainText(),
        }
