class SupplierService:

    def __init__(self, repository):

        self.repository = repository

    def all(self):

        return self.repository.all()

    def get(self, supplier_id):

        return self.repository.get(supplier_id)

    def count(self):

        return self.repository.count()