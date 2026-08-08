import random

import pandas as pd


class CustomerSeeder:

    def generate(self, count=100):

        first_names = [
            "Michael",
            "Sarah",
            "David",
            "Jennifer",
            "Christopher",
            "Amanda",
            "Daniel",
            "Ashley",
            "Matthew",
            "Jessica",
        ]

        last_names = [
            "Johnson",
            "Miller",
            "Thompson",
            "Adams",
            "Wilson",
            "Brown",
            "Taylor",
            "Moore",
            "Clark",
            "Hall",
        ]

        records = []

        for i in range(1, count + 1):

            first = random.choice(first_names)
            last = random.choice(last_names)

            records.append(
                {
                    "Customer ID": f"CUS{i:06d}",
                    "Customer Type": "Residential",
                    "First Name": first,
                    "Last Name": last,
                    "Business Name": "",
                    "Email": f"{first.lower()}.{last.lower()}{i}@email.com",
                    "Mobile Phone": f"(802) 555-{1000+i:04d}",
                    "Home Phone": "",
                    "Work Phone": "",
                    "Preferred Contact": "Mobile",
                    "Billing Address": "",
                    "Shipping Address": "",
                    "Tax Exempt": False,
                    "Active": True,
                    "Date Created": "",
                    "Last Modified": "",
                    "Notes": "",
                }
            )

        return pd.DataFrame(records)
