"""Configuration constants for the device catalog migration."""

from __future__ import annotations

OUTPUT_XLSX = "Nocturnix_Master_Devices_Catalog_v1.6_Normalized_Draft.xlsx"
REPORT_JSON = "Nocturnix_Master_Devices_Catalog_v1.6_Migration_Report.json"
LOG_CSV = "Nocturnix_Master_Devices_Catalog_v1.6_Migration_Log.csv"
EXCEPTIONS_CSV = "Nocturnix_Master_Devices_Catalog_v1.6_Exceptions.csv"
README_REPORT = "README_Device_Catalog_Migration.md"

AUDIT_SHEETS = [
    "Migration Summary",
    "Migration Audit Log",
    "Migration Exceptions",
    "Relationship Validation",
    "Duplicate Review",
    "Source Table Inventory",
]

ENTITY_SPECS = {
    "DeviceType": {
        "id": "devicetypeid",
        "name": "devicetype",
        "required": {"devicetypeid", "devicetype"},
    },
    "Manufacturer": {
        "id": "manufacturerid",
        "name": "manufacturer",
        "required": {"manufacturerid", "manufacturer"},
    },
    "DeviceFamily": {
        "id": "devicefamilyid",
        "name": "devicefamily",
        "required": {"devicefamilyid", "devicefamily"},
    },
    "DeviceModel": {
        "id": "devicemodelid",
        "name": "devicemodel",
        "required": {"devicemodelid", "devicefamilyid"},
    },
}

ALIASES = {
    "devicetype": {"devicetype", "devicetype name", "device type"},
    "manufacturer": {"manufacturer", "manufacturername", "manufacturer name"},
    "devicefamily": {"devicefamily", "devicefamilyname", "device family"},
    "devicemodelid": {"modelid"},
    "devicemodel": {"devicemodel", "devicemodelname", "device model", "modelname", "devicename", "device display name"},
    "modelnumber": {"modelnumber", "manufacturermodel", "model number"},
    "isactive": {"isactive", "active"},
}
