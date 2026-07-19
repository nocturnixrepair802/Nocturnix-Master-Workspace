from config.database import TABLES


class DatabaseValidator:

    def __init__(self, data):
        self.data = data
        self.errors = []
        self.warnings = []

    def validate(self):

        print("\n" + "=" * 70)
        print("DATABASE VALIDATION")
        print("=" * 70)

        self.validate_required_tables()
        self.validate_table_sizes()
        self.validate_duplicate_keys()

        self.print_summary()

    def validate_required_tables(self):

        print("\nChecking Required Tables")

        for key in TABLES.keys():

            if key in self.data:
                print(f"✓ {key}")
            else:
                print(f"✗ {key}")
                self.errors.append(f"Missing table: {key}")

    def validate_table_sizes(self):

        print("\nChecking Table Sizes")

        for name, dataframe in self.data.items():

            if dataframe.empty:
                print(f"✗ {name} is empty")
                self.errors.append(f"{name} contains no records")
            else:
                print(f"✓ {name:<20} {len(dataframe):>6} rows")
    def validate_duplicate_keys(self):

        print("\nChecking Duplicate Keys")

        key_columns = {

            "manufacturer_catalog": "Manufacturer ID",

            "device_catalog": "Device Family Code",

            "master_devices": "Device ID",

            "master_services": "Service ID",

            "compatibility": "Compatibility ID",

        }

        for table_name, key_column in key_columns.items():

            if table_name not in self.data:
                continue

            dataframe = self.data[table_name]

            if key_column not in dataframe.columns:
                print(f"✗ {table_name}: Missing column '{key_column}'")
                self.errors.append(
                    f"{table_name} missing key column {key_column}"
                )
                continue

            # Ignore blank IDs before checking duplicates
            valid_rows = dataframe[dataframe[key_column].notna()]

            duplicates = valid_rows[
                valid_rows[key_column].duplicated()
            ]

            if duplicates.empty:
                print(f"✓ {table_name}")
            else:
                print(f"✗ {table_name}: {len(duplicates)} duplicate keys")
                self.errors.append(
                    f"{table_name} has duplicate {key_column} values"
                )

    def print_summary(self):

        print("\n" + "=" * 70)

        if self.errors:
            print("DATABASE STATUS : FAILED")
        else:
            print("DATABASE STATUS : PASSED")

        print(f"\nErrors   : {len(self.errors)}")
        print(f"Warnings : {len(self.warnings)}")

        if self.errors:

            print("\nError Details")

            for error in self.errors:
                print(f" • {error}")

        print("=" * 70)