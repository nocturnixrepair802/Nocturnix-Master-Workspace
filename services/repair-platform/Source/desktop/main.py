from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from desktop.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Nocturnix Repair Platform")
    app.setOrganizationName("Nocturnix Repair")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
