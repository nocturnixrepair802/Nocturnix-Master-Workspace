from device_catalog_migration.audit import EntityRecord
from device_catalog_migration.relationship_engine import validate_records


def rec(entity, rid, values):
    return EntityRecord(entity, rid, values, "S", "T", 2)


def test_family_foreign_keys_validate():
    records = {
        "DeviceType": {"DT1": rec("DeviceType", "DT1", {"devicetypeid": "DT1", "devicetype": "Phone"})},
        "Manufacturer": {"MFG1": rec("Manufacturer", "MFG1", {"manufacturerid": "MFG1", "manufacturer": "Apple"})},
        "DeviceFamily": {"DF1": rec("DeviceFamily", "DF1", {"devicefamilyid": "DF1", "manufacturerid": "MFG1", "devicetypeid": "DT1", "devicefamily": "iPhone"})},
        "DeviceModel": {},
    }
    assert validate_records(records) == []


def test_missing_family_fk_fails():
    records = {
        "DeviceType": {},
        "Manufacturer": {},
        "DeviceFamily": {"DF1": rec("DeviceFamily", "DF1", {"devicefamilyid": "DF1", "manufacturerid": "MFG9", "devicetypeid": "DT9", "devicefamily": "iPhone"})},
    }
    issues = validate_records(records)
    assert any(i.rule == "Family manufacturer FK" for i in issues)
