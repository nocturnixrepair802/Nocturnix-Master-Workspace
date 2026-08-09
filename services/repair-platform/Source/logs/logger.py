from datetime import datetime
from pathlib import Path


class Logger:

    def __init__(self):

        self.log_folder = (
            Path(__file__).resolve().parent.parent.parent
            / "Logs"
        )

        self.log_folder.mkdir(
            exist_ok=True
        )

    def write(

        self,

        filename,

        message

    ):

        logfile = self.log_folder / filename

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        with open(
            logfile,
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                f"[{timestamp}] {message}\n"
            )