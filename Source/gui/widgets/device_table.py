from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

import pandas as pd


class DeviceTable(QTableWidget):

    def __init__(self):

        super().__init__()

        self.setup_table()

    # ======================================================

    def setup_table(self):

        self.setColumnCount(6)

        self.setHorizontalHeaderLabels(
            [
                "Manufacturer",
                "Family",
                "Device",
                "Model",
                "Year",
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

    # ======================================================

    def load_devices(self, dataframe):

        self.setSortingEnabled(False)

        self.clearContents()

        self.setRowCount(len(dataframe))

        for row, (_, device) in enumerate(dataframe.iterrows()):

            manufacturer = device.get("Manufacturer", "")
            family = device.get("Device Family", "")
            name = device.get("Device Model", "")
            model = device.get("Model Number", "")
            year = device.get("Release Year", "")
            active = device.get("Active", True)

            manufacturer = "" if pd.isna(manufacturer) else str(manufacturer)
            family = "" if pd.isna(family) else str(family)
            name = "" if pd.isna(name) else str(name)
            model = "" if pd.isna(model) else str(model)
            if pd.isna(year):

                year = ""

            else:

                year = str(int(year))

            if pd.isna(active):
                active = True

            active_text = "✔ Active" if bool(active) else "✖ Inactive"

            self.setItem(row, 0, QTableWidgetItem(manufacturer))

            self.setItem(row, 1, QTableWidgetItem(family))

            self.setItem(row, 2, QTableWidgetItem(name))

            self.setItem(row, 3, QTableWidgetItem(model))

            self.setItem(row, 4, QTableWidgetItem(year))

            self.setItem(row, 5, QTableWidgetItem(active_text))

        self.setSortingEnabled(True)

    # ======================================================

    def selected_device(self):

        row = self.currentRow()

        if row < 0:
            return None

        item = self.item(row, 2)

        if item is None:
            return None

        return item.text()
