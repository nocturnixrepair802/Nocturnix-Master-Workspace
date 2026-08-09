from pathlib import Path

import openpyxl

path = Path(
    r"D:\Business Portal\300_Pricing\Working\Nocturnix_Manufacturer_Registry_v0.1_Draft.xlsx"
)
wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
ws = wb["01 - Manufacturer Registry"]
rows = list(ws.iter_rows(values_only=True))
for i, row in enumerate(rows[:50]):
    print(i, row)
