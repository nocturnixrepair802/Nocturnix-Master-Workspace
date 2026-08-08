import pandas as pd

from core.base_service import BaseService


class SupplierService(BaseService):

    def __init__(self, repository):

        super().__init__(repository)

    # ======================================================
    # Collections
    # ======================================================

    def all(self) -> pd.DataFrame:

        return self.repository.all()

    def get(self, supplier_id) -> pd.Series | None:

        return self.repository.get(supplier_id)

    def count(self) -> int:

        return self.repository.count()

    def exists(self, supplier_id) -> bool:

        return self.repository.exists("Supplier ID", supplier_id)
