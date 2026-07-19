class CustomerSearch:

    def __init__(self, repository):

        self.repository = repository

    def by_id(self, customer_id):

        return self.repository.get(customer_id)

    def by_last_name(self, last_name):

        customers = self.repository.all()

        return customers[
            customers["Last Name"]
            .str.contains(
                last_name,
                case=False,
                na=False
            )
        ]

    def by_phone(self, phone):

        customers = self.repository.all()

        return customers[
            customers["Mobile Phone"]
            .astype(str)
            .str.contains(
                phone,
                na=False
            )
        ]