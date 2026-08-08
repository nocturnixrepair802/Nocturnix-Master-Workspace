import pandas as pd

from core.base_service import BaseService


class CustomerService(BaseService):

    def __init__(self, repository):

        super().__init__(repository)

    # ==========================================================
    # Basic Operations
    # ==========================================================

    def all(self) -> pd.DataFrame:

        return self.repository.all()

    def get(self, customer_id) -> pd.Series | None:

        return self.repository.get(customer_id)

    def count(self) -> int:

        return self.repository.count()

    # ==========================================================
    # Search Methods
    # ==========================================================

    def search(self, text: str = "") -> pd.DataFrame:

        customers = self.repository.all()

        if not text:

            return customers

        text = str(text)

        mask = (
            customers["First Name"].fillna("").str.contains(text, case=False, na=False)
            | customers["Last Name"].fillna("").str.contains(text, case=False, na=False)
            | customers["Business Name"]
            .fillna("")
            .str.contains(text, case=False, na=False)
            | customers["Email"].fillna("").str.contains(text, case=False, na=False)
            | customers["Mobile Phone"]
            .fillna("")
            .astype(str)
            .str.contains(text, na=False)
        )

        return customers[mask]

    def search_last_name(self, last_name: str) -> pd.DataFrame:

        customers = self.repository.all()

        return customers[
            customers["Last Name"]
            .fillna("")
            .str.contains(
                last_name,
                case=False,
                na=False,
            )
        ]

    def search_phone(self, phone: str) -> pd.DataFrame:

        customers = self.repository.all()

        return customers[
            customers["Mobile Phone"]
            .fillna("")
            .astype(str)
            .str.contains(
                phone,
                na=False,
            )
        ]


    def exists(self, customer_id) -> bool:

        return self.repository.exists(
            "Customer ID",
            customer_id
        )
