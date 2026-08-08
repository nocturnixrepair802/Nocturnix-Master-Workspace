from seeders.customer_seeder import CustomerSeeder
from seeders.device_seeder import CustomerDeviceSeeder
from seeders.repair_seeder import RepairSeeder


class SeederManager:

    def __init__(self, database):

        self.database = database

    def run(self):

        print()

        print("=" * 60)

        print("Running Database Seeders")

        print("=" * 60)

        customers = CustomerSeeder().generate(100)

        print(f"Customers............. {len(customers)}")

        devices = CustomerDeviceSeeder(self.database["master_devices"]).generate(
            customers, 300
        )

        print(f"Customer Devices...... {len(devices)}")

        repairs = RepairSeeder().generate(customers, devices, 150)

        print(f"Repair Tickets........ {len(repairs)}")

        self.database["customers"] = customers

        self.database["customer_devices"] = devices

        self.database["repair_tickets"] = repairs

        print()

        print("Seeding Complete")

        print("=" * 60)
