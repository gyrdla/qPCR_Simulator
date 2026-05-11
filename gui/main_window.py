# gui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from PyQt6.QtCore import Qt
from gui.input_panel import InputPanel
from gui.settings_panel import SettingsPanel
from gui.results_panel import ResultsPanel
from gui.simulation_worker import SimulationWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("qPCR Simulator v1.0")
        self.resize(1150, 780)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.input_panel = InputPanel()
        self.settings_panel = SettingsPanel()
        self.results_panel = ResultsPanel()

        # Laboratuvar iş akışına uygun sıralama
        self.tabs.addTab(self.input_panel, "1️⃣ Sekans & Primer")
        self.tabs.addTab(self.settings_panel, "2️⃣ Reaksiyon & Döngü")
        self.tabs.addTab(self.results_panel, "3️⃣ Sonuçlar & Rapor")

        self.worker = None
        self.input_panel.run_requested.connect(self._start_simulation)

    def _start_simulation(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Uyarı", "Simülasyon zaten çalışıyor.")
            return

        params = {
            **self.input_panel.get_params(),
            **self.settings_panel.get_params(),
            'primer_conc': 250e-9
        }

        self.worker = SimulationWorker(params)
        self.worker.finished.connect(self._on_simulation_finished)
        self.worker.error.connect(self._on_simulation_error)
        self.worker.progress.connect(self.results_panel.update_progress)

        self.input_panel.set_running_state(True)
        self.results_panel.clear()
        self.worker.start()

    def _on_simulation_finished(self, result: dict):
        self.input_panel.set_running_state(False)
        self.results_panel.plot_curve(result['cycles'], result['signal'], label=result.get('dye', 'Target'))
        self.results_panel.update_results(result)
        self.tabs.setCurrentIndex(2)  # Sonuçlar sekmesine otomatik geç

    def _on_simulation_error(self, msg: str):
        self.input_panel.set_running_state(False)
        QMessageBox.critical(self, "Simülasyon Hatası", msg)