from repositories.repository_base import RepositoryBase
from models.customer import Customer


class CustomerRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(
            database,
            "customers"
        )

    def get(self, customer_id):

        row = self.first(
            "Customer ID",
            customer_id
        )

        if row is None:
            return None

        return Customer(

            customer_id=row["Customer ID"],

            first_name=row["First Name"],

            last_name=row["Last Name"],

            business_name=row["Business Name"],

            email=row["Email"],

            mobile_phone=row["Mobile Phone"],

            preferred_contact=row["Preferred Contact"],

            active=row["Active"]

        )

    def all_customers(self):

        customers = []

        for _, row in self.table.iterrows():

            customers.append(

                Customer(

                    customer_id=row["Customer ID"],

                    first_name=row["First Name"],

                    last_name=row["Last Name"],

                    business_name=row["Business Name"],

                    email=row["Email"],

                    mobile_phone=row["Mobile Phone"],

                    preferred_contact=row["Preferred Contact"],

                    active=row["Active"]

                )

            )

        return customers