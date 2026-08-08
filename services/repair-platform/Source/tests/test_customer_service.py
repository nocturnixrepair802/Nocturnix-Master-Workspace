from app import Application
from services.customer_service import CustomerService

print("=" * 70)
print("CUSTOMER SERVICE TEST")
print("=" * 70)

app = Application()

service = CustomerService(
    app.repositories.customers
)

print()

print("Customer Count")

print(service.count())

print()

print("All Customers")

print(service.all())