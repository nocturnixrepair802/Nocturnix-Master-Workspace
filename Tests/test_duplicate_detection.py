from device_catalog_migration.audit import EntityRecord
from device_catalog_migration.relationship_engine import detect_duplicates


def test_duplicate_manufacturer_name_detected():
    records = {
        "Manufacturer": {
            "MFG1": EntityRecord("Manufacturer", "MFG1", {"manufacturer": "ASUS", "manufacturerid": "MFG1"}, "S", "T", 2),
            "MFG2": EntityRecord("Manufacturer", "MFG2", {"manufacturer": " Asus ", "manufacturerid": "MFG2"}, "S", "T", 3),
        }
    }
    issues = detect_duplicates(records)
    assert issues
    assert issues[0].duplicate_type == "NORMALIZED_NAME_DUPLICATE"
