from pathlib import Path

from openpyxl import load_workbook


class WorkbookManager:

    def __init__(self, workbook_path):

        self.workbook_path = Path(workbook_path)

        self.workbook = None

    # ======================================================
    # Workbook
    # ======================================================

    def open(self):

        self.workbook = load_workbook(self.workbook_path, data_only=True)

        return self.workbook

    def save(self):

        if self.workbook is not None:

            self.workbook.save(self.workbook_path)

    def close(self):

        if self.workbook is not None:

            self.workbook.close()

            self.workbook = None
