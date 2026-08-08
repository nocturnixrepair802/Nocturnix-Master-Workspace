from PySide6.QtWidgets import QVBoxLayout, QWidget

"""
Base class for all application pages.
Provides a standard vertical layout.
"""

class BasePage(QWidget):

    def __init__(self):

        super().__init__()

        self.layout: QVBoxLayout = QVBoxLayout()

        self.setLayout(self.layout)
