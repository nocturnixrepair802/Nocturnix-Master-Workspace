from abc import ABC


class EngineBase(ABC):

    def __init__(self, database):

        self.database = database

    def get_table(self, table_name):

        if table_name not in self.database:

            raise ValueError(
                f"Database table '{table_name}' not loaded."
            )

        return self.database[table_name]

    def table_exists(self, table_name):

        return table_name in self.database

    def record_exists(self, table_name, column, value):

        table = self.get_table(table_name)

        return value in table[column].values

    def find_record(self, table_name, column, value):

        table = self.get_table(table_name)

        return table[
            table[column] == value
        ]