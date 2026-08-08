from pathlib import Path

import openpyxl

path = Path(
    r"D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Devices_Catalog_v1.xlsx"
)
wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
ws = wb["01 - Master Devices"]
rows = list(ws.iter_rows(values_only=True))
headers = rows[0]
for row in rows[1:15]:
    rec = dict(zip(headers, row))
    print(
        rec["Device ID"],
        "|",
        rec["Manufacturer ID"],
        "|",
        rec["Manufacturer Name"],
        "|",
        rec["Device Family Name"],
        "|",
        rec["Device Name"],
        "|",
        rec["Model Number"],
        "|",
        rec["Generation"],
        "|",
        rec["Release Year"],
        "|",
        rec["Form Factor"],
    )
