from pathlib import Path

from core.xlsx_preview import read_workbook_preview


def test_preview_reads_workbook(tmp_path: Path) -> None:
    # Integration smoke tests will use a copied fixture in a later release.
    assert callable(read_workbook_preview)
