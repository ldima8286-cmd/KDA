"""Async remote image loading for hero icons and player avatars.

QNetworkAccessManager keeps thumbnails off the UI thread; pixmaps are cached by
URL so tables stay fast on relaunch.

QtNetwork needs a few system libraries (e.g. libkrb5 on Linux). If they are
missing the cache degrades to placeholders instead of failing to start.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QPixmap

try:  # pragma: no cover - depends on host system libraries
    from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

    HAS_QT_NETWORK = True
except ImportError:  # pragma: no cover
    QNetworkAccessManager = QNetworkReply = QNetworkRequest = None  # type: ignore[assignment]
    HAS_QT_NETWORK = False


class ImageCache(QObject):
    loaded = Signal(str, object)  # url -> QPixmap

    _instance: "ImageCache | None" = None

    @classmethod
    def instance(cls) -> "ImageCache":
        if cls._instance is None:
            cls._instance = ImageCache()
        return cls._instance

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self) if HAS_QT_NETWORK else None
        if self._nam is not None:
            self._nam.finished.connect(self._on_finished)
        self._pix: dict[str, QPixmap] = {}
        self._pending: set[str] = set()

    def cached(self, url: str | None) -> QPixmap | None:
        if not url:
            return None
        return self._pix.get(url)

    def request(self, url: str | None) -> None:
        if self._nam is None or not url or url in self._pix or url in self._pending:
            return
        self._pending.add(url)
        self._nam.get(QNetworkRequest(QUrl(url)))

    def _on_finished(self, reply: "QNetworkReply") -> None:
        url = reply.url().toString()
        self._pending.discard(url)
        try:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                pm = QPixmap()
                if pm.loadFromData(reply.readAll().data()):
                    self._pix[url] = pm
                    self.loaded.emit(url, pm)
        finally:
            reply.deleteLater()
