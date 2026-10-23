"""Async remote image loading for hero icons and player avatars.

QNetworkAccessManager keeps thumbnails off the UI thread; pixmaps are cached by
URL so tables stay fast on relaunch.

QtNetwork needs a few system libraries (e.g. libkrb5 on Linux). If they are
missing the cache degrades to placeholders instead of failing to start.
"""
from __future__ import annotations

import urllib.error
import urllib.request

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QUrl, Signal
from PySide6.QtGui import QPixmap

try:  # pragma: no cover - depends on host system libraries
    from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

    HAS_QT_NETWORK = True
except ImportError:  # pragma: no cover
    QNetworkAccessManager = QNetworkReply = QNetworkRequest = None  # type: ignore[assignment]
    HAS_QT_NETWORK = False


class _UrllibFetch(QRunnable):
    """Download an image off the UI thread when QtNetwork is unavailable."""

    def __init__(self, cache: "ImageCache", url: str) -> None:
        super().__init__()
        self._cache = cache
        self._url = url

    def run(self) -> None:  # pragma: no cover - network timing
        try:
            request = urllib.request.Request(
                self._url, headers={"User-Agent": "KDA/1.0 (+desktop)"}
            )
            with urllib.request.urlopen(request, timeout=15) as reply:
                data = reply.read()
        except (urllib.error.URLError, OSError, ValueError):
            self._cache._pending.discard(self._url)
            return
        self._cache._fetched.emit(self._url, data)


class ImageCache(QObject):
    loaded = Signal(str, object)  # url -> QPixmap
    _fetched = Signal(str, object)  # url -> bytes (fallback worker thread)

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
        self._fetched.connect(self._on_fetched)
        self._pix: dict[str, QPixmap] = {}
        self._pending: set[str] = set()

    def cached(self, url: str | None) -> QPixmap | None:
        if not url:
            return None
        return self._pix.get(url)

    def request(self, url: str | None) -> None:
        if not url or url in self._pix or url in self._pending:
            return
        self._pending.add(url)
        if self._nam is not None:
            self._nam.get(QNetworkRequest(QUrl(url)))
        else:
            # Some Linux runtimes cannot load QtNetwork (missing krb5 libs);
            # fall back to a stdlib download so artwork still appears.
            QThreadPool.globalInstance().start(_UrllibFetch(self, url))

    def _on_fetched(self, url: str, data: object) -> None:
        self._pending.discard(url)
        pixmap = QPixmap()
        if isinstance(data, (bytes, bytearray)) and pixmap.loadFromData(bytes(data)):
            self._pix[url] = pixmap
            self.loaded.emit(url, pixmap)

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
