class RepairService:

    def __init__(self, repository):

        self.repository = repository

    # ======================================================
    # READ
    # ======================================================

    def all(self):

        return self.repository.all_repairs()

    def get(self, ticket_id):

        return self.repository.get(ticket_id)

    def count(self):

        return self.repository.count()

    # ======================================================
    # Search
    # ======================================================

    def search(self, text=""):

        return self.repository.search(text)
