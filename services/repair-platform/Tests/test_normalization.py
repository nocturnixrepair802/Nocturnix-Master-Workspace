from device_catalog_migration.normalization import (
    normalize_header,
    normalize_text,
    trim_text,
)


def test_normalize_header_equivalents():
    assert normalize_header("Device Type ID") == "devicetypeid"
    assert normalize_header("device_type_id") == "devicetypeid"
    assert normalize_header("DEVICE-TYPE-ID") == "devicetypeid"


def test_normalize_text_collapses_space_and_case():
    assert normalize_text(" Nothing  Phone ") == "nothing phone"
    assert trim_text(" ASUS ") == "ASUS"
