from PySide6.QtCore import Qt
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

        self.setColumnCount(5)

        self.setHorizontalHeaderLabels(
            [
                "Customer ID",
                "Customer Name",
                "Phone",
                "Email",
                "Type",
            ]
        )

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.verticalHeader().setVisible(False)

        self.setAlternatingRowColors(True)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.setSelectionMode(QAbstractItemView.SingleSelection)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.setSortingEnabled(True)

    # ==========================================================

    def load_customers(self, dataframe):

        self.setSortingEnabled(False)

        self.clearContents()

        self.setRowCount(len(dataframe))

        for row, (_, customer) in enumerate(dataframe.iterrows()):

            self.setItem(row, 0, QTableWidgetItem(str(customer["Customer ID"])))

            self.setItem(
                row,
                1,
                QTableWidgetItem(f'{customer["First Name"]} {customer["Last Name"]}'),
            )

            self.setItem(row, 2, QTableWidgetItem(str(customer["Mobile Phone"])))

            self.setItem(row, 3, QTableWidgetItem(str(customer["Email"])))

            self.setItem(row, 4, QTableWidgetItem(str(customer["Customer Type"])))

        self.setSortingEnabled(True)

    # ==========================================================

    def selected_customer_id(self):

        row = self.currentRow()

        if row < 0:

            return None

        return int(self.item(row, 0).text())
