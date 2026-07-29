from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from core.database import Database


def main() -> int:
    root = Path(__file__).resolve().parent
    database = Database(root / "data" / "nocturnix_dev.sqlite3", root / "database" / "schema.sql")
    app = QApplication(sys.argv)
    app.setApplicationName("Nocturnix Core Desktop")
    app.setStyleSheet((root / "app" / "style.qss").read_text(encoding="utf-8"))
    window = MainWindow(database)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
