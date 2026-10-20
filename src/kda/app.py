"""KDA desktop entry point: Qt shell around the sync OpenDota service."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .services import KdaService
from .ui.main_window import MainWindow
from .ui.theme import apply_theme


def main() -> int:
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("KDA")
    qt_app.setOrganizationName("KDA")

    apply_theme(qt_app)

    service = KdaService()
    window = MainWindow(service)
    window.show()

    try:
        return qt_app.exec()
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
