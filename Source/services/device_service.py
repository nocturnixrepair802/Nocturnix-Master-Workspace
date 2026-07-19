class DeviceService:

    def __init__(self, repository):

        self.repository = repository

    def all(self):

        return self.repository.all()

    def get(self, device_id):

        return self.repository.get(device_id)

    def count(self):

        return self.repository.count()