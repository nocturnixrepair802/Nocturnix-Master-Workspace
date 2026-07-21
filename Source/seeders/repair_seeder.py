import random

import pandas as pd


class RepairSeeder:

    def generate(self, customers, customer_devices, count=150):

        statuses = [
            "Open",
            "In Progress",
            "Waiting Parts",
            "Completed",
            "Picked Up",
            "Cancelled",
        ]

        technicians = ["Ryan", "Alex", "Jordan", "Taylor"]

        records = []

        customer_ids = customers["Customer ID"].tolist()

        devices = customer_devices.to_dict("records")

        for i in range(1, count + 1):

            customer = random.choice(customer_ids)

            device = random.choice(devices)

            records.append(
                {
                    "Ticket ID": f"REP{i:06d}",
                    "Customer ID": customer,
                    "Device ID": device["Device ID"],
                    "Repair Status": random.choice(statuses),
                    "Intake Date": "",
                    "Technician": random.choice(technicians),
                    "Problem Description": "Screen Damage",
                    "Diagnosis": "",
                    "Estimated Cost": 0.00,
                    "Final Cost": 0.00,
                    "Date Completed": "",
                    "Date Picked Up": "",
                    "Warranty": "",
                    "Notes": "",
                }
            )

        return pd.DataFrame(records)
