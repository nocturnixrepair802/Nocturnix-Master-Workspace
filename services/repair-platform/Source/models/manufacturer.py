class Manufacturer:

    def __init__(

        self,

        manufacturer_id,

        manufacturer,

        website,

        active=True

    ):

        self.manufacturer_id = manufacturer_id

        self.manufacturer = manufacturer

        self.website = website

        self.active = active

    def __str__(self):

        return self.manufacturer