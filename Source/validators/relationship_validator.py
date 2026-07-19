class RelationshipValidator:

    def __init__(self, database):

        self.database = database

        self.errors = []

    def validate(self):

        print()
        print("=" * 70)
        print("RELATIONSHIP VALIDATION")
        print("=" * 70)

        self.validate_devices()

        print()
        print("-" * 70)

        if self.errors:

            print(f"FAILED ({len(self.errors)} errors)\n")

            for error in self.errors:
                print(f"• {error}")

            return False

        print("PASSED")
        return True

    def validate_devices(self):

        if (
            "master_devices" not in self.database
            or
            "manufacturer_catalog" not in self.database
        ):
            return

        devices = self.database["master_devices"]

        manufacturers = self.database["manufacturer_catalog"]

        manufacturer_column = "Manufacturer Code"

        manufacturer_id_column = "Manufacturer ID"

        if (
            manufacturer_column not in devices.columns
            or
            manufacturer_id_column not in manufacturers.columns
        ):
            print("Skipping manufacturer validation (columns not found)")
            return

        valid_manufacturers = set(
            manufacturers[manufacturer_id_column]
            .dropna()
            .astype(str)
        )

        invalid = devices[
            ~devices[manufacturer_column]
            .astype(str)
            .isin(valid_manufacturers)
        ]

        if len(invalid):

            self.errors.append(
                f"{len(invalid)} device(s) reference invalid Manufacturer IDs."
            )

        else:

            print("✓ Device → Manufacturer relationships")