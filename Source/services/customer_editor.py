from datetime import datetime


class CustomerEditor:

    def __init__(self, repository):

        self.repository = repository

    # ==========================================================
    # CREATE
    # ==========================================================

    def add(self, customer):

        customer = customer.copy()

        customer["Customer ID"] = self.next_customer_id()

        customer.setdefault("Customer Type", "")
        customer.setdefault("First Name", "")
        customer.setdefault("Last Name", "")
        customer.setdefault("Business Name", "")
        customer.setdefault("Email", "")
        customer.setdefault("Mobile Phone", "")
        customer.setdefault("Home Phone", "")
        customer.setdefault("Work Phone", "")
        customer.setdefault("Preferred Contact", "Mobile Phone")
        customer.setdefault("Billing Address", "")
        customer.setdefault("Shipping Address", "")
        customer.setdefault("Tax Exempt", False)
        customer.setdefault("Active", True)
        customer.setdefault("Date Created", datetime.now())
        customer.setdefault("Last Modified", datetime.now())
        customer.setdefault("Notes", "")

        self.repository.append(customer)

        return customer["Customer ID"]

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update(self, customer_id, updates):

        table = self.repository.table

        matches = table.index[table["Customer ID"] == customer_id]

        if len(matches) == 0:

            return False

        row = matches[0]

        for column, value in updates.items():

            if column in table.columns:

                table.at[row, column] = value

        table.at[row, "Last Modified"] = datetime.now()

        self.repository.replace(table)

        return True

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete(self, customer_id):

        table = self.repository.table

        table = table[table["Customer ID"] != customer_id].copy()

        self.repository.replace(table)

        return True

    # ==========================================================
    # CUSTOMER ID
    # ==========================================================

    def next_customer_id(self):

        table = self.repository.table

        if table.empty:

            return 1000

        return int(table["Customer ID"].max()) + 1
