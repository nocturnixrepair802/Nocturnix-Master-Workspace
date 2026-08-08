from repositories.repository_base import RepositoryBase


class RepairRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "repair_tickets")

    # ======================================================
    # Collections
    # ======================================================

    def all(self):

        return super().all()

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

        return self.first("Ticket ID", ticket_id)

    # ======================================================
    # Count
    # ======================================================

    def count(self):

        return super().count()
