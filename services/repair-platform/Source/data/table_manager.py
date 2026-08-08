import pandas as pd

from config.database import TABLES


class TableManager:

    def __init__(self, workbook):

        self.workbook = workbook

    # ======================================================
    # Tables
    # ======================================================

    def list_tables(self):

        print("\nWorkbook Tables")
        print("=" * 70)

        for worksheet in self.workbook.worksheets:

            if worksheet.tables:

                print(f"\n{worksheet.title}")

                for table in worksheet.tables.values():

                    print(f"  {table.name}")

    # ======================================================
    # Load One Table
    # ======================================================

    def load_table(self, table_name):

        for worksheet in self.workbook.worksheets:

            if table_name in worksheet.tables:

                table = worksheet.tables[table_name]

                rows = list(worksheet[table.ref])

                headers = [cell.value for cell in rows[0]]

                records = [[cell.value for cell in row] for row in rows[1:]]

                return pd.DataFrame(records, columns=headers)

        raise ValueError(f"Table '{table_name}' not found.")

    # ======================================================
    # Load All Tables
    # ======================================================

    def load_all_tables(self):

        data = {}

        print("\nLoading Database Tables")
        print("=" * 70)

        for key, table_name in TABLES.items():

            try:

                dataframe = self.load_table(table_name)

                data[key] = dataframe

                print(f"✓ {table_name:<30}" f"{len(dataframe):>6} rows")

            except Exception as error:

                print(f"✗ {table_name}")
                print(f"   {error}")

        return data
