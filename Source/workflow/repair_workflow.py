from workflow.workflow_base import WorkflowBase


class RepairWorkflow(WorkflowBase):

    def start(

        self,

        customer_id,

        device_id,

        service_id

    ):

        customer = self.manager.customer(

            customer_id

        )

        if customer is None:

            return self.failure(

                "Customer not found."

            )

        device = self.manager.device(

            device_id

        )

        if device is None:

            return self.failure(

                "Device not found."

            )

        service = self.manager.service(

            service_id

        )

        if service is None:

            return self.failure(

                "Service not found."

            )

        return self.success(

            "Repair workflow started.",

            {

                "customer": customer,

                "device": device,

                "service": service

            }

        )