import openpyxl
from collections import Counter
from pathlib import Path

path = Path(
    r"D:\Business Portal\300_Pricing\Working\Nocturnix_Master_Devices_Catalog_v1.xlsx"
)
wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
ws = wb["01 - Master Devices"]
rows = list(ws.iter_rows(values_only=True))
headers = rows[0]
records = []
for row in rows[1:]:
    rec = dict(zip(headers, row))
    records.append(rec)

print("row count", len(records))
print(
    "manufacturer names",
    Counter(r["Manufacturer Name"] for r in records if r.get("Manufacturer Name")),
)
print("device names sample", [r["Device Name"] for r in records[:20]])
