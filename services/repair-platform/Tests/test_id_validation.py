from device_catalog_migration.normalization import valid_id


def test_valid_ids_accept_existing_padding():
    assert valid_id("DeviceType", "DT000001")
    assert valid_id("Manufacturer", "MFG1")
    assert valid_id("DeviceFamily", "DF081")
    assert valid_id("DeviceModel", "MOD000001")


def test_invalid_ids_rejected():
    assert not valid_id("Manufacturer", "APL")
    assert not valid_id("DeviceType", "DT-1")
