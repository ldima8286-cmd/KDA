"""Run blocking work off the Qt main thread.

OpenDota calls (and profile/meta computation) take hundreds of milliseconds, so
every panel submits a Worker to the global pool and reacts via queued signals.
"""
from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot


class WorkerSignals(QObject):
    ok = Signal(object)
    err = Signal(str)
    done = Signal()


class Worker(QRunnable):
    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as exc:  # noqa: BLE001 - boundary: any failure is user-facing
            self.signals.err.emit(str(exc) or type(exc).__name__)
        else:
            self.signals.ok.emit(result)
        finally:
            self.signals.done.emit()


_ACTIVE: set[Worker] = set()


def submit(
    fn: Callable[..., Any],
    on_ok: Callable[[Any], None] | None = None,
    on_err: Callable[[str], None] | None = None,
    on_done: Callable[[], None] | None = None,
    *args: Any,
    **kwargs: Any,
) -> Worker:
    worker = Worker(fn, *args, **kwargs)
    _ACTIVE.add(worker)
    if on_ok:
        worker.signals.ok.connect(on_ok)
    if on_err:
        worker.signals.err.connect(on_err)
    if on_done:
        worker.signals.done.connect(on_done)
    # Keep the runnable alive until its slot has run on the main thread.
    worker.signals.done.connect(lambda w=worker: _ACTIVE.discard(w))
    QThreadPool.globalInstance().start(worker)
    return worker
