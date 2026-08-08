import pandas as pd

from core.base_service import BaseService


class RepairService(BaseService):

    def __init__(self, repository):

        super().__init__(repository)

    # ======================================================
    # READ
    # ======================================================

    def all(self) -> pd.DataFrame:

        return self.repository.all()

    def get(self, ticket_id) -> pd.Series | None:

        return self.repository.get(ticket_id)

    def count(self) -> int:

        return self.repository.count()

    # ======================================================
    # Search
    # ======================================================

    def search(self, text: str = "") -> pd.DataFrame:

        return self.repository.search(text)

    def exists(self, ticket_id) -> bool:

        return self.repository.exists(
            "Ticket ID",
            ticket_id
        )
