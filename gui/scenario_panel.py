# gui/scenario_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QSpinBox, QPushButton, QGroupBox, QFormLayout
from PyQt6.QtCore import pyqtSignal

class ScenarioPanel(QWidget):
    scenario_ready = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        grp = QGroupBox("🔬 Senaryo Simülasyonu (Kontrol vs Tedavi)")
        form = QFormLayout()
        grp.setLayout(form)

        self.base_copies = QDoubleSpinBox()
        self.base_copies.setRange(10, 100000); self.base_copies.setValue(1000)
        form.addRow("Temel Kopya Sayısı:", self.base_copies)

        self.fc_factor = QDoubleSpinBox()
        self.fc_factor.setRange(0.1, 10.0); self.fc_factor.setValue(2.0); self.fc_factor.setSingleStep(0.1)
        form.addRow("Kat Fold Değişim (FC):", self.fc_factor)

        self.bio_cv = QDoubleSpinBox()
        self.bio_cv.setRange(0.05, 0.50); self.bio_cv.setValue(0.20); self.bio_cv.setDecimals(2)
        form.addRow("Biyolojik CV (%):", self.bio_cv)

        self.tech_reps = QSpinBox()
        self.tech_reps.setRange(2, 12); self.tech_reps.setValue(3)
        form.addRow("Teknik Tekrar:", self.tech_reps)

        layout.addWidget(grp)
        self.run_btn = QPushButton("🚀 Senaryoyu Simüle Et")
        self.run_btn.clicked.connect(self._emit_scenario)
        layout.addWidget(self.run_btn)

        self.status_lbl = QLabel("Hazır. Simülasyon verisi gelince otomatik aktif olur.")
        layout.addWidget(self.status_lbl)
        layout.addStretch()

    def _emit_scenario(self):
        self.scenario_ready.emit({
            'base_copies': self.base_copies.value(),
            'fold_change': self.fc_factor.value(),
            'bio_cv': self.bio_cv.value(),
            'tech_reps': self.tech_reps.value()
        })
        self.status_lbl.setText("✅ Senaryo parametreleri simülasyona iletildi.")

    def update_data(self, efficiency: float, cts: list):
        """Simülasyon bittiğinde otomatik güncelleme (main_window'dan çağrılır)"""
        if not cts: return
        mean_ct = sum(cts)/len(cts)
        self.status_lbl.setText(f"✅ Yüklendi: E={efficiency*100:.1f}% | Ort Ct={mean_ct:.1f} | n={len(cts)}")