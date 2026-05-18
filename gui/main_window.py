# gui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QTabWidget, QMessageBox, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QProgressBar, QLabel, QSizePolicy, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtCore import Qt, QSize
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
import os, sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("qPCR Simulator v1.7 UI")
        self.setMinimumSize(1050, 750)
        self.resize(1200, 820)

        # 🎨 GLOBAL UI THEME
        self.setStyleSheet("""
            QMainWindow { background-color: #f8fafc; }
            QLabel { font-family: "Segoe UI", "Inter", "Arial"; font-size: 13px; color: #334155; }
            QLabel[heading="true"] { font-size: 15px; font-weight: 600; color: #0f172a; margin-bottom: 6px; }
            
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
                padding: 7px 10px; border: 1px solid #cbd5e1; border-radius: 6px;
                background: #ffffff; font-size: 13px; min-height: 26px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.15); }
            QTextEdit { border: 1px solid #cbd5e1; border-radius: 6px; background: #f8fafc; }
            
            QPushButton {
                padding: 8px 16px; border: none; border-radius: 6px;
                background: #3b82f6; color: white; font-weight: 500; font-size: 13px;
            }
            QPushButton:hover { background: #2563eb; }
            QPushButton:pressed { background: #1d4ed8; }
            QPushButton:disabled { background: #94a3b8; color: #f1f5f9; }
            QPushButton[success="true"] { background: #10b981; }
            QPushButton[success="true"]:hover { background: #059669; }
            QPushButton[warning="true"] { background: #f59e0b; }
            QPushButton[warning="true"]:hover { background: #d97706; }

            QGroupBox {
                border: 1px solid #e2e8f0; border-radius: 8px; margin-top: 12px; padding-top: 10px;
                font-weight: 600; color: #334155; background: #ffffff;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #0f172a; }

            QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 8px; background: #ffffff; margin-top: 6px; }
            QTabBar::tab {
                padding: 10px 22px; border: 1px solid #e2e8f0; border-bottom: none;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
                background: #f1f5f9; color: #475569; font-size: 13px; margin-right: 5px; font-weight: 500;
            }
            QTabBar::tab:selected { background: #ffffff; color: #0f172a; border-color: #e2e8f0; font-weight: 600; }
            QTabBar::tab:hover:!selected { background: #f8fafc; }

            QTableWidget {
                border: 1px solid #e2e8f0; border-radius: 8px; background: #ffffff;
                gridline-color: #f1f5f9; font-size: 12px; alternate-background-color: #f8fafc;
            }
            QHeaderView::section {
                background: #f1f5f9; padding: 9px; border: none; border-bottom: 2px solid #e2e8f0;
                color: #334155; font-weight: 600; font-size: 12px;
            }
            QTableWidget::item:selected { background-color: #dbeafe; color: #0f172a; }
            QTableWidget::item:hover { background-color: #f1f5f9; }

            QWidget[canvas-container="true"] { background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; }
        """)

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
        ws_layout.setContentsMargins(12, 12, 12, 12)
        ws_layout.setSpacing(10)
        top_bar = QHBoxLayout()
        self.btn_home = QPushButton("🔄 Ana Ekran")
        self.btn_home.setFixedWidth(110)
        self.btn_home.setProperty("warning", True)
        self.btn_home.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        top_bar.addWidget(self.btn_home)
        top_bar.addStretch()
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

        self.tabs.addTab(self.input_panel, "🧬 Sekans & Primer")
        self.tabs.addTab(self.settings_panel, "⚙️ Reaksiyon & Döngü")
        self.tabs.addTab(self.plate_panel, "📊 Plaka & Kuyu")
        self.tabs.addTab(self.mix_panel, "⚗️ Master Mix")
        self.tabs.addTab(self.multiplex_panel, "🎨 Multiplex")
        
        results_container = QWidget()
        res_layout = QVBoxLayout(results_container)
        res_layout.setContentsMargins(0, 0, 0, 0)
        res_layout.addWidget(self.results_panel)
        btn_layout = QHBoxLayout()
        self.validate_btn = QPushButton("📊 Validasyon Raporu")
        self.validate_btn.setProperty("success", True)
        self.validate_btn.clicked.connect(self._run_validation)
        btn_layout.addWidget(self.validate_btn)
        btn_layout.addStretch()
        res_layout.addLayout(btn_layout)
        self.tabs.addTab(results_container, "📈 Sonuçlar")

        self.loading_overlay = QWidget(self)
        self.loading_overlay.setProperty("loading-overlay", True)
        self.loading_overlay.setStyleSheet("""
            QWidget[loading-overlay="true"] { background: rgba(15, 23, 42, 0.88); border-radius: 12px; }
        """)
        self.loading_overlay.setVisible(False)
        lo_layout = QVBoxLayout(self.loading_overlay)
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setFixedHeight(6)
        self.loading_bar.setStyleSheet("QProgressBar { border: none; border-radius: 3px; background: #334155; } QProgressBar::chunk { background: #3b82f6; border-radius: 3px; }")
        self.loading_lbl = QLabel("⏳ Simülasyon çalışıyor... Lütfen bekleyin.")
        self.loading_lbl.setStyleSheet("color: #f8fafc; font-size: 15px; font-weight: 500;")
        self.loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo_layout.addStretch()
        lo_layout.addWidget(self.loading_bar, 0, Qt.AlignmentFlag.AlignCenter)
        lo_layout.addSpacing(8)
        lo_layout.addWidget(self.loading_lbl, 0, Qt.AlignmentFlag.AlignCenter)
        lo_layout.addStretch()

        self.welcome.start_requested.connect(self._setup_workspace)
        self.input_panel.run_requested.connect(self._start_simulation)
        self.mix_panel.mix_ready.connect(self._apply_mix_params)
        self.plate_panel.plate_ready.connect(self._apply_plate_params)
        self.settings_panel.optimize_requested.connect(self._run_optimizer)
        self.multiplex_panel.multiplex_config_ready.connect(self._apply_multiplex_config)

        self.sim_worker = None
        self.val_worker = None
        self.opt_worker = None
        self._mix_override = None
        self._plate_wells = None
        self._multiplex_override = None
        self.current_user = "Anonim"

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.loading_overlay.setGeometry(0, 0, self.width(), self.height())

    def _setup_workspace(self, config: dict):
        self.current_user = config.get("user", "Anonim")
        exp = config.get("exp_type", "single")
        for i in range(self.tabs.count()):
            self.tabs.setTabVisible(i, False)
        if exp == "single":
            for i in [0,1,3,4,5]: self.tabs.setTabVisible(i, True)
            self.tabs.setCurrentIndex(0)
            self.input_panel.set_template_enabled(True)
        elif exp == "plate":
            for i in [0,1,2,3,4,5]: self.tabs.setTabVisible(i, True)
            self.tabs.setCurrentIndex(2)
            self.input_panel.set_template_enabled(False)
        elif exp == "validation":
            for i in [1,3,4,5]: self.tabs.setTabVisible(i, True)
            self.tabs.setCurrentIndex(4)
        elif exp == "diagnostics":
            QMessageBox.information(self, "Bilgi", "Diagnostik/LoD modülü aktif.")
            self._setup_workspace({"user": self.current_user, "exp_type": "plate"})
            return
        self.setWindowTitle(f"qPCR Simulator v1.7 | {self.current_user} | {exp.upper()}")
        self.stack.setCurrentIndex(1)

    def _apply_mix_params(self, m: dict):
        self._mix_override = m
        QMessageBox.information(self, "Mix Uygulandı", f"Mg²⁺: {m['mg_final']} mM | dNTP: {m['dntp_final']} mM | Primer: {m['primer_final']} µM")

    def _apply_plate_params(self, wells: list):
        self._plate_wells = wells
        self.tabs.setCurrentIndex(5)
        QMessageBox.information(self, "Plaka Aktarıldı", f"{len(wells)} kuyu yapılandırması kaydedildi.")

    def _apply_multiplex_config(self, config: dict):
        self._multiplex_override = config
        QMessageBox.information(self, "Multiplex Ayarlandı", f"Ch1: {config['ch1_dye']} | Ch2: {config['ch2_dye']} | Ch3: {config['ch3_dye']}")

    def _start_simulation(self):
        if self.sim_worker and self.sim_worker.isRunning():
            QMessageBox.warning(self, "Uyarı", "Simülasyon zaten çalışıyor.")
            return
        params = {**self.input_panel.get_params(), **self.settings_panel.get_params(), 'primer_conc': 250e-9, 'user': self.current_user}
        if self._mix_override:
            m = self._mix_override
            params.update({'mg_conc': m['mg_final'], 'dntp_conc': m['dntp_final'], 'primer_conc': m['primer_final']*1e-6, 'pipette_cv': m['pipette_cv']})
        if self._plate_wells: params['plate_wells'] = self._plate_wells
        if self._multiplex_override: params['multiplex'] = self._multiplex_override
            
        self.loading_overlay.setVisible(True)
        self.sim_worker = SimulationWorker(params)
        self.sim_worker.finished.connect(self._on_sim_finished)
        self.sim_worker.error.connect(self._on_sim_error)
        self.sim_worker.progress.connect(self.results_panel.update_progress)
        self.input_panel.set_running_state(True)
        self.results_panel.clear()
        self.sim_worker.start()

    def _on_sim_finished(self, result: dict):
        self.loading_overlay.setVisible(False)
        self.input_panel.set_running_state(False)
        self.results_panel.plot_curve(result['cycles'], result['signal'], label=result.get('dye', 'Target'))
        self.results_panel.update_results(result, self.sim_worker.params)
        self.tabs.setCurrentIndex(5)

    def _on_sim_error(self, msg: str):
        self.loading_overlay.setVisible(False)
        self.input_panel.set_running_state(False)
        QMessageBox.critical(self, "Hata", msg)

    def _run_validation(self):
        if self.val_worker and self.val_worker.isRunning(): return
        s = self.settings_panel.get_params()
        m = self._mix_override
        base = {'mg': m['mg_final'] if m else s.get('mg_conc',3.0), 'dntp': m['dntp_final'] if m else s.get('dntp_conc',0.2),
                'ta': s.get('ta_temp',60.0), 'tm': 58.0, 'cycles': s.get('cycles',40),
                'primer_uM': (m['primer_final'] if m else s.get('primer_conc_uM',0.25))*1000,
                'polymerase_U': 1.0, 'dye': s.get('dye_type','SYBR'), 'copies': 1000.0, 'time_factor': 1.0, 'user': self.current_user}
        self.val_worker = ValidationWorker(base)
        self.val_worker.progress.connect(self.results_panel.update_status)
        self.val_worker.finished.connect(self._on_val_finished)
        self.val_worker.error.connect(self._on_val_error)
        self.validate_btn.setEnabled(False)
        self.validate_btn.setText("⏳ Rapor Oluşturuluyor...")
        self.val_worker.start()

    def _on_val_finished(self, pdf_path: str):
        self.validate_btn.setEnabled(True)
        self.validate_btn.setText("📊 Validasyon Raporu")
        self.results_panel.update_status(f"✅ Rapor hazır: {os.path.basename(pdf_path)}")
        QMessageBox.information(self, "Validasyon Tamamlandı", f"PDF oluşturuldu:\n{pdf_path}")

    def _on_val_error(self, msg: str):
        self.validate_btn.setEnabled(True)
        self.validate_btn.setText("📊 Validasyon Raporu")
        QMessageBox.critical(self, "Validasyon Hatası", msg)

    def _run_optimizer(self, tm_avg: float, copies: float):
        if self.opt_worker and self.opt_worker.isRunning():
            QMessageBox.warning(self, "Uyarı", "Optimizasyon zaten çalışıyor.")
            return
        self.settings_panel.optimize_btn.setEnabled(False)
        self.settings_panel.optimize_btn.setText("⏳ Taranıyor...")
        self.settings_panel.optimize_lbl.setText("⏳ Mg²⁺/Ta/Primer grid taraması başladı. ~5-10 sn sürebilir.")
        self.opt_worker = OptimizerWorker(tm_avg, copies)
        self.opt_worker.progress.connect(self.settings_panel.optimize_lbl.setText)
        self.opt_worker.finished.connect(self._on_opt_finished)
        self.opt_worker.error.connect(self._on_opt_error)
        self.opt_worker.start()

    def _on_opt_finished(self, results: list):
        self.settings_panel.optimize_btn.setEnabled(True)
        self.settings_panel.optimize_btn.setText("🚀 Optimize Et")
        if not results:
            self.settings_panel.optimize_lbl.setText("⚠️ Uygun kombinasyon bulunamadı.")
            return
        txt = "✅ MIQE Optimizasyon Önerileri (Top 3):\n"
        for i, r in enumerate(results):
            txt += f"{i+1}. Mg: {r['mg']:.2f} mM | Ta: {r['ta']:.1f}°C | Primer: {r['primer_uM']:.2f} µM → E: {r['efficiency']*100:.1f}% | Ct: {r['ct']:.1f}\n"
        txt += "\n💡 Laboratuvar önerisi: Önce 1. kombinasyonu test edin. NTC ve melt curve ile doğrulayın."
        self.settings_panel.optimize_lbl.setText(txt)
        QMessageBox.information(self, "Optimizasyon Tamamlandı", txt)

    def _on_opt_error(self, msg: str):
        self.settings_panel.optimize_btn.setEnabled(True)
        self.settings_panel.optimize_btn.setText("🚀 Optimize Et")
        self.settings_panel.optimize_lbl.setText(f"⚠️ Hata: {msg}")
        QMessageBox.critical(self, "Optimizasyon Hatası", msg)