from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel

from gui.pages.base_page import BasePage
from gui.widgets.stat_card import StatCard


class DashboardPage(BasePage):

    def __init__(self):

        super().__init__()

        main_layout = self.layout

        title = QLabel("Dashboard")

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title.setStyleSheet("""
            font-size:30px;
            font-weight:bold;
        """)

        main_layout.addWidget(title)

        cards = QGridLayout()

        cards.addWidget(
            StatCard("Customers", 10),
            0, 0
        )

        cards.addWidget(
            StatCard("Devices", 837),
            0, 1
        )

        cards.addWidget(
            StatCard("Services", 75),
            0, 2
        )

        cards.addWidget(
            StatCard("Open Repairs", 0),
            0, 3
        )

        main_layout.addLayout(cards)

        main_layout.addStretch()
