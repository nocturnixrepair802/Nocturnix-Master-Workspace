from workflow.workflow_base import WorkflowBase


class EstimateWorkflow(WorkflowBase):

    def create(

        self,

        device_family,

        service_id,

        labor,

        parts

    ):

        return self.manager.create_quote(

            device_family,

            service_id,

            labor,

            parts

        )