# gui/async_worker.py
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
import traceback
import sys

class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str, object)

class AsyncTask(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.setAutoDelete(True)
        self.kwargs['progress_callback'] = self.signals.progress

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(f"{traceback.format_exc()}\n{str(e)}")

class TaskManager:
    def __init__(self, max_threads: int = 4):
        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(max_threads)  # ✅ PyQt6 doğru API ismi

    def start(self, fn, *args, **kwargs) -> WorkerSignals:
        worker = AsyncTask(fn, *args, **kwargs)
        self.pool.start(worker)
        return worker.signals