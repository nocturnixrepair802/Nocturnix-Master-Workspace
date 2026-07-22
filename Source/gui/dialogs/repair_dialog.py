from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)


class RepairDialog(QDialog):

    def __init__(self, gui_service, parent=None):

        super().__init__(parent)

        self.gui_service = gui_service

        self.device_data = {}

        self.setWindowTitle("Repair Ticket")

        self.resize(500, 450)

        self.build_ui()

        self.load_data()

        self.customer.currentIndexChanged.connect(self.load_devices)

        self.device.currentIndexChanged.connect(self.load_services)

    # ======================================================
    # Load Data
    # =====================================================

    def load_data(self):

        customers = self.gui_service.customers_list()

        self.customer.clear()

        self.customer.addItem("-- Select Customer --")

        self.customer_data = {}

        for _, row in customers.iterrows():

            customer_id = row["Customer ID"]

            name = f"{row['First Name']} {row['Last Name']}"

            self.customer.addItem(name)

            self.customer_data[name] = customer_id

    # ======================================================
    # Load Devices
    # ======================================================

    def load_devices(self):

        self.device.clear()

        self.device_data = {}

        customer_id = self.selected_customer_id()

        if customer_id is None:

            return

        devices = self.gui_service.devices_list(customer_id)

        self.device.addItem("-- Select Device --")

        for _, row in devices.iterrows():

            device_name = row["Device Model"]

            device_id = row["Device ID"]

            self.device.addItem(device_name)

            self.device_data[device_name] = device_id

    # ======================================================
    # Load Services
    # ======================================================

    def load_services(self):

        self.service.clear()

        device_id = self.selected_device_id()

        if device_id is None:

            return

        services = self.gui_service.compatible_services(device_id)

        self.service.addItem("-- Select Service --")

        self.service.addItems(services)

    # ======================================================
    # Selected Customer
    # ======================================================

    def selected_customer_id(self):

        name = self.customer.currentText()

        return self.customer_data.get(name)

    # ======================================================
    # Selected Device
    # ======================================================

    def selected_device_id(self):

        device = self.device.currentText()

        return self.device_data.get(device)

    # ======================================================
    # UI
    # ======================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.ticket_id = QLineEdit()

        self.customer = QComboBox()

        self.device = QComboBox()

        self.service = QComboBox()

        self.status = QComboBox()

        self.status.addItems(
            [
                "Open",
                "In Progress",
                "Waiting Parts",
                "Completed",
                "Picked Up",
                "Cancelled",
            ]
        )

        self.technician = QLineEdit()

        self.problem = QTextEdit()

        self.problem.setMinimumHeight(100)

        form.addRow("Ticket ID", self.ticket_id)

        form.addRow("Customer", self.customer)

        form.addRow("Device", self.device)

        form.addRow("Service", self.service)

        form.addRow("Status", self.status)

        form.addRow("Technician", self.technician)

        form.addRow("Problem", self.problem)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept)

        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    # ======================================================
    # Data
    # ======================================================

    def data(self):

        return {
            "Ticket ID": self.ticket_id.text(),
            "Customer ID": self.selected_customer_id(),
            "Device": self.device.currentText(),
            "Repair Status": self.status.currentText(),
            "Technician": self.technician.text(),
            "Problem Description": self.problem.toPlainText(),
        }
