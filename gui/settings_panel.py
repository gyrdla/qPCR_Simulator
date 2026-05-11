# gui/settings_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QDoubleSpinBox, QSpinBox, QComboBox, QGroupBox, QLabel

class SettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 1. Kit & Thermal Grubu
        grp_kit = QGroupBox("🧪 Master Mix & Thermal Profil")
        form_kit = QFormLayout()
        grp_kit.setLayout(form_kit)

        self.master_mix = QComboBox()
        self.master_mix.addItems(["Manual", "SYBR Green (Standart)", "SYBR Fast (High ROX)", "TaqMan Probe (FAM)", "Roche LC480 Probes"])
        form_kit.addRow("Master Mix Preset:", self.master_mix)

        self.thermal_profile = QComboBox()
        self.thermal_profile.addItems(["LC480 Standard", "QuantStudio Fast"])
        form_kit.addRow("Cihaz/Thermal Profil:", self.thermal_profile)

        self.cycles = QSpinBox()
        self.cycles.setRange(10, 50)
        self.cycles.setValue(40)
        form_kit.addRow("Döngü Sayısı:", self.cycles)

        self.ta_temp = QDoubleSpinBox()
        self.ta_temp.setRange(40.0, 72.0)
        self.ta_temp.setValue(60.0)
        self.ta_temp.setDecimals(1)
        self.ta_temp.setSuffix(" °C")
        form_kit.addRow("Annealing Sıcaklığı:", self.ta_temp)

        layout.addWidget(grp_kit)

        # 2. Manuel Reaktifler (Preset seçilirse worker otomatik override eder)
        grp_manual = QGroupBox("⚗️ Manuel Reaktifler (Preset yoksa aktif)")
        form_man = QFormLayout()
        grp_manual.setLayout(form_man)

        self.mg_conc = QDoubleSpinBox()
        self.mg_conc.setRange(0.5, 10.0)
        self.mg_conc.setValue(3.0)
        self.mg_conc.setDecimals(2)
        self.mg_conc.setSuffix(" mM")
        form_man.addRow("[Mg²⁺]:", self.mg_conc)

        self.dntp_conc = QDoubleSpinBox()
        self.dntp_conc.setRange(0.05, 1.0)
        self.dntp_conc.setValue(0.2)
        self.dntp_conc.setDecimals(2)
        self.dntp_conc.setSingleStep(0.05)
        self.dntp_conc.setSuffix(" mM")
        form_man.addRow("[dNTP]:", self.dntp_conc)

        self.dye_type = QComboBox()
        self.dye_type.addItems(["SYBR", "TaqMan"])
        form_man.addRow("Boyama/Prob:", self.dye_type)

        layout.addWidget(grp_manual)

        # 3. Tekrar & Varyasyon Grubu
        grp_rep = QGroupBox("📊 Teknik/Biyolojik Tekrar & Varyasyon")
        form_rep = QFormLayout()
        grp_rep.setLayout(form_rep)

        self.tech_rep = QSpinBox()
        self.tech_rep.setRange(1, 12)
        self.tech_rep.setValue(3)
        form_rep.addRow("Teknik Tekrar:", self.tech_rep)

        self.bio_rep = QSpinBox()
        self.bio_rep.setRange(1, 6)
        self.bio_rep.setValue(1)
        form_rep.addRow("Biyolojik Tekrar:", self.bio_rep)

        self.pipette_cv = QDoubleSpinBox()
        self.pipette_cv.setRange(0.0, 0.15)
        self.pipette_cv.setValue(0.02)
        self.pipette_cv.setDecimals(3)
        self.pipette_cv.setSingleStep(0.005)
        form_rep.addRow("Pipet Hatası (CV):", self.pipette_cv)

        self.thermal_sd = QDoubleSpinBox()
        self.thermal_sd.setRange(0.0, 1.0)
        self.thermal_sd.setValue(0.3)
        self.thermal_sd.setDecimals(2)
        self.thermal_sd.setSuffix(" °C")
        form_rep.addRow("Blok Uniformitesi (SD):", self.thermal_sd)

        layout.addWidget(grp_rep)
        layout.addStretch()

    def get_params(self) -> dict:
        return {
            'master_mix_preset': self.master_mix.currentText(),
            'thermal_profile': self.thermal_profile.currentText(),
            'cycles': self.cycles.value(),
            'ta_temp': self.ta_temp.value(),
            'mg_conc': self.mg_conc.value(),
            'dntp_conc': self.dntp_conc.value(),
            'dye_type': self.dye_type.currentText(),
            'tech_rep': self.tech_rep.value(),
            'bio_rep': self.bio_rep.value(),
            'pipette_cv': self.pipette_cv.value(),
            'thermal_sd': self.thermal_sd.value()
        }