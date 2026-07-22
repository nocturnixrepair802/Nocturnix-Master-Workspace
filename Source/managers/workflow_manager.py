from workflow.repair_workflow import RepairWorkflow
from workflow.estimate_workflow import EstimateWorkflow
from workflow.invoice_workflow import InvoiceWorkflow
from managers.repair_manager import RepairManager

class WorkflowManager:
    """
    Creates and owns all business workflows.
    """

    def __init__(self, repair_manager: RepairManager):

        self.repair_manager: RepairManager = repair_manager

        # ======================================================
        # Business Workflows
        # ======================================================

        self.repairs = RepairWorkflow(repair_manager)

        self.estimates = EstimateWorkflow(repair_manager)

        self.invoices = InvoiceWorkflow(repair_manager)

    # ======================================================
    # Utility
    # ======================================================

    def all(self) -> dict:

        return {
            "repairs": self.repairs,
            "estimates": self.estimates,
            "invoices": self.invoices,
        }
