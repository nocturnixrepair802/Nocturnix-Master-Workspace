import pandas as pd


class RepositoryBase:
    """
    Base class for all DataFrame-backed repositories.
    """

    def __init__(self, database, table_name):

        self.database = database

        self.table_name = table_name

        if table_name not in database:

            raise ValueError(f"Table '{table_name}' not loaded.")

        self.table = database[table_name]

    # ==========================================================
    # READ
    # ==========================================================

    def all(self) -> pd.DataFrame:

        return self.table.copy()

    def count(self):

        return len(self.table)

    def columns(self):

        return list(self.table.columns)

    def exists(self, column, value):

        self.validate_column(column)

        return value in self.table[column].values

    def find(self, column: str, value) -> pd.DataFrame:

        self.validate_column(column)

        return self.table[self.table[column] == value]

    def first(self, column: str, value) -> pd.Series | None:

        records = self.find(column, value)

        if records.empty:

            return None

        return records.iloc[0]

    def filter(self, column, value):

        return self.find(column, value)

    def unique(self, column):

        self.validate_column(column)

        return sorted(self.table[column].dropna().unique().tolist())

    # ==========================================================
    # WRITE
    # ==========================================================

    def append(self, row):

        self.table = pd.concat([self.table, pd.DataFrame([row])], ignore_index=True)

        self.database[self.table_name] = self.table

    def replace_all(self, dataframe):

        self.table = dataframe.copy()

        self.database[self.table_name] = self.table

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def validate_column(self, column):

        if column not in self.table.columns:

            raise ValueError(f"Column '{column}' not found in '{self.table_name}'.")
