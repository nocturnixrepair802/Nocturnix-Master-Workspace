from services.customer_editor import CustomerEditor
from services.customer_service import CustomerService


class CustomerGuiService:

    def __init__(self, application):

        self.application = application

        self.repository = application.repositories.customers

        self.service = CustomerService(self.repository)

        self.editor = CustomerEditor(self.repository)

    # ==========================================================
    # READ
    # ==========================================================

    def all_customers(self):

        return self.service.all()

    def search_customers(self, text):

        return self.service.search(text)

    def customer_count(self):

        return self.service.count()

    def get_customer(self, customer_id):

        return self.service.get(customer_id)

    # ==========================================================
    # CREATE
    # ==========================================================

    def add_customer(self, customer):

        return self.editor.add(customer)

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update_customer(self, customer_id, customer):

        return self.editor.update(customer_id, customer)

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete_customer(self, customer_id):

        return self.editor.delete(customer_id)
