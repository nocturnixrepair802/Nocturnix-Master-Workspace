from app import Application

app = Application()

customers = app.repositories.customers.all()

print(customers)