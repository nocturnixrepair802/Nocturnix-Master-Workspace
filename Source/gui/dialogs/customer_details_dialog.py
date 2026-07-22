from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class CustomerDetailsDialog(QDialog):

    def __init__(self, customer, parent=None):

        super().__init__(parent)

        self.customer = customer

        self.setWindowTitle("Customer Details")

        self.resize(900, 700)

        self.build_ui()

    def build_ui(self):

        layout = QVBoxLayout(self)

        title = QLabel(f"{self.customer['First Name']} {self.customer['Last Name']}")

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
            padding:15px;
        """)

        layout.addWidget(title)

        info = QGroupBox("Customer Information")

        form = QFormLayout()

        form.addRow("Customer ID", QLabel(str(self.customer["Customer ID"])))
        form.addRow("Customer Type", QLabel(str(self.customer["Customer Type"])))
        form.addRow("Business", QLabel(str(self.customer["Business Name"])))
        form.addRow("Email", QLabel(str(self.customer["Email"])))
        form.addRow("Mobile", QLabel(str(self.customer["Mobile Phone"])))
        form.addRow(
            "Preferred Contact", QLabel(str(self.customer["Preferred Contact"]))
        )

        info.setLayout(form)

        layout.addWidget(info)

        buttons = QHBoxLayout()

        buttons.addWidget(QPushButton("✏ Edit"))
        buttons.addWidget(QPushButton("🗑 Delete"))
        buttons.addWidget(QPushButton("📱 Devices"))
        buttons.addWidget(QPushButton("🔧 New Repair"))
        buttons.addWidget(QPushButton("🧾 Invoices"))

        buttons.addStretch()

        close = QPushButton("Close")

        close.clicked.connect(self.close)

        buttons.addWidget(close)

        layout.addLayout(buttons)
