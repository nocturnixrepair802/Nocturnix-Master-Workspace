class CustomerRepository:

    def add(self, customer):

        self.database.insert("tblCustomers", customer)
