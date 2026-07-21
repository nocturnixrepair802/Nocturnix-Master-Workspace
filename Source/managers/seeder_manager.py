from seeders.customer_seeder import CustomerSeeder
from seeders.repair_seeder import RepairSeeder


class SeederManager:

    def __init__(self, application):

        self.application = application

        self.customers = CustomerSeeder(application)

        self.repairs = RepairSeeder(application)

    # ======================================================
    # Run All
    # ======================================================

    def run(self):

        print()

        print("=" * 70)

        print("Running Seeders")

        print("=" * 70)

        self.customers.seed()

        self.repairs.seed()

        print()

        print("=" * 70)

        print("Seeder Complete")

        print("=" * 70)
