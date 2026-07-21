from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QMessageBox,
)

from gui.pages.base_page import BasePage
from gui.widgets.device_table import DeviceTable
from gui.dialogs.device_dialog import DeviceDialog
from gui.services.device_catalog_service import DeviceCatalogService


class DevicePage(BasePage):

    def __init__(self, application):

        super().__init__()

        self.application = application

        self.catalog = DeviceCatalogService(application)

        self.current_devices = None

        self.build_page()

        self.load_data()

    # ==========================================================
    # UI
    # ==========================================================

    def build_page(self):

        title = QLabel("Device Catalog")

        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
            padding:10px;
        """)

        self.layout.addWidget(title)

        # ------------------------------------------------------

        search_layout = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search devices...")

        self.manufacturer = QComboBox()
        self.family = QComboBox()

        search_layout.addWidget(self.search)
        search_layout.addWidget(self.manufacturer)
        search_layout.addWidget(self.family)

        self.layout.addLayout(search_layout)

        # ------------------------------------------------------

        toolbar = QHBoxLayout()

        self.add_button = QPushButton("➕ Add")
        self.edit_button = QPushButton("✏ Edit")
        self.delete_button = QPushButton("🗑 Delete")
        self.view_button = QPushButton("👁 View")
        self.refresh_button = QPushButton("🔄 Refresh")

        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.delete_button)
        toolbar.addWidget(self.view_button)

        toolbar.addStretch()

        toolbar.addWidget(self.refresh_button)

        self.layout.addLayout(toolbar)

        # ------------------------------------------------------

        self.table = DeviceTable()

        self.layout.addWidget(self.table)

        # ------------------------------------------------------

        self.status = QLabel()

        self.layout.addWidget(self.status)

        # ------------------------------------------------------
        # Signals
        # ------------------------------------------------------

        self.refresh_button.clicked.connect(self.load_data)

        self.search.textChanged.connect(self.search_devices)

        self.manufacturer.currentTextChanged.connect(self.load_families)

        self.family.currentTextChanged.connect(self.filter_devices)

        # ------------------------------------------------------
        # Signals
        # ------------------------------------------------------

        self.refresh_button.clicked.connect(self.load_data)

        self.search.textChanged.connect(self.search_devices)

        self.manufacturer.currentTextChanged.connect(self.load_families)

        self.family.currentTextChanged.connect(self.filter_devices)

        self.add_button.clicked.connect(self.add_device)

        self.view_button.clicked.connect(self.view_device)

        self.edit_button.clicked.connect(self.edit_device)

        self.delete_button.clicked.connect(self.delete_device)

    # ==========================================================
    # Load
    # ==========================================================

    def load_data(self):

        self.current_devices = self.catalog.search("")

        self.table.load_devices(self.current_devices)

        self.manufacturer.blockSignals(True)

        self.manufacturer.clear()

        self.manufacturer.addItem("All Manufacturers")

        self.manufacturer.addItems(
            self.catalog.manufacturers()
        )

        self.manufacturer.setCurrentIndex(0)

        self.manufacturer.blockSignals(False)

        self.family.blockSignals(True)

        self.family.clear()

        self.family.addItem("All Families")

        self.family.setCurrentIndex(0)

        self.family.blockSignals(False)

        self.status.setText(
            f"{len(self.current_devices)} Devices"
        )

    # ==========================================================
    # Search
    # ==========================================================

    def search_devices(self):

        text = self.search.text()

        self.current_devices = self.catalog.search(text)

        self.table.load_devices(self.current_devices)

        self.status.setText(f"{len(self.current_devices)} Devices")

    # ==========================================================
    # Families
    # ==========================================================

    def load_families(self):

        manufacturer = self.manufacturer.currentText()

        self.family.clear()

        self.family.addItem("All Families")

        if manufacturer == "All Manufacturers":

            return

        self.family.addItems(self.catalog.families(manufacturer))

    # ==========================================================
    # Filter
    # ==========================================================

    def filter_devices(self):

        manufacturer = self.manufacturer.currentText()

        family = self.family.currentText()

        self.current_devices = self.catalog.search("")

        if manufacturer != "All Manufacturers":

            self.current_devices = self.current_devices[
                self.current_devices["Manufacturer"] == manufacturer
            ]

        if family != "All Families":

            self.current_devices = self.current_devices[
                self.current_devices["Device Family"] == family
            ]

        self.table.load_devices(self.current_devices)

        self.status.setText(f"{len(self.current_devices)} Devices")

    # ==========================================================
    # Add
    # ==========================================================

    def add_device(self):

        dialog = DeviceDialog(self.application, self)

        dialog.exec()

    # ==========================================================
    # View
    # ==========================================================

    def view_device(self):

        selected = self.table.selected_device()

        if selected is None:

            QMessageBox.information(
                self, "View Device", "Please select a device first."
            )

            return

        QMessageBox.information(self, "View Device", f"Selected Device:\n\n{selected}")

    # ==========================================================
    # Edit
    # ==========================================================

    def edit_device(self):

        selected = self.table.selected_device()

        if selected is None:

            QMessageBox.information(
                self, "Edit Device", "Please select a device first."
            )

            return

        QMessageBox.information(
            self, "Edit Device", f"Edit functionality coming next.\n\n{selected}"
        )

    # ==========================================================
    # Delete
    # ==========================================================

    def delete_device(self):

        selected = self.table.selected_device()

        if selected is None:

            QMessageBox.information(
                self, "Delete Device", "Please select a device first."
            )

            return

        QMessageBox.information(
            self, "Delete Device", f"Delete functionality coming next.\n\n{selected}"
        )
