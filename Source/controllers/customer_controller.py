from managers.service_manager import ServiceManager
from services.customer_editor import CustomerEditor


class CustomerController:

    def __init__(self, services: ServiceManager):

        self.editor = CustomerEditor()

    def list_customers(self):

        customers = self.services.customers.all()

        print()
        print("=" * 80)
        print("CUSTOMERS")
        print("=" * 80)

        print(customers)

        print()

    def customer_count(self):

        print()

        print(
            f"Customers : {self.services.customers.count()}"
        )

        print()

    def search_customer(self):

        print()

        print("=" * 70)
        print("CUSTOMER SEARCH")
        print("=" * 70)

        print("1. Last Name")
        print("2. Mobile Phone")

        option = input("\nSearch By: ")

        if option == "1":

            value = input("Last Name: ")

            print()

            print(
                self.services.customers.search_last_name(value)
            )

        elif option == "2":

            value = input("Phone: ")

            print()

            print(
                self.services.customers.search_phone(value)
            )

        else:

            print("Invalid selection.")

    def add_customer(self):

            print()

            print("=" * 70)
            print("ADD CUSTOMER")
            print("=" * 70)

            customer_id = input("Customer ID : ")
            customer_type = input("Customer Type : ")
            first_name = input("First Name : ")
            last_name = input("Last Name : ")
            business_name = input("Business Name : ")
            email = input("Email : ")
            mobile_phone = input("Mobile Phone : ")

            self.editor.add_customer(
                customer_id,
                customer_type,
                first_name,
                last_name,
                business_name,
                email,
                mobile_phone
            )