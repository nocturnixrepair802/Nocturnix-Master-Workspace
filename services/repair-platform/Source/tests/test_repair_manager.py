from config import MASTER_DATABASE
from managers.repair_manager import RepairManager
from services.table_loader import TableLoader

print("=" * 70)
print("REPAIR MANAGER TEST")
print("=" * 70)

loader = TableLoader(MASTER_DATABASE)

database = loader.load_all_tables()

repair = RepairManager(database)

print()

print("Customers")

print(repair.repositories.customers.count())

print()

print("Devices")

print(repair.repositories.devices.count())

print()

print("Services")

print(repair.repositories.services.count())

print()

print("Suppliers")

print(repair.repositories.suppliers.count())