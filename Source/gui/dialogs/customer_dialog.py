from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)


class CustomerDialog(QDialog):

    def __init__(self, customer=None, parent=None):

        super().__init__(parent)

        self.customer = customer

        self.setWindowTitle("Customer")

        self.resize(650, 700)

        self.build_ui()

        if customer is not None:
            self.load_customer()

    # ==========================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.customer_type = QComboBox()
        self.customer_type.addItems(
            [
                "Residential",
                "Business",
            ]
        )

        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.business_name = QLineEdit()
        self.email = QLineEdit()
        self.mobile_phone = QLineEdit()
        self.home_phone = QLineEdit()
        self.work_phone = QLineEdit()
        self.preferred_contact = QComboBox()

        self.preferred_contact.addItems(
            [
                "Mobile Phone",
                "Home Phone",
                "Work Phone",
                "Email",
            ]
        )

        self.billing_address = QTextEdit()
        self.shipping_address = QTextEdit()
        self.notes = QTextEdit()

        form.addRow("Customer Type", self.customer_type)
        form.addRow("First Name", self.first_name)
        form.addRow("Last Name", self.last_name)
        form.addRow("Business Name", self.business_name)
        form.addRow("Email", self.email)
        form.addRow("Mobile Phone", self.mobile_phone)
        form.addRow("Home Phone", self.home_phone)
        form.addRow("Work Phone", self.work_phone)
        form.addRow("Preferred Contact", self.preferred_contact)
        form.addRow("Billing Address", self.billing_address)
        form.addRow("Shipping Address", self.shipping_address)
        form.addRow("Notes", self.notes)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    # ==========================================================

    def load_customer(self):

        customer = self.customer

        self.customer_type.setCurrentText(
            str(customer.get("Customer Type", "Residential"))
        )

        self.first_name.setText(str(customer.get("First Name", "")))

        self.last_name.setText(str(customer.get("Last Name", "")))

        self.business_name.setText(str(customer.get("Business Name", "")))

        self.email.setText(str(customer.get("Email", "")))

        self.mobile_phone.setText(str(customer.get("Mobile Phone", "")))

        self.home_phone.setText(str(customer.get("Home Phone", "")))

        self.work_phone.setText(str(customer.get("Work Phone", "")))

        self.preferred_contact.setCurrentText(
            str(customer.get("Preferred Contact", "Mobile Phone"))
        )

        self.billing_address.setPlainText(str(customer.get("Billing Address", "")))

        self.shipping_address.setPlainText(str(customer.get("Shipping Address", "")))

        self.notes.setPlainText(str(customer.get("Notes", "")))

    # ==========================================================

    def customer_data(self):

        return {
            "Customer Type": self.customer_type.currentText(),
            "First Name": self.first_name.text(),
            "Last Name": self.last_name.text(),
            "Business Name": self.business_name.text(),
            "Email": self.email.text(),
            "Mobile Phone": self.mobile_phone.text(),
            "Home Phone": self.home_phone.text(),
            "Work Phone": self.work_phone.text(),
            "Preferred Contact": self.preferred_contact.currentText(),
            "Billing Address": self.billing_address.toPlainText(),
            "Shipping Address": self.shipping_address.toPlainText(),
            "Notes": self.notes.toPlainText(),
        }
