from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.widgets.widgets import MetricCard
from core.database import Database
from core.import_service import ImportService


class DashboardPage(QWidget):
    def __init__(self, database: Database) -> None:
        super().__init__(); self.database = database
        layout = QVBoxLayout(self)
        heading = QLabel("Dashboard"); heading.setObjectName("pageHeading"); layout.addWidget(heading)
        metrics = QGridLayout()
        self.devices = MetricCard("Devices"); self.services = MetricCard("Services")
        self.pricing = MetricCard("Pricing records"); self.pending = MetricCard("Missing part costs")
        for i, card in enumerate((self.devices, self.services, self.pricing, self.pending)): metrics.addWidget(card, 0, i)
        layout.addLayout(metrics)
        group = QGroupBox("Current integration state"); group_layout = QVBoxLayout(group)
        group_layout.addWidget(QLabel("Website: Offline export mode"))
        group_layout.addWidget(QLabel("Square: Sandbox not connected"))
        group_layout.addWidget(QLabel("MobileSentrix: Awaiting API approval"))
        layout.addWidget(group); layout.addStretch(); self.refresh()

    def refresh(self) -> None:
        self.devices.set_value(self.database.scalar("SELECT COUNT(*) FROM devices") or 0)
        self.services.set_value(self.database.scalar("SELECT COUNT(*) FROM services") or 0)
        self.pricing.set_value(self.database.scalar("SELECT COUNT(*) FROM pricing_records") or 0)
        self.pending.set_value(self.database.scalar("SELECT COUNT(*) FROM pricing_records WHERE part_cost_cents IS NULL") or 0)


class WorkbookImportPage(QWidget):
    def __init__(self, database: Database, dashboard: DashboardPage, refresh_callbacks: list) -> None:
        super().__init__(); self.import_service = ImportService(database); self.dashboard = dashboard
        self.refresh_callbacks = refresh_callbacks; self.pricing_path: Path | None = None; self.device_path: Path | None = None
        layout = QVBoxLayout(self)
        heading = QLabel("Workbook Import"); heading.setObjectName("pageHeading"); layout.addWidget(heading)
        layout.addWidget(QLabel("Select both authoritative workbooks, inspect them, then import into the local development database."))
        grid = QGridLayout()
        self.pricing_label = QLabel("No pricing workbook selected")
        self.device_label = QLabel("No device workbook selected")
        bp = QPushButton("Select Pricing Catalog"); bp.clicked.connect(self.select_pricing)
        bd = QPushButton("Select Device Mapping Workbook"); bd.clicked.connect(self.select_device)
        grid.addWidget(bp,0,0); grid.addWidget(self.pricing_label,0,1); grid.addWidget(bd,1,0); grid.addWidget(self.device_label,1,1)
        layout.addLayout(grid)
        row = QHBoxLayout(); inspect = QPushButton("Inspect Selected Workbook"); inspect.clicked.connect(self.inspect_selected)
        do_import = QPushButton("Import Master Data"); do_import.clicked.connect(self.import_data)
        row.addWidget(inspect); row.addWidget(do_import); row.addStretch(); layout.addLayout(row)
        self.tabs = QTabWidget(); layout.addWidget(self.tabs,1)

    def select_pricing(self):
        name,_=QFileDialog.getOpenFileName(self,"Select pricing workbook","","Excel Workbooks (*.xlsx)")
        if name: self.pricing_path=Path(name); self.pricing_label.setText(name)
    def select_device(self):
        name,_=QFileDialog.getOpenFileName(self,"Select device workbook","","Excel Workbooks (*.xlsx)")
        if name: self.device_path=Path(name); self.device_label.setText(name)
    def inspect_selected(self):
        path=self.device_path or self.pricing_path
        if not path: QMessageBox.warning(self,"Nothing selected","Select a workbook first."); return
        try: previews,row_count=self.import_service.inspect_xlsx(path)

        except (OSError, ValueError, RuntimeError) as exc:
            QMessageBox.critical(self,"Inspection failed",str(exc)); return
        self.tabs.clear()
        for preview in previews:
            table=QTableWidget(); table.setRowCount(len(preview.rows)); table.setColumnCount(max((len(r) for r in preview.rows),default=0))
            for r,row in enumerate(preview.rows):
                for c,value in enumerate(row): table.setItem(r,c,QTableWidgetItem(value))
            table.setAlternatingRowColors(True); table.resizeColumnsToContents(); self.tabs.addTab(table,preview.name)
        QMessageBox.information(self,"Workbook inspected",f"Inspected {len(previews)} worksheet(s) and approximately {row_count:,} rows.")
    def import_data(self):
        if not self.pricing_path or not self.device_path:
            QMessageBox.warning(self,"Files required","Select both workbooks before importing."); return
        try: counts=self.import_service.import_master_data(self.pricing_path,self.device_path)

        except (OSError, ValueError, RuntimeError) as exc:
            QMessageBox.critical(self,"Import failed",str(exc)); return
        self.dashboard.refresh()
        for callback in self.refresh_callbacks: callback()
        QMessageBox.information(self,"Import complete",f"Imported {counts['devices']:,} devices, {counts['services']:,} services, and {counts['pricing']:,} pricing records.")


class PlaceholderPage(QWidget):
    def __init__(self,title:str,message:str):
        super().__init__(); layout=QVBoxLayout(self); heading=QLabel(title); heading.setObjectName("pageHeading")
        label=QLabel(message); label.setWordWrap(True); label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(heading); layout.addWidget(label); layout.addStretch()
