from workflow.workflow_base import WorkflowBase


class InvoiceWorkflow(WorkflowBase):

    def create(

        self,

        repair_quote

    ):

        return self.success(

            "Invoice generated.",

            repair_quote

        )