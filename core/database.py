from __future__ import annotations

import sqlite3
from pathlib import Path


class Database:
    def __init__(self, database_path: Path, schema_path: Path) -> None:
        self.database_path = database_path
        self.schema_path = schema_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        schema = self.schema_path.read_text(encoding="utf-8")
        with self.connect() as connection:
            connection.executescript(schema)

    def scalar(self, query: str, params: tuple = ()) -> int | str | None:
        with self.connect() as connection:
            row = connection.execute(query, params).fetchone()
            return None if row is None else row[0]

    def rows(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(connection.execute(query, params))

    def execute(self, query: str, params: tuple = ()) -> int:
        """Execute a write query and return the number of affected rows."""

        with self.connect() as connection:
            cursor = connection.execute(query, params)
            connection.commit()
            return cursor.rowcount
