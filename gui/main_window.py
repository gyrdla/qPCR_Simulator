# gui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QTabWidget, QMessageBox, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QProgressBar, QLabel, QSizePolicy, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from gui.welcome_panel import WelcomePanel
from gui.input_panel import InputPanel
from gui.settings_panel import SettingsPanel
from gui.plate_editor import PlateEditorPanel
from gui.mix_builder import MixBuilderPanel
from gui.results_panel import ResultsPanel
from gui.simulation_worker import SimulationWorker
from gui.validation_worker import ValidationWorker
from gui.optimizer_worker import OptimizerWorker
from gui.multiplex_panel import MultiplexPanel
from gui.specificity_panel_v2 import SpecificityPanelV2
from gui.scenario_panel import ScenarioPanel
from gui.roc_loq_panel import ROCLoQPanel
from gui.lims_export_panel import LIMSPortPanel
from gui.async_worker import TaskManager
from core.config import AppConfig
from core.project_state import ProjectState
from analysis.report_generator import ReportGenerator
from gui.error_logger import ErrorLogger
import os, sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("qPCR Simulator v2.1 Digital Twin")
        self.setMinimumSize(1100, 800); self.resize(1250, 850)

        # ✅ QFont uyarısını tamamen engelle
        os.environ["QT_QPA_FONTDIR"] = "" # Varsayılan font yolunu boşalt (sistem fontu kullanır)
        
        self.config = AppConfig()
        self.state = ProjectState(self.config)
        self.task_mgr = TaskManager(max_threads=4)
        self.report_gen = ReportGenerator()
        self.error_logger = ErrorLogger()

        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "icon.png"))
        if os.path.exists(icon_path):
            px = QPixmap(icon_path).scaled(QSize(64, 64), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.setWindowIcon(QIcon(px))

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.welcome = WelcomePanel()
        self.stack.addWidget(self.welcome)

        self.workspace = QWidget()
        ws_layout = QVBoxLayout(self.workspace)
        ws_layout.setContentsMargins(12, 12, 12, 12); ws_layout.setSpacing(10)
        top_bar = QHBoxLayout()
        self.btn_home = QPushButton("🔄 Ana Ekran"); self.btn_home.setFixedWidth(110)
        self.btn_home.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        top_bar.addWidget(self.btn_home); top_bar.addStretch()
        ws_layout.addLayout(top_bar)
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        ws_layout.addWidget(self.tabs)
        self.stack.addWidget(self.workspace)

        self.input_panel = InputPanel()
        self.settings_panel = SettingsPanel()
        self.plate_panel = PlateEditorPanel()
        self.mix_panel = MixBuilderPanel()
        self.results_panel = ResultsPanel()
        self.multiplex_panel = MultiplexPanel()
        self.specificity_panel = SpecificityPanelV2()
        self.scenario_panel = ScenarioPanel()
        self.roc_panel = ROCLoQPanel()
        self.lims_panel = LIMSPortPanel()

        self.tabs.addTab(self.input_panel, "🧬 Sekans & Primer")
        self.tabs.addTab(self.settings_panel, "⚙️ Reaksiyon & Döngü")
        self.tabs.addTab(self.plate_panel, "📊 Plaka & Kuyu")
        self.tabs.addTab(self.mix_panel, "⚗️ Master Mix")
        self.tabs.addTab(self.multiplex_panel, "🎨 Multiplex")
        self.tabs.addTab(self.specificity_panel, "🔬 İzomorf & Spesifiklik")
        self.tabs.addTab(self.scenario_panel, "🧪 Senaryo Modu")
        self.tabs.addTab(self.roc_panel, "📈 ROC & LoQ")
        self.tabs.addTab(self.lims_panel, "📤 LIMS Export")
        self.tabs.addTab(self.results_panel, "📊 Sonuçlar & Rapor")

        self.specificity_panel.primers_analyzed.connect(self._sync_primers_to_input)

        self.loading_overlay = QWidget(self)
        self.loading_overlay.setStyleSheet("background: rgba(15, 23, 42, 0.88); border-radius: 12px;")
        self.loading_overlay.setVisible(False)
        lo = QVBoxLayout(self.loading_overlay)
        self.loading_bar = QProgressBar(); self.loading_bar.setRange(0,0); self.loading_bar.setTextVisible(False); self.loading_bar.setFixedHeight(6)
        self.loading_bar.setStyleSheet("QProgressBar{border:none;border-radius:3px;background:#334155}QProgressBar::chunk{background:#3b82f6}")
        self.loading_lbl = QLabel("⏳ İşlem çalışıyor..."); self.loading_lbl.setStyleSheet("color:#f8fafc;font-size:15px;font-weight:500"); self.loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.addStretch(); lo.addWidget(self.loading_bar, 0, Qt.AlignmentFlag.AlignCenter); lo.addWidget(self.loading_lbl, 0, Qt.AlignmentFlag.AlignCenter); lo.addStretch()

        self.welcome.start_requested.connect(self._setup_workspace)
        self.input_panel.run_requested.connect(self._start_simulation)
        self.mix_panel.mix_ready.connect(self._apply_mix_params)
        self.plate_panel.plate_ready.connect(self._apply_plate_params)
        self.settings_panel.optimize_requested.connect(self._run_optimizer_async)
        self.multiplex_panel.multiplex_config_ready.connect(self._apply_multiplex_config)
        self.scenario_panel.scenario_ready.connect(self._load_scenario)

        self.sim_worker = None
        self.val_worker = None
        self.opt_worker = None
        self._mix_override = None; self._plate_wells = None; self._multiplex_override = None
        self.current_user = "Anonim"; self.current_session_id = None; self._scenario_data = None

    def closeEvent(self, event):
        """✅ Zorunlu Thread Temizliği"""
        # Task pool'u durdur
        try: self.task_mgr.pool.clear()
        except: pass
        
        # Worker'ları zorla durdur
        workers = [self.sim_worker, self.val_worker, self.opt_worker]
        for w in workers:
            if w and w.isRunning():
                w.terminate() # Hemen öldür
                w.wait()      # Bitmesini bekle
        event.accept()

    def resizeEvent(self, e): super().resizeEvent(e); self.loading_overlay.setGeometry(0,0,self.width(),self.height())

    def _setup_workspace(self, cfg: dict):
        self.current_user = cfg.get("user", "Anonim")
        for i in range(self.tabs.count()): self.tabs.setTabVisible(i, True)
        self.tabs.setCurrentIndex(8)
        self.setWindowTitle(f"qPCR Simulator v2.1 | {self.current_user}")
        self.stack.setCurrentIndex(1)
        self.current_session_id = f"{self.current_user}_run"

    def _sync_primers_to_input(self, fwd: str, rev: str):
        self.input_panel.fwd_input.setPlainText(fwd)
        self.input_panel.rev_input.setPlainText(rev)
        self.tabs.setCurrentIndex(0)

    def _apply_mix_params(self, m: dict): self._mix_override = m
    def _apply_plate_params(self, w: list): self._plate_wells = w
    def _apply_multiplex_config(self, c: dict): self._multiplex_override = c
    def _load_scenario(self, c: dict): self._scenario_data = c

    def _start_simulation(self):
        if self.sim_worker and self.sim_worker.isRunning(): return QMessageBox.warning(self, "Uyarı", "Çalışıyor.")
        fwd = self.input_panel.fwd_input.toPlainText().strip()
        rev = self.input_panel.rev_input.toPlainText().strip()
        if not fwd or not rev:
            spec_fwd = self.specificity_panel.fwd_input.text().strip()
            spec_rev = self.specificity_panel.rev_input.text().strip()
            if spec_fwd and spec_rev:
                self._sync_primers_to_input(spec_fwd, spec_rev)
                fwd, rev = spec_fwd, spec_rev
            else:
                return QMessageBox.critical(self, "Hata", "Forward ve Reverse primer sekansları boş bırakılamaz.")
        
        params = {**self.input_panel.get_params(), **self.settings_panel.get_params(), 'primer_conc': 250e-9, 'user': self.current_user, 'fwd_primer': fwd, 'rev_primer': rev}
        if self._mix_override:
            m = self._mix_override
            params.update({'mg_conc': m['mg_final'], 'dntp_conc': m['dntp_final'], 'primer_conc': m['primer_final']*1e-6, 'pipette_cv': m['pipette_cv']})
        if self._plate_wells: params['plate_wells'] = self._plate_wells
        if self._multiplex_override: params['multiplex'] = self._multiplex_override
        if self._scenario_data: params['scenario'] = self._scenario_data
            
        self.loading_overlay.setVisible(True)
        self.sim_worker = SimulationWorker(params)
        self.sim_worker.finished.connect(self._on_sim_finished)
        self.sim_worker.error.connect(self._on_sim_error)
        self.sim_worker.progress.connect(self.results_panel.update_progress)
        self.input_panel.set_running_state(True); self.results_panel.clear(); self.sim_worker.start()

    def _on_sim_finished(self, result: dict):
        self.loading_overlay.setVisible(False); self.input_panel.set_running_state(False)
        self.results_panel.plot_curve(result['cycles'], result['signal'], label=result.get('dye', 'Target'))
        self.results_panel.update_results(result, self.sim_worker.params)
        self.tabs.setCurrentIndex(8)
        
        if self.current_session_id:
            save_path = self.state.create_session(self.current_session_id)
            self.state.save(save_path, {'parameters': self.sim_worker.params, 'results': result})
            cts = result.get('plate_cts', [result.get('ct', 0)])
            labels = [1 if c < 38 else 0 for c in cts]
            eff = result.get('efficiency', 0.8)
            if hasattr(self.roc_panel, 'update_data'): self.roc_panel.update_data(cts, labels, eff)
            if hasattr(self.lims_panel, 'update_data'): self.lims_panel.update_data({'user': self.current_user, 'parameters': self.sim_worker.params, 'results': result})
            if hasattr(self.scenario_panel, 'update_data'): self.scenario_panel.update_data(eff, cts)
            class ReportWorker(QThread):
                finished = pyqtSignal(str)
                def run(self):
                    html = self.report_gen.generate_html(self.session_id, self.params, {'Verimlilik': f"{self.eff*100:.1f}%", 'Ct': f"{self.ct:.2f}"})
                    self.report_gen.generate_pdf(html)
                    self.finished.emit(html)
                def __init__(self, gen, sid, params, eff, ct):
                    super().__init__(); self.report_gen = gen; self.session_id = sid; self.params = params; self.eff = eff; self.ct = ct
            rpt = ReportWorker(self.report_gen, self.current_session_id, self.sim_worker.params, eff, result.get('ct',0))
            rpt.finished.connect(lambda p: self.results_panel.update_status(f"✅ Rapor hazır: {os.path.basename(p)}"))
            rpt.start()

    def _on_sim_error(self, msg: str): 
        self.loading_overlay.setVisible(False); self.input_panel.set_running_state(False)
        self.error_logger.log(Exception(msg), "Simulation Error")
        QMessageBox.critical(self, "Hata", f"{msg}\n\n📁 Detaylı log: {self.error_logger.get_latest_log()}")

    def _run_optimizer_async(self, tm_avg: float, copies: float, **kwargs):
        self.loading_overlay.setVisible(True); self.loading_lbl.setText("⏳ Grid Tarama...")
        def run_opt(**kw):
            w = OptimizerWorker(tm_avg, copies); res=[]; w.finished.connect(lambda r: res.extend(r)); w.start(); w.wait(); return res
        sig = self.task_mgr.start(run_opt); sig.finished.connect(self._on_opt_finished_async); sig.error.connect(self._on_opt_error_async)

    def _on_opt_finished_async(self, results: list):
        self.loading_overlay.setVisible(False)
        if not results: 
            self.settings_panel.optimize_lbl.setText("⚠️ MIQE aralığında kombinasyon bulunamadı.")
            return
        txt = "✅ MIQE Top 3:\n" + "".join(f"{i+1}. Mg:{r['mg']:.2f}mM Ta:{r['ta']:.1f}°C P:{r['primer_uM']:.2f}µM → E:{r['efficiency']*100:.1f}%\n" for i,r in enumerate(results))
        self.settings_panel.optimize_lbl.setText(txt); QMessageBox.information(self, "Optimizasyon Tamamlandı", txt)
    def _on_opt_error_async(self, msg: str): 
        self.loading_overlay.setVisible(False)
        self.error_logger.log(Exception(msg), "Optimizer Error")
        self.settings_panel.optimize_lbl.setText(f"⚠️ {msg}")