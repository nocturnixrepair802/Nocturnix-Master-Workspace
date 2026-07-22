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
