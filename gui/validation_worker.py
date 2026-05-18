# gui/validation_worker.py
import datetime
from PyQt6.QtCore import QThread, pyqtSignal
from analysis.validation_suite import ValidationSuite
import os

class ValidationWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)  # PDF dosya yolu
    error = pyqtSignal(str)

    def __init__(self, base_params: dict):
        super().__init__()
        self.base_params = base_params

    def run(self):
        try:
            self.progress.emit("⏳ 10x dilüsyon serisi hesaplanıyor...")
            suite = ValidationSuite(self.base_params)
            dil_res = suite.run_dilution_series()

            if 'error' in dil_res:
                self.error.emit(dil_res['error'])
                return

            self.progress.emit("⏳ Mg²⁺ taraması yapılıyor...")
            scan_res = suite.run_parameter_scan('mg', [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5])

            self.progress.emit("📄 PDF raporu oluşturuluyor...")
            pdf_name = f"qPCR_Validation_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            pdf_path = suite.generate_pdf_report(dil_res, scan_res, pdf_name)

            self.finished.emit(os.path.abspath(pdf_path))
        except Exception as e:
            self.error.emit(str(e))