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
from gui.pages.device_page import DevicePage


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.application = Application()

        self.setWindowTitle("Nocturnix Repair Platform")

        self.resize(1600, 900)
        self.setMinimumSize(1200, 800)
        self.showMaximized()

        self.build_menu()
        self.build_statusbar()
        self.build_ui()

    # ==========================================================
    # Menu
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
    # UI
    # ==========================================================

    def build_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)

        # ------------------------------------------------------
        # Navigation
        # ------------------------------------------------------

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

        # ------------------------------------------------------
        # Content
        # ------------------------------------------------------

        content = QFrame()

        content_layout = QVBoxLayout(content)

        self.page_stack = QStackedWidget()

        # ------------------------------------------------------
        # Pages
        # ------------------------------------------------------

        self.dashboard_page = DashboardPage()

        self.customer_page = CustomerPage(self.application)

        self.device_page = DevicePage(self.application)

        # ------------------------------------------------------
        # Load Data
        # ------------------------------------------------------

        self.customer_page.load_data()

        self.device_page.load_data()

        # ------------------------------------------------------
        # Page Stack
        # ------------------------------------------------------

        self.page_stack.addWidget(self.dashboard_page)

        self.page_stack.addWidget(self.customer_page)

        self.page_stack.addWidget(self.device_page)

        content_layout.addWidget(self.page_stack)

        # ------------------------------------------------------

        main_layout.addWidget(self.navigation)

        main_layout.addWidget(content)

        self.navigation.setCurrentRow(0)

    # ==========================================================
    # Navigation
    # ==========================================================

    def change_page(self, index):

        if index < self.page_stack.count():

            self.page_stack.setCurrentIndex(index)


# ==========================================================
# Entry Point
# ==========================================================


def main():

    app = QApplication(sys.argv)

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":

    main()
