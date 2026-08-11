from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

NAVY = "#081630"
WHITE = "#FFFFFF"
TEAL = "#00DAB7"
BLUE = "#00B4E7"

TEXT_DARK = "#152033"
TEXT_MUTED = "#667085"
SURFACE = "#F5F7FA"
SURFACE_ALT = "#EEF2F6"
BORDER = "#D7DEE8"
DANGER = "#C62828"


APP_STYLESHEET = f"""
QWidget {{
    font-family: "Aptos";
    font-size: 10pt;
    color: {TEXT_DARK};
}}

QMainWindow {{
    background-color: {SURFACE};
}}

QWidget#appHeader {{
    background-color: {NAVY};
    border: none;
}}

QLabel#appTitle {{
    color: {WHITE};
    font-size: 22px;
    font-weight: 700;
}}

QLabel#appSubtitle {{
    color: {TEAL};
    font-size: 10pt;
    font-weight: 600;
}}

QLabel#pageTitle {{
    color: {NAVY};
    font-size: 24px;
    font-weight: 700;
}}

QLabel#sectionTitle {{
    color: {NAVY};
    font-size: 16px;
    font-weight: 700;
}}

QLabel#mutedText {{
    color: {TEXT_MUTED};
}}

QListWidget#mainNavigation {{
    background-color: {NAVY};
    border: none;
    color: {WHITE};
    outline: none;
    padding-top: 10px;
}}

QListWidget#mainNavigation::item {{
    padding: 15px 18px;
    margin: 2px 8px;
    border-radius: 6px;
    color: {WHITE};
}}

QListWidget#mainNavigation::item:hover {{
    background-color: {BLUE};
    color: {NAVY};
}}

QListWidget#mainNavigation::item:selected {{
    background-color: {TEAL};
    color: {NAVY};
    font-weight: 700;
}}

QPushButton {{
    min-height: 34px;
    padding: 7px 14px;
    border-radius: 6px;
    border: 1px solid {BORDER};
    background-color: {WHITE};
    color: {NAVY};
    font-weight: 600;
}}

QPushButton:hover {{
    border-color: {BLUE};
    background-color: {SURFACE_ALT};
}}

QPushButton:pressed {{
    background-color: {BORDER};
}}

QPushButton#primaryButton {{
    background-color: {TEAL};
    color: {NAVY};
    border: 1px solid {TEAL};
    font-weight: 700;
}}

QPushButton#primaryButton:hover {{
    background-color: {BLUE};
    border-color: {BLUE};
}}

QPushButton#secondaryButton {{
    background-color: {BLUE};
    color: {NAVY};
    border: 1px solid {BLUE};
    font-weight: 700;
}}

QPushButton#secondaryButton:hover {{
    background-color: {TEAL};
    border-color: {TEAL};
}}

QPushButton#navButton {{
    text-align: left;
    padding-left: 16px;
}}

QGroupBox {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding: 14px;
    font-weight: 700;
    color: {NAVY};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}

QFrame#statCard {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

QLabel#statValue {{
    color: {NAVY};
    font-size: 30px;
    font-weight: 700;
}}

QLabel#statLabel {{
    color: {TEXT_MUTED};
    font-size: 10pt;
    font-weight: 600;
}}

QTableWidget {{
    background-color: {WHITE};
    alternate-background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    gridline-color: {BORDER};
    selection-background-color: {BLUE};
    selection-color: {NAVY};
}}

QTableWidget::item {{
    padding: 7px;
}}

QHeaderView::section {{
    background-color: {NAVY};
    color: {WHITE};
    border: none;
    border-right: 1px solid #203456;
    padding: 8px;
    font-weight: 700;
}}

QLineEdit,
QTextEdit,
QComboBox {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 6px;
    selection-background-color: {BLUE};
}}

QLineEdit:focus,
QTextEdit:focus,
QComboBox:focus {{
    border: 2px solid {BLUE};
}}

QCheckBox {{
    spacing: 8px;
}}

QStatusBar {{
    background-color: {NAVY};
    color: {WHITE};
}}

QDialog {{
    background-color: {SURFACE};
}}

QMessageBox {{
    background-color: {SURFACE};
}}
"""


def apply_theme(app: QApplication) -> None:
    app.setFont(QFont("Aptos", 10))
    app.setStyleSheet(APP_STYLESHEET)
