from models.repair_session import RepairSession


class RepairWorkflow:
    """
    Coordinates the complete repair creation workflow.
    """

    def __init__(self, repair_manager):

        self.repair_manager = repair_manager

        self.session = RepairSession()

    # ======================================================
    # Customer
    # ======================================================

    def select_customer(self, customer):

        self.session.customer = customer

    # ======================================================
    # Device
    # ======================================================

    def select_device(self, device):

        self.session.device = device

    # ======================================================
    # Repair
    # ======================================================

    def select_service(self, service):

        self.session.service = service

    # ======================================================
    # Utility
    # ======================================================

    def clear(self):

        self.session.reset()

    @property
    def current(self):

        return self.session
