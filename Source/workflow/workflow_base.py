from abc import ABC


class WorkflowBase(ABC):

    def __init__(

        self,

        manager

    ):

        self.manager = manager

    def success(

        self,

        message,

        data=None

    ):

        return {

            "success": True,

            "message": message,

            "data": data

        }

    def failure(

        self,

        message

    ):

        return {

            "success": False,

            "message": message

        }