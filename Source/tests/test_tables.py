from config import MASTER_DATABASE
from services.table_loader import TableLoader

loader = TableLoader(MASTER_DATABASE)

compatibility = loader.load_table("tblCompatibilityID")

duplicates = compatibility[
    compatibility["Compatibility ID"].duplicated(keep=False)
]

print("=" * 70)
print("DUPLICATE COMPATIBILITY IDs")
print("=" * 70)

if duplicates.empty:
    print("No duplicate IDs found.")
else:
    print(duplicates.sort_values("Compatibility ID"))