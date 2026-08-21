import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_FOLDER = PROJECT_ROOT / "Data"

MASTER_DATABASE = DATA_FOLDER / "Nocturnix_Master_Database.xlsm"

TABLES = {
    "customers": "tblCustomers",
    "customer_devices": "tblCustomerDevices",
    "repair_tickets": "tblRepairTickets",
    "diagnostics": "tblDiagnostics",
    "manufacturer_catalog": "tblManufacturerCatalog",
    "device_catalog": "tblDeviceCatalog",
    "master_devices": "tblMasterDevices",
    "service_types": "tblServiceTypes",
    "master_services": "tblMasterServices",
    "compatibility": "tblCompatibilityID",
    # ======================================================
    # Technical Knowledge System
    # ======================================================
    "guide_categories": "tblGuideCategories",
    "guide_sources": "tblGuideSources",
    "repair_guides": "tblRepairGuides",
    "technical_library": "tblTechnicalLibrary",
    "parts_catalog": "tblPartsCatalog",
    "supplier_catalog": "tblSupplierCatalog",
    "labor_rates": "tblLaborRates",
    "parts_pricing": "tblParts",
    "retail_pricing": "tblRetailPricing",
    "profit_margin": "tblProfitMargin",
}
# ======================================================
# Operational SQLite Database
# ======================================================

OPERATIONS_DATA_FOLDER = PROJECT_ROOT / "data"

OPERATIONS_LOCAL_DATABASE = (
    OPERATIONS_DATA_FOLDER / "nocturnix_operations.local.sqlite3"
)

OPERATIONS_FALLBACK_DATABASE = OPERATIONS_DATA_FOLDER / "nocturnix_operations.sqlite3"

_configured_operations_database = os.environ.get(
    "NOCTURNIX_OPERATIONS_DATABASE",
    "",
).strip()

if _configured_operations_database:
    OPERATIONS_DATABASE = Path(_configured_operations_database).expanduser()
elif OPERATIONS_LOCAL_DATABASE.exists():
    OPERATIONS_DATABASE = OPERATIONS_LOCAL_DATABASE
else:
    OPERATIONS_DATABASE = OPERATIONS_FALLBACK_DATABASE
# ======================================================
# Read-Only Master Catalog SQLite Database
# ======================================================

CATALOG_DATABASE = Path(
    os.environ.get(
        "NOCTURNIX_CATALOG_DATABASE",
        (
            r"D:\Development\Desktop Application"
            r"\Nocturnix_Core_Desktop_v0.2"
            r"\data\nocturnix_dev.sqlite3"
        ),
    )
)
