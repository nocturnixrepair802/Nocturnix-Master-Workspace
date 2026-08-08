from logging_system.logger import Logger


class ErrorLog(Logger):

    def error(

        self,

        message

    ):

        self.write(
            "error.log",
            message
        )