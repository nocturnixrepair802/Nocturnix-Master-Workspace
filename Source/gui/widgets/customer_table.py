import pandas as pd
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class CustomerTable(QTableWidget):

    def __init__(self):

        super().__init__()

        self.setup_table()

    # ==========================================================

    def setup_table(self):

        self.setColumnCount(6)

        self.setHorizontalHeaderLabels(
            [
                "Customer ID",
                "Customer",
                "Phone",
                "Email",
                "Type",
                "Active",
            ]
        )

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.verticalHeader().setVisible(False)

        self.setAlternatingRowColors(True)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.setSelectionMode(QAbstractItemView.SingleSelection)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.setSortingEnabled(True)

    # ==========================================================

    def load_customers(self, dataframe):

        self.setSortingEnabled(False)

        self.clearContents()

        self.setRowCount(len(dataframe))

        for row, (_, customer) in enumerate(dataframe.iterrows()):

            # ---------------------------------------------
            # Handle missing values
            # ---------------------------------------------

            first = customer.get("First Name", "")
            last = customer.get("Last Name", "")
            business = customer.get("Business Name", "")
            phone = customer.get("Mobile Phone", "")
            email = customer.get("Email", "")
            customer_type = customer.get("Customer Type", "")
            active = customer.get("Active", True)

            first = "" if pd.isna(first) else str(first)
            last = "" if pd.isna(last) else str(last)
            business = "" if pd.isna(business) else str(business)
            phone = "" if pd.isna(phone) else str(phone)
            email = "" if pd.isna(email) else str(email)
            customer_type = "" if pd.isna(customer_type) else str(customer_type)

            if pd.isna(active):
                active = True

            # ---------------------------------------------
            # Display Name
            # ---------------------------------------------

            if business.strip():
                display_name = business
            else:
                display_name = f"{first} {last}".strip()

            active_text = "✔ Active" if bool(active) else "✖ Inactive"

            # ---------------------------------------------
            # Populate Table
            # ---------------------------------------------

            self.setItem(row, 0, QTableWidgetItem(str(customer["Customer ID"])))

            self.setItem(row, 1, QTableWidgetItem(display_name))

            self.setItem(row, 2, QTableWidgetItem(phone))

            self.setItem(row, 3, QTableWidgetItem(email))

            self.setItem(row, 4, QTableWidgetItem(customer_type))

            self.setItem(row, 5, QTableWidgetItem(active_text))

        self.setSortingEnabled(True)

    # ==========================================================

    def selected_customer_id(self):

        row = self.currentRow()

        if row < 0:
            return None

        item = self.item(row, 0)

        if item is None:
            return None

        return item.text()
