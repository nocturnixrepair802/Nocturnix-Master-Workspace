from repositories.repository_base import RepositoryBase


class CustomerRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "customers")

    # ======================================================
    # Collections
    # ======================================================

    def all(self):

        return super().all()

    # ======================================================
    # Single Record
    # ======================================================

    def get(self, customer_id):

        return self.first("Customer ID", customer_id)
