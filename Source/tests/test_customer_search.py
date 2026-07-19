from app import Application
from services.customer_search import CustomerSearch

app = Application()

search = CustomerSearch(
    app.repositories.customers
)

print("=" * 70)
print("CUSTOMER SEARCH TEST")
print("=" * 70)

print()

print(search.by_last_name("Smith"))