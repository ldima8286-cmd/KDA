"""Qt shell: runs the local FastAPI server and embeds the web UI.

Falls back to the system browser if QtWebEngine is unavailable, so the app
still works on thinner installs.
"""
from __future__ import annotations

import socket
import sys
import threading
import time

import uvicorn

from .server.app import app as fastapi_app


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run_server(port: int, holder: list) -> None:
    config = uvicorn.Config(fastapi_app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    holder.append(server)
    server.run()


def _wait_for_port(port: int, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.25)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.1)
    return False


def main() -> int:
    port = _free_port()
    holder: list = []
    threading.Thread(target=_run_server, args=(port, holder), daemon=True).start()

    if not _wait_for_port(port):
        print("KDA: server failed to start", file=sys.stderr)
        return 1

    url = f"http://127.0.0.1:{port}/"

    try:
        from PySide6.QtCore import QUrl
        from PySide6.QtWidgets import QApplication, QMainWindow
        from PySide6.QtWebEngineWidgets import QWebEngineView
    except Exception:  # noqa: BLE001 - WebEngine missing
        import webbrowser

        print(f"KDA running at {url} (Ctrl+C to stop)")
        webbrowser.open(url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return 0

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("KDA")

    window = QMainWindow()
    window.setWindowTitle("KDA — esports intelligence")
    window.resize(1320, 860)
    view = QWebEngineView()
    view.setUrl(QUrl(url))
    window.setCentralWidget(view)
    window.show()

    try:
        return qt_app.exec()
    finally:
        if holder:
            holder[0].should_exit = True


if __name__ == "__main__":
    raise SystemExit(main())
