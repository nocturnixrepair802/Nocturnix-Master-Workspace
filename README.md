# Nocturnix Core Desktop v0.2

This build turns the v0.1 shell into a working local catalog importer.

## Working features

- Select and inspect both authoritative Excel workbooks without modifying them
- Import `DeviceCatalogTable` from `DeviceFamilyTypeID.xlsx`
- Import `Service Catalog` and match `21 - Pricing Output`
- Rebuild the local SQLite development database in one controlled transaction
- Searchable Device Catalog and Service Catalog screens
- Dashboard counts, including missing supplier part costs
- Money displayed in U.S. dollars

## Setup

1. Extract the project folder.
2. Run `setup_windows.bat` once.
3. Run `run_app.bat`.
4. Open **Workbook Import**.
5. Select:
   - `Nocturnix_Master_Pricing_Catalog_v3.5_Audited_Updated.xlsx`
   - `DeviceFamilyTypeID.xlsx`
6. Click **Import Master Data**.

The original workbooks remain unchanged. The imported development database is stored at `data/nocturnix_dev.sqlite3`.

## Next version

- Pricing approval queue
- Website JSON export
- Square catalog staging export
- Import validation report and duplicate checks
