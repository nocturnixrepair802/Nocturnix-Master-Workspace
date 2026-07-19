class RepairTicket:

    def __init__(

        self,

        ticket_number,

        customer,

        device,

        status,

        diagnosis,

        technician=None

    ):

        self.ticket_number = ticket_number

        self.customer = customer

        self.device = device

        self.status = status

        self.diagnosis = diagnosis

        self.technician = technician