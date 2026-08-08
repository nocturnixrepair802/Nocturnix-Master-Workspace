class Device:

    def __init__(

        self,

        device_id,

        manufacturer,

        device_family,

        model,

        model_number,

        release_year,

        active=True

    ):

        self.device_id = device_id

        self.manufacturer = manufacturer

        self.device_family = device_family

        self.model = model

        self.model_number = model_number

        self.release_year = release_year

        self.active = active

    def __str__(self):

        return self.model