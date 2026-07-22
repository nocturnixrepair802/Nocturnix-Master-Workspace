from managers.service_manager import ServiceManager


class DeviceController:

    def __init__(self, services: ServiceManager):

        self.services = services

    # ======================================================
    # Collections
    # ======================================================

    def list_devices(self):

        devices = self.services.devices.search("")

        print()
        print("=" * 100)
        print("DEVICE CATALOG")
        print("=" * 100)

        columns = ["Device ID", "Manufacturer", "Device Family", "Device Model"]

        print(devices[columns].to_string(index=False))

        print()
        print(f"Total Devices : {len(devices)}")
        print()

    # ======================================================
    # Search
    # ======================================================

    def search_devices(self):

        print()
        print("=" * 70)
        print("DEVICE SEARCH")
        print("=" * 70)

        text = input("Search: ")

        results = self.services.devices.search(text)

        if results.empty:

            print("\nNo matching devices found.\n")
            return

        columns = ["Device ID", "Manufacturer", "Device Family", "Device Model"]

        print()
        print(results[columns].to_string(index=False))
        print()

    # ======================================================
    # Device Details
    # ======================================================

    def device_details(self):

        print()
        print("=" * 70)
        print("DEVICE DETAILS")
        print("=" * 70)

        device_id = input("Device ID: ")

        device = self.services.devices.get(device_id)

        if device is None:

            print("\nDevice not found.\n")
            return

        device["Manufacturer"] = self.services.devices.manufacturer_name(
            device["Manufacturer Code"]
        )

        device["Device Family"] = self.services.devices.family_name(
            device["Device Family Code"]
        )

        print()

        for field, value in device.items():

          if field in ("Manufacturer Code", "Device Family Code"):
            continue

          if value is None:
              value = ""

          elif hasattr(value, "item"):
              value = value.item()

          if isinstance(value, float):

              import math

              if math.isnan(value):
                  value = ""

              elif value.is_integer():
                  value = int(value)

          print(f"{field:<30}: {value}")

        repair_count = self.services.devices.repair_count(device_id)

        print("-" * 70)

        print(f"Available Repair Guides : {repair_count}")

        print()

    # ======================================================
    # Statistics
    # ======================================================

    def device_count(self):

        print()

        print(f"Devices : {self.services.devices.count()}")

        print()
