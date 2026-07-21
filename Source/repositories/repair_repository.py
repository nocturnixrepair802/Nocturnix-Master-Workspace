from repositories.repository_base import RepositoryBase


class RepairRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "repair_tickets")

    # ======================================================
    # Collections
    # ======================================================

    def all_repairs(self):

        return self.table.copy()

    # ======================================================
    # Search
    # ======================================================


    def search(self, text=""):

        if not text:

            return self.table.copy()

        text = str(text).lower()

        mask = (
            self.table["Ticket ID"].fillna("").astype(str).str.lower().str.contains(text)
            | self.table["Customer ID"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(text)
            | self.table["Device ID"].fillna("").astype(str).str.lower().str.contains(text)
            | self.table["Repair Status"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(text)
            | self.table["Problem Description"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(text)
        )

        return self.table.loc[mask].copy()

    # ======================================================
    # Single Record
    # ======================================================

    def get(self, ticket_id):

        row = self.first("Ticket ID", ticket_id)

        if row is None:

            return None

        return row

    # ======================================================
    # Count
    # ======================================================

    def count(self):

        return len(self.table)
