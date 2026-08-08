from managers.service_manager import ServiceManager


class RepairController:

    def __init__(self, services: ServiceManager):

        self.services = services

    # ======================================================
    # New Repair Wizard
    # ======================================================

    def new_repair(self):

        print()
        print("=" * 70)
        print("NEW REPAIR WIZARD")
        print("=" * 70)

        # --------------------------------------------------
        # Step 1 - Customer
        # --------------------------------------------------

        customer_id = input("Customer ID : ")

        customer = self.services.customers.get(customer_id)

        if customer is None:

            print("\nCustomer not found.\n")
            return

        print(f"Customer : {customer['First Name']} {customer['Last Name']}")

        # --------------------------------------------------
        # Step 2 - Device
        # --------------------------------------------------

        device_id = input("\nDevice ID : ")

        device = self.services.devices.get(device_id)

        if device is None:

            print("\nDevice not found.\n")
            return

        print(f"Device : {device['Device Model']}")

        print()

        print("Repair Wizard Phase 2 Complete")
