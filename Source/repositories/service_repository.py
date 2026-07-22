from repositories.repository_base import RepositoryBase


class ServiceRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(
            database,
            "master_services"
        )

    def get(self, service_id):

        return self.first("Service ID", service_id)


    def by_category(self, category):

        return self.filter(
            "Service Category",
            category
        )

    def active_services(self):

        return self.filter(
            "Active",
            True
        )

    # ======================================================
    # Collections
    # ======================================================


    def all(self):

        return super().all()
