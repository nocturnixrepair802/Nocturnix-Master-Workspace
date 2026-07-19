from workflow.repair_workflow import RepairWorkflow
from workflow.estimate_workflow import EstimateWorkflow
from workflow.invoice_workflow import InvoiceWorkflow


class WorkflowManager:

    def __init__(

        self,

        repair_manager

    ):

        self.repair = RepairWorkflow(

            repair_manager

        )

        self.estimate = EstimateWorkflow(

            repair_manager

        )

        self.invoice = InvoiceWorkflow(

            repair_manager

        )