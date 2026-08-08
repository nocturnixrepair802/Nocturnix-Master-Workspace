from logging_system.logger import Logger


class ApplicationLog(Logger):

    def info(self, message):

        self.write(
            "application.log",
            f"INFO : {message}"
        )

    def warning(self, message):

        self.write(
            "application.log",
            f"WARNING : {message}"
        )