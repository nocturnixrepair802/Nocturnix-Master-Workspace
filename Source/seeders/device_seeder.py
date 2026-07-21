import random

import pandas as pd


class CustomerDeviceSeeder:

    def __init__(self, master_devices):

        self.master_devices = master_devices

    def generate(self, customers, count=300):

        records = []

        customer_ids = customers["Customer ID"].tolist()

        devices = self.master_devices.to_dict("records")

        for i in range(1, count + 1):

            customer = random.choice(customer_ids)

            device = random.choice(devices)

            records.append(
                {
                    "Device ID": f"DEV{i:06d}",
                    "Customer ID": customer,
                    "Manufacturer": device["Manufacturer Code"],
                    "Device Family": device["Device Family Code"],
                    "Device Model": device["Device Model"],
                    "Serial Number": f"SN{i:08d}",
                    "IMEI / Service Tag": f"{random.randint(100000000000000,999999999999999)}",
                    "Color": "",
                    "Storage": "",
                    "Carrier": "",
                    "Purchase Date": "",
                    "Warranty Expiration": "",
                    "Active": True,
                    "Notes": "",
                }
            )

        return pd.DataFrame(records)
