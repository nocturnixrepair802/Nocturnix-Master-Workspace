import sys

from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app import Application

from gui.pages.dashboard_page import DashboardPage
from gui.pages.customer_page import CustomerPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # ----------------------------------
        # Backend Application
        # ----------------------------------

        self.application = Application()

        # ----------------------------------
        # Window Configuration
        # ----------------------------------

        self.setWindowTitle("Nocturnix Repair Platform")

        self.resize(1600, 900)
        self.setMinimumSize(1200, 800)

        # Open Maximized
        self.showMaximized()

        # ----------------------------------
        # Build UI
        # ----------------------------------

        self.build_menu()
        self.build_statusbar()
        self.build_ui()

    # ==========================================================
    # Menu Bar
    # ==========================================================

    def build_menu(self):

        menu = self.menuBar()

        menu.addMenu("File")
        menu.addMenu("Customers")
        menu.addMenu("Devices")
        menu.addMenu("Repairs")
        menu.addMenu("Inventory")
        menu.addMenu("Reports")
        menu.addMenu("Administration")
        menu.addMenu("Help")

    # ==========================================================
    # Status Bar
    # ==========================================================

    def build_statusbar(self):

        status = QStatusBar()

        status.showMessage("Ready")

        self.setStatusBar(status)

    # ==========================================================
    # Main Interface
    # ==========================================================

    def build_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        main_layout = QHBoxLayout()

        central.setLayout(main_layout)

        # ----------------------------------
        # Navigation Panel
        # ----------------------------------

        self.navigation = QListWidget()

        self.navigation.setFixedWidth(220)

        self.navigation.addItems(
            [
                "🏠 Dashboard",
                "👤 Customers",
                "📱 Devices",
                "🔧 Repairs",
                "📦 Inventory",
                "📊 Reports",
                "⚙ Administration",
            ]
        )

        self.navigation.currentRowChanged.connect(self.change_page)

        # ----------------------------------
        # Content Area
        # ----------------------------------

        content = QFrame()

        content_layout = QVBoxLayout()

        content.setLayout(content_layout)

        # ----------------------------------
        # Page Stack
        # ----------------------------------

        self.page_stack = QStackedWidget()

        # Create Pages

        self.dashboard_page = DashboardPage()

        self.customer_page = CustomerPage(self.application)

        # Load Initial Data

        self.customer_page.load_data()

        # Add Pages

        self.page_stack.addWidget(self.dashboard_page)

        self.page_stack.addWidget(self.customer_page)

        # Add Page Stack

        content_layout.addWidget(self.page_stack)

        # ----------------------------------
        # Assemble Window
        # ----------------------------------

        main_layout.addWidget(self.navigation)

        main_layout.addWidget(content)

        # Dashboard on Startup

        self.navigation.setCurrentRow(0)

    # ==========================================================
    # Navigation
    # ==========================================================

    def change_page(self, index):

        if 0 <= index < self.page_stack.count():

            self.page_stack.setCurrentIndex(index)


# ==============================================================
# Application Entry Point
# ==============================================================


def main():

    app = QApplication(sys.argv)

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":

    main()
