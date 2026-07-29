from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.device_catalog_page import DeviceCatalogPage
from app.pages import DashboardPage, PlaceholderPage, WorkbookImportPage
from app.service_catalog_page import ServiceCatalogPage
from core.database import Database

class MainWindow(QMainWindow):
    def __init__(self, database: Database) -> None:
        super().__init__()

        self.setWindowTitle("Nocturnix Core Desktop v0.2")
        self.setMinimumSize(QSize(1180, 720))

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.setFixedWidth(230)

        self.stack = QStackedWidget()

        dashboard = DashboardPage(database)
        devices = DeviceCatalogPage(database)
        services = ServiceCatalogPage(database)

        importer = WorkbookImportPage(
            database,
            dashboard,
            [
                devices.reload,
                services.refresh,
            ],
        )

        pages = [
            ("Dashboard", dashboard),
            ("Workbook Import", importer),
            ("Device Catalog", devices),
            ("Service Catalog", services),
            (
                "Pricing Review",
                PlaceholderPage(
                    "Pricing Review",
                    "Next: approval controls, margin review, and publish eligibility.",
                ),
            ),
            (
                "Integrations",
                PlaceholderPage(
                    "Integrations",
                    "Next: Website JSON export and Square Sandbox staging.",
                ),
            ),
            (
                "Settings",
                PlaceholderPage(
                    "Settings",
                    "Credentials will be read from environment variables and never stored in Git.",
                ),
            ),
        ]

        for label, page in pages:
            self.navigation.addItem(QListWidgetItem(label))
            self.stack.addWidget(page)

        self.navigation.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.navigation.setCurrentRow(0)

        layout.addWidget(self.navigation)
        layout.addWidget(self.stack, 1)

        self.setCentralWidget(container)
