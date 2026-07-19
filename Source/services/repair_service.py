class RepairService:

    def __init__(self, repository):

        self.repository = repository

    def all(self):

        return self.repository.all()

    def get(self, service_id):

        return self.repository.get(service_id)

    def count(self):

        return self.repository.count()