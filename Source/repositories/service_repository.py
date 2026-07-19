from repositories.repository_base import RepositoryBase
from models.service import Service


class ServiceRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(
            database,
            "master_services"
        )

    def get(self, service_id):

        row = self.first(
            "Service ID",
            service_id
        )

        if row is None:
            return None

        return Service(

            service_id=row["Service ID"],

            service_name=row["Service Name"],

            category=row["Service Category"],

            repair_type=row["Repair Type"],

            estimated_hours=row["Estimated Labor (hrs)"],

            active=row["Active"]

        )

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