from services.device_service import DeviceService


class DeviceCatalogService:

    def __init__(self, application):

        self.application = application

        self.service = application.services.devices

    # ======================================================
    # Manufacturers
    # ======================================================

    def manufacturers(self):

        return self.service.manufacturers()

    # ======================================================
    # Device Families
    # ======================================================

    def families(self, manufacturer):

        if not manufacturer:

            return []

        return self.service.families(manufacturer)

    # ======================================================
    # Devices
    # ======================================================

    def devices(self, manufacturer, family):

        if not manufacturer:

            return []

        if not family:

            return []

        return self.service.devices(manufacturer, family)

    # ======================================================
    # Search
    # ======================================================

    def search(self, text):

        return self.service.search(text)

    # ======================================================
    # Counts
    # ======================================================

    def manufacturer_count(self):

        return len(self.manufacturers())

    def family_count(self, manufacturer):

        return len(self.families(manufacturer))

    def device_count(self, manufacturer, family):

        return len(self.devices(manufacturer, family))
