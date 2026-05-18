# gui/optimizer_worker.py
from PyQt6.QtCore import QThread, pyqtSignal
from analysis.optimizer import optimize_qpcr_params

class OptimizerWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, tm_avg: float, copies: float = 1000):
        super().__init__()
        self.tm_avg = tm_avg
        self.copies = copies

    def run(self):
        try:
            self.progress.emit("⏳ Mg²⁺ / Ta / Primer grid taraması başlatıldı...")
            results = optimize_qpcr_params(self.tm_avg, self.copies)
            self.progress.emit("✅ Optimizasyon tamamlandı.")
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))