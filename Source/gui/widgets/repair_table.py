from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

import pandas as pd


class RepairTable(QTableWidget):

    def __init__(self):

        super().__init__()

        self.setup_table()

    # ======================================================

    def setup_table(self):

        self.setColumnCount(7)

        self.setHorizontalHeaderLabels(
            [
                "Ticket",
                "Customer",
                "Device",
                "Status",
                "Technician",
                "Date",
                "Total",
            ]
        )

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.verticalHeader().setVisible(False)

        self.setAlternatingRowColors(True)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.setSelectionMode(QAbstractItemView.SingleSelection)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.setSortingEnabled(True)

    # ======================================================

    def load_repairs(self, dataframe):

        self.setSortingEnabled(False)

        self.clearContents()

        self.setRowCount(len(dataframe))

        for row, (_, repair) in enumerate(dataframe.iterrows()):

            columns = [
                "Ticket ID",
                "Customer",
                "Device",
                "Status",
                "Technician",
                "Date Created",
                "Total",
            ]

            for col, field in enumerate(columns):

                value = repair.get(field, "")

                if pd.isna(value):

                    value = ""

                self.setItem(row, col, QTableWidgetItem(str(value)))

        self.setSortingEnabled(True)

    # ======================================================

    def selected_ticket(self):

        row = self.currentRow()

        if row < 0:

            return None

        item = self.item(row, 0)

        if item is None:

            return None

        return item.text()
