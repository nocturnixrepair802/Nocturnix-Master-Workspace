from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatCard(QFrame):

    def __init__(self, title, value):

        super().__init__()

        self.setFrameShape(QFrame.StyledPanel)

        self.setStyleSheet("""
            QFrame{
                background:white;
                border:1px solid #D9D9D9;
                border-radius:10px;
            }
        """)

        layout = QVBoxLayout()

        self.setLayout(layout)

        title_label = QLabel(title)

        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label.setStyleSheet("""
            font-size:16px;
            color:gray;
        """)

        value_label = QLabel(str(value))

        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        value_label.setStyleSheet("""
            font-size:30px;
            font-weight:bold;
        """)

        layout.addStretch()

        layout.addWidget(title_label)

        layout.addWidget(value_label)

        layout.addStretch()
