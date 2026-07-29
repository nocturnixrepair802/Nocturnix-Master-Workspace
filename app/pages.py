from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
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
        except Exception as exc: QMessageBox.critical(self,"Inspection failed",str(exc)); return
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
        except Exception as exc: QMessageBox.critical(self,"Import failed",str(exc)); return
        self.dashboard.refresh()
        for callback in self.refresh_callbacks: callback()
        QMessageBox.information(self,"Import complete",f"Imported {counts['devices']:,} devices, {counts['services']:,} services, and {counts['pricing']:,} pricing records.")


class CatalogPage(QWidget):
    def __init__(self, database: Database, kind: str) -> None:
        super().__init__(); self.database=database; self.kind=kind
        layout=QVBoxLayout(self); heading=QLabel("Device Catalog" if kind=="devices" else "Service Catalog"); heading.setObjectName("pageHeading"); layout.addWidget(heading)
        self.search=QLineEdit(); self.search.setPlaceholderText("Search..."); self.search.textChanged.connect(self.refresh); layout.addWidget(self.search)
        self.table=QTableWidget(); self.table.setAlternatingRowColors(True); layout.addWidget(self.table,1); self.refresh()
    def refresh(self):
        term=f"%{self.search.text().strip()}%" if hasattr(self,'search') else "%"
        if self.kind=="devices":
            headers=["Device ID","Manufacturer","Model","Family ID","Type ID","Active"]
            rows=self.database.rows("SELECT device_id,manufacturer,model,device_family_id,device_type_id,active FROM devices WHERE manufacturer LIKE ? OR model LIKE ? ORDER BY manufacturer,model LIMIT 500",(term,term))
        else:
            headers=["Service ID","Service Name","Service Type","Device ID","Part Cost","Retail","Status"]
            rows=self.database.rows("""SELECT s.service_id,s.internal_name,s.service_type_name,p.device_id,p.part_cost_cents,p.retail_price_cents,p.approval_status FROM services s JOIN pricing_records p ON p.service_id=s.service_id WHERE s.internal_name LIKE ? OR s.service_type_name LIKE ? ORDER BY s.internal_name LIMIT 500""",(term,term))
        self.table.setColumnCount(len(headers)); self.table.setHorizontalHeaderLabels(headers); self.table.setRowCount(len(rows))
        for r,row in enumerate(rows):
            for c,value in enumerate(row):
                if self.kind!="devices" and c in (4,5): value="" if value is None else f"${value/100:,.2f}"
                if self.kind=="devices" and c==5: value="Yes" if value else "No"
                self.table.setItem(r,c,QTableWidgetItem(str(value or "")))
        self.table.resizeColumnsToContents()


class PlaceholderPage(QWidget):
    def __init__(self,title:str,message:str):
        super().__init__(); layout=QVBoxLayout(self); heading=QLabel(title); heading.setObjectName("pageHeading")
        label=QLabel(message); label.setWordWrap(True); label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(heading); layout.addWidget(label); layout.addStretch()
