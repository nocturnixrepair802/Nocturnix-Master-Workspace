from config import MASTER_DATABASE
from managers.repository_manager import RepositoryManager
from services.table_loader import TableLoader

print("=" * 70)
print("REPOSITORY TEST")
print("=" * 70)

loader = TableLoader(MASTER_DATABASE)

database = loader.load_all_tables()

repositories = RepositoryManager(database)

print()

print("Customers")

print(repositories.customers.count())

print()

print("Manufacturers")

print(repositories.manufacturers.count())

print()

print("Devices")

print(repositories.devices.count())

print()

print("Services")

print(repositories.services.count())

print()

print("Compatibility")

print(repositories.compatibility.count())

print()

print("Suppliers")

print(repositories.suppliers.count())