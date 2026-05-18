# gui/settings_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QDoubleSpinBox, QSpinBox, QComboBox, QGroupBox, QLabel, QCheckBox, QPushButton, QHBoxLayout, QScrollArea
from PyQt6.QtCore import pyqtSignal, Qt

class SettingsPanel(QWidget):
    optimize_requested = pyqtSignal(float, float)

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 📜 Scroll Area: İçerik sığsa bile kaymaz, sığmadığında otomatik kaydırır
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.Box.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(18)

        # Ortak input stili (daha okunabilir, tıklaması kolay)
        input_style = "padding: 8px 10px; font-size: 14px; min-height: 34px; border-radius: 6px;"

        # 1. Master Mix & Thermal
        grp_kit = QGroupBox("🧪 Master Mix & Thermal Profil")
        form_kit = QFormLayout()
        form_kit.setSpacing(12)
        form_kit.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        self.master_mix = QComboBox()
        self.master_mix.addItems(["Manual", "SYBR Green (Standart)", "SYBR Fast (High ROX)", "TaqMan Probe (FAM)", "Roche LC480 Probes"])
        self.master_mix.setStyleSheet(input_style)
        form_kit.addRow("Master Mix Preset:", self.master_mix)
        
        self.thermal_profile = QComboBox()
        self.thermal_profile.addItems(["LC480 Standard", "QuantStudio Fast"])
        self.thermal_profile.setStyleSheet(input_style)
        form_kit.addRow("Cihaz/Thermal Profil:", self.thermal_profile)
        
        self.cycles = QSpinBox()
        self.cycles.setRange(10, 50)
        self.cycles.setValue(40)
        self.cycles.setStyleSheet(input_style)
        form_kit.addRow("Döngü Sayısı:", self.cycles)
        
        self.ta_temp = QDoubleSpinBox()
        self.ta_temp.setRange(40.0, 72.0)
        self.ta_temp.setValue(60.0)
        self.ta_temp.setDecimals(1)
        self.ta_temp.setSuffix(" °C")
        self.ta_temp.setStyleSheet(input_style)
        form_kit.addRow("Annealing Sıcaklığı:", self.ta_temp)
        
        grp_kit.setLayout(form_kit)
        layout.addWidget(grp_kit)

        # 2. Manuel Reaktifler
        grp_manual = QGroupBox("⚗️ Manuel Reaktifler")
        form_man = QFormLayout()
        form_man.setSpacing(12)
        form_man.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        self.mg_conc = QDoubleSpinBox()
        self.mg_conc.setRange(0.5, 10.0)
        self.mg_conc.setValue(3.0)
        self.mg_conc.setDecimals(2)
        self.mg_conc.setSuffix(" mM")
        self.mg_conc.setStyleSheet(input_style)
        form_man.addRow("[Mg²⁺]:", self.mg_conc)
        
        self.dntp_conc = QDoubleSpinBox()
        self.dntp_conc.setRange(0.05, 1.0)
        self.dntp_conc.setValue(0.2)
        self.dntp_conc.setDecimals(2)
        self.dntp_conc.setSuffix(" mM")
        self.dntp_conc.setStyleSheet(input_style)
        form_man.addRow("[dNTP]:", self.dntp_conc)
        
        self.primer_conc_uM = QDoubleSpinBox()
        self.primer_conc_uM.setRange(0.05, 1.0)
        self.primer_conc_uM.setValue(0.25)
        self.primer_conc_uM.setDecimals(2)
        self.primer_conc_uM.setSuffix(" µM")
        self.primer_conc_uM.setStyleSheet(input_style)
        form_man.addRow("Primer Konsantrasyonu:", self.primer_conc_uM)
        
        self.dye_type = QComboBox()
        self.dye_type.addItems(["SYBR", "TaqMan"])
        self.dye_type.setStyleSheet(input_style)
        form_man.addRow("Boyama/Prob:", self.dye_type)
        
        grp_manual.setLayout(form_man)
        layout.addWidget(grp_manual)

        # 3. Teknik/Biyolojik Tekrar
        grp_rep = QGroupBox("📊 Teknik/Biyolojik Tekrar")
        form_rep = QFormLayout()
        form_rep.setSpacing(12)
        form_rep.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        self.tech_rep = QSpinBox()
        self.tech_rep.setRange(1, 12)
        self.tech_rep.setValue(3)
        self.tech_rep.setStyleSheet(input_style)
        form_rep.addRow("Teknik Tekrar:", self.tech_rep)
        
        self.bio_rep = QSpinBox()
        self.bio_rep.setRange(1, 6)
        self.bio_rep.setValue(1)
        self.bio_rep.setStyleSheet(input_style)
        form_rep.addRow("Biyolojik Tekrar:", self.bio_rep)
        
        self.pipette_cv = QDoubleSpinBox()
        self.pipette_cv.setRange(0.0, 0.15)
        self.pipette_cv.setValue(0.02)
        self.pipette_cv.setDecimals(3)
        self.pipette_cv.setStyleSheet(input_style)
        form_rep.addRow("Pipet Hatası (CV):", self.pipette_cv)
        
        self.thermal_sd = QDoubleSpinBox()
        self.thermal_sd.setRange(0.0, 1.0)
        self.thermal_sd.setValue(0.3)
        self.thermal_sd.setDecimals(2)
        self.thermal_sd.setSuffix(" °C")
        self.thermal_sd.setStyleSheet(input_style)
        form_rep.addRow("Blok Uniformitesi (SD):", self.thermal_sd)
        
        grp_rep.setLayout(form_rep)
        layout.addWidget(grp_rep)

        # 4. Diagnostik & LoD
        grp_diag = QGroupBox("🦠 Diagnostik & LoD (IVD/CLSI)")
        form_diag = QFormLayout()
        form_diag.setSpacing(12)
        form_diag.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        self.diag_enabled = QCheckBox("Diagnostik Modu Aktif Et")
        self.diag_enabled.setStyleSheet("font-size: 14px; padding: 4px;")
        form_diag.addRow("", self.diag_enabled)
        
        self.pos_cutoff = QDoubleSpinBox()
        self.pos_cutoff.setRange(20.0, 40.0)
        self.pos_cutoff.setValue(35.0)
        self.pos_cutoff.setDecimals(1)
        self.pos_cutoff.setStyleSheet(input_style)
        form_diag.addRow("Pozitif Eşik (Ct ≤):", self.pos_cutoff)
        
        self.indet_cutoff = QDoubleSpinBox()
        self.indet_cutoff.setRange(30.0, 40.0)
        self.indet_cutoff.setValue(38.0)
        self.indet_cutoff.setDecimals(1)
        self.indet_cutoff.setStyleSheet(input_style)
        form_diag.addRow("Şüpheli Aralık (Ct <):", self.indet_cutoff)
        
        self.ntc_contam = QDoubleSpinBox()
        self.ntc_contam.setRange(0.0, 0.20)
        self.ntc_contam.setValue(0.02)
        self.ntc_contam.setDecimals(3)
        self.ntc_contam.setStyleSheet(input_style)
        form_diag.addRow("NTC Kontaminasyon Olasılığı:", self.ntc_contam)
        
        grp_diag.setLayout(form_diag)
        layout.addWidget(grp_diag)

        # 5. Optik Kalibrasyon
        grp_opt = QGroupBox("🔍 Optik & Cihaz Kalibrasyonu")
        form_opt = QFormLayout()
        form_opt.setSpacing(12)
        form_opt.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        self.opt_calib_offset = QDoubleSpinBox()
        self.opt_calib_offset.setRange(-500.0, 500.0)
        self.opt_calib_offset.setValue(0.0)
        self.opt_calib_offset.setDecimals(1)
        self.opt_calib_offset.setStyleSheet(input_style)
        form_opt.addRow("RFU Kalibrasyon Offset:", self.opt_calib_offset)
        
        self.opt_calib_drift = QDoubleSpinBox()
        self.opt_calib_drift.setRange(-0.10, 0.10)
        self.opt_calib_drift.setValue(0.0)
        self.opt_calib_drift.setDecimals(3)
        self.opt_calib_drift.setStyleSheet(input_style)
        form_opt.addRow("Optik Drift (Lot/Yaşlanma):", self.opt_calib_drift)
        
        self.opt_meniscus = QDoubleSpinBox()
        self.opt_meniscus.setRange(0.0, 0.10)
        self.opt_meniscus.setValue(0.03)
        self.opt_meniscus.setDecimals(3)
        self.opt_meniscus.setStyleSheet(input_style)
        form_opt.addRow("Menisküs Kayıp Faktörü:", self.opt_meniscus)
        
        grp_opt.setLayout(form_opt)
        layout.addWidget(grp_opt)

        # 6. Optimizasyon
        grp_optimize = QGroupBox("⚙️ Hızlı MIQE Optimizasyonu")
        opt_layout = QVBoxLayout()
        opt_layout.setSpacing(10)
        grp_optimize.setLayout(opt_layout)
        
        self.optimize_btn = QPushButton("🚀 Optimize Et (Mg/Ta/Primer Taraması)")
        self.optimize_btn.setMinimumHeight(36)
        self.optimize_btn.clicked.connect(self._emit_optimize)
        opt_layout.addWidget(self.optimize_btn)
        
        self.optimize_lbl = QLabel("Hazır. MIQE PASS veren top-3 kombinasyon önerilir.")
        self.optimize_lbl.setWordWrap(True)
        self.optimize_lbl.setStyleSheet("color: #475569; font-size: 13px; line-height: 1.4;")
        opt_layout.addWidget(self.optimize_lbl)
        layout.addWidget(grp_optimize)

        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def _emit_optimize(self):
        self.optimize_requested.emit(60.0, 1000.0)

    def get_params(self) -> dict:
        return {
            'master_mix_preset': self.master_mix.currentText(),
            'thermal_profile': self.thermal_profile.currentText(),
            'cycles': self.cycles.value(),
            'ta_temp': self.ta_temp.value(),
            'mg_conc': self.mg_conc.value(),
            'dntp_conc': self.dntp_conc.value(),
            'primer_conc_uM': self.primer_conc_uM.value(),
            'dye_type': self.dye_type.currentText(),
            'tech_rep': self.tech_rep.value(),
            'bio_rep': self.bio_rep.value(),
            'pipette_cv': self.pipette_cv.value(),
            'thermal_sd': self.thermal_sd.value(),
            'diagnostics': {
                'enabled': self.diag_enabled.isChecked(),
                'pos_cutoff': self.pos_cutoff.value(),
                'indet_cutoff': self.indet_cutoff.value(),
                'ntc_contam_rate': self.ntc_contam.value()
            },
            'optics': {
                'calibration_offset': self.opt_calib_offset.value(),
                'calibration_drift': self.opt_calib_drift.value(),
                'meniscus_loss': self.opt_meniscus.value()
            }
        }