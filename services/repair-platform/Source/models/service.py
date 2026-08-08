class Service:

    def __init__(

        self,

        service_id,

        service_name,

        category,

        repair_type,

        estimated_hours,

        active=True

    ):

        self.service_id = service_id

        self.service_name = service_name

        self.category = category

        self.repair_type = repair_type

        self.estimated_hours = estimated_hours

        self.active = active