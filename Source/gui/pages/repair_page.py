from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QHBoxLayout,
    QLineEdit,
    QComboBox,

)
import pandas as pd
from gui.pages.base_page import BasePage
from gui.widgets.repair_table import RepairTable
from gui.services.repair_gui_service import RepairGuiService
from gui.dialogs.repair_dialog import RepairDialog

class RepairPage(BasePage):

    def __init__(self, application):

        super().__init__()

        self.application = application

        self.repairs = RepairGuiService(application)

        self.current_repairs: pd.DataFrame = pd.DataFrame()

        self.build_page()

        self.load_data()

    # ==========================================================
    # UI
    # ==========================================================

    def build_page(self):

        # ------------------------------------------------------
        # Title
        # ------------------------------------------------------

        title = QLabel("Repair Management")

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
            padding:10px;
        """)

        self.layout.addWidget(title)

        # ------------------------------------------------------
        # Search / Filter
        # ------------------------------------------------------

        search_layout = QHBoxLayout()

        self.search = QLineEdit()

        self.search.setPlaceholderText("Search repairs...")

        self.status_filter = QComboBox()

        self.status_filter.addItems(
            [
                "All Repairs",
                "Open",
                "In Progress",
                "Waiting Parts",
                "Completed",
                "Picked Up",
                "Cancelled",
            ]
        )

        search_layout.addWidget(self.search)

        search_layout.addWidget(self.status_filter)

        self.layout.addLayout(search_layout)

        # ======================================================
        # Signals
        # ======================================================

        self.search.textChanged.connect(
            self.search_repairs
        )

        self.status_filter.currentIndexChanged.connect(
            self.filter_repairs
        )

        # ------------------------------------------------------
        # Toolbar
        # ------------------------------------------------------

        toolbar = QHBoxLayout()

        self.new_button = QPushButton("➕ New Repair")

        self.edit_button = QPushButton("✏ Edit")

        self.view_button = QPushButton("👁 View")

        self.delete_button = QPushButton("🗑 Delete")

        self.refresh_button = QPushButton("🔄 Refresh")

        toolbar.addWidget(self.new_button)

        toolbar.addWidget(self.edit_button)

        toolbar.addWidget(self.view_button)

        toolbar.addWidget(self.delete_button)

        toolbar.addStretch()

        toolbar.addWidget(self.refresh_button)

        self.layout.addLayout(toolbar)

        # ======================================================
        # Button Signals
        # ======================================================

        self.new_button.clicked.connect(self.add_repair)

        self.refresh_button.clicked.connect(self.load_data)

        # ------------------------------------------------------
        # Table
        # ------------------------------------------------------
        # ------------------------------------------------------
        # Table
        # ------------------------------------------------------

        # ------------------------------------------------------
        # Table
        # ------------------------------------------------------

        self.table = RepairTable()

        self.layout.addWidget(self.table)

        # ------------------------------------------------------
        # Status
        # ------------------------------------------------------

        self.status = QLabel("0 Repairs")

        self.layout.addWidget(self.status)

    # ==========================================================
    # Load Data
    # ==========================================================

    def load_data(self):

        self.current_repairs = self.repairs.search("")

        self.table.load_repairs(self.current_repairs)

        self.status.setText(f"{len(self.current_repairs.index)} Repairs")

    # ======================================================
    # Search
    # ======================================================

    def search_repairs(self):

        text = self.search.text()

        self.current_repairs = self.repairs.search(text)

        self.filter_repairs()

    # ======================================================
    # Filter
    # ======================================================


    def filter_repairs(self):

        dataframe: pd.DataFrame = self.current_repairs.copy()

        status = self.status_filter.currentText()

        if status != "All Repairs":

            dataframe = dataframe[dataframe["Repair Status"] == status]

        self.table.load_repairs(dataframe)

        self.status.setText(f"{len(dataframe.index)} Repairs")

        
    # ======================================================
    # Add Repair
    # ======================================================

    def add_repair(self):

        dialog = RepairDialog(
            self.repairs,
            self
        )
