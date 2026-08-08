"""
Labor Repository

Reserved for future labor rate management.
"""
from repositories.repository_base import RepositoryBase


class LaborRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "labor_rates")

    def all(self):

        return super().all()

    def current_rate(self):

        if self.table.empty:
            return None

        return self.table.iloc[0]
