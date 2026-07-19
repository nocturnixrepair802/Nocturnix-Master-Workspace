class Compatibility:

    def __init__(

        self,

        compatibility_id,

        device_family,

        service_id,

        supported,

        required_capability=None,

        notes=None

    ):

        self.compatibility_id = compatibility_id

        self.device_family = device_family

        self.service_id = service_id

        self.supported = supported

        self.required_capability = required_capability

        self.notes = notes