from app import Application
from managers.service_manager import ServiceManager

print("=" * 70)
print("SERVICE MANAGER TEST")
print("=" * 70)

app = Application()

services = ServiceManager(app.repositories)

print()

print("Customers :", services.customers.count())
print("Devices   :", services.devices.count())
print("Repairs   :", services.repairs.count())
print("Suppliers :", services.suppliers.count())