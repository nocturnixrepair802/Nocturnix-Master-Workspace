from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
)

from gui.pages.base_page import BasePage
from gui.widgets.customer_table import CustomerTable
from gui.dialogs.customer_dialog import CustomerDialog
from gui.dialogs.customer_details_dialog import CustomerDetailsDialog
from gui.services.customer_gui_service import CustomerGuiService


class CustomerPage(BasePage):

    def __init__(self, application):

        super().__init__()

        self.application = application

        self.service = CustomerGuiService(application)

        self.current_customers = None

        self.build_page()

        self.load_data()

    # ==========================================================

    def build_page(self):

        title = QLabel("Customer Management")

        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
            padding:10px;
        """)

        self.layout.addWidget(title)

        # ------------------------------------------------------

        search_layout = QHBoxLayout()

        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText("Search customers...")

        search_layout.addWidget(self.search_box)

        self.layout.addLayout(search_layout)

        # ------------------------------------------------------

        toolbar = QHBoxLayout()

        self.add_button = QPushButton("➕ Add")
        self.edit_button = QPushButton("✏ Edit")
        self.delete_button = QPushButton("🗑 Delete")
        self.view_button = QPushButton("👁 View")
        self.devices_button = QPushButton("📱 Devices")
        self.refresh_button = QPushButton("🔄 Refresh")

        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.delete_button)
        toolbar.addWidget(self.view_button)
        toolbar.addWidget(self.devices_button)

        toolbar.addStretch()

        toolbar.addWidget(self.refresh_button)

        self.layout.addLayout(toolbar)

        # ------------------------------------------------------

        self.table = CustomerTable()

        self.layout.addWidget(self.table)

        # ------------------------------------------------------

        self.status = QLabel()

        self.layout.addWidget(self.status)

        # ======================================================
        # Signals
        # ======================================================

        self.search_box.textChanged.connect(self.search_customers)

        self.refresh_button.clicked.connect(self.load_data)

        self.add_button.clicked.connect(self.add_customer)

        self.edit_button.clicked.connect(self.edit_customer)

        self.view_button.clicked.connect(self.view_customer)

        self.delete_button.clicked.connect(self.delete_customer)

        self.table.doubleClicked.connect(self.edit_customer)

    # ==========================================================

    def load_data(self):

        self.current_customers = self.service.all_customers()

        self.table.load_customers(self.current_customers)

        self.status.setText(f"{len(self.current_customers)} Customers")

    # ==========================================================

    def search_customers(self):

        text = self.search_box.text()

        self.current_customers = self.service.search_customers(text)

        self.table.load_customers(self.current_customers)

        self.status.setText(f"{len(self.current_customers)} Customers Found")

    # ==========================================================

    def selected_customer(self):

        row = self.table.currentRow()

        if row < 0:

            return None

        return self.current_customers.iloc[row]

    # ==========================================================

    def add_customer(self):

        dialog = CustomerDialog(self)

        if dialog.exec():

            customer = dialog.customer_data()

            self.service.add_customer(customer)

            self.load_data()

    # ==========================================================

    def edit_customer(self):

        customer = self.selected_customer()

        if customer is None:

            QMessageBox.information(self, "Customer", "Please select a customer.")

            return

        dialog = CustomerDialog(customer, self)

        if dialog.exec():

            data = dialog.customer_data()

            self.service.update_customer(customer["Customer ID"], data)

            self.load_data()

    # ==========================================================

    def delete_customer(self):

        customer = self.selected_customer()

        if customer is None:

            return

        result = QMessageBox.question(
            self,
            "Delete Customer",
            f"Delete {customer['First Name']} {customer['Last Name']}?",
        )

        if result == QMessageBox.Yes:

            self.service.delete_customer(customer["Customer ID"])

            self.load_data()

    # ==========================================================

    def view_customer(self):

        customer = self.selected_customer()

        if customer is None:

            return

        dialog = CustomerDetailsDialog(customer, self)

        dialog.exec()
