# gui/welcome_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QGroupBox, QRadioButton, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal

class WelcomePanel(QWidget):
    start_requested = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("👤 Kullanıcı / Araştırmacı Adı:"))
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Adınız, Lab ID veya Proje Kodu")
        layout.addWidget(self.user_input)

        grp = QGroupBox("🔬 Çalışma Tipi Seçin (Sadece ilgili paneller açılacak)")
        grp_layout = QVBoxLayout()
        self.rb_single = QRadioButton("🧪 Tek Tüp / Hızlı Test (Target + Mix + Sonuç)")
        self.rb_plate = QRadioButton("📊 Strip / Plaka (Çoklu Kuyu, Edge Effect, NTC/REF)")
        self.rb_validation = QRadioButton("📈 Validasyon & Optimizasyon (Dilüsyon, Slope, R², PDF)")
        self.rb_diagnostics = QRadioButton("🦠 Diagnostik / LoD (Var-Yok, Cutoff, False±) [Yakında]")
        grp_layout.addWidget(self.rb_single)
        grp_layout.addWidget(self.rb_plate)
        grp_layout.addWidget(self.rb_validation)
        grp_layout.addWidget(self.rb_diagnostics)
        self.rb_single.setChecked(True)
        grp.setLayout(grp_layout)
        layout.addWidget(grp)

        self.start_btn = QPushButton("🚀 Çalışma Alanını Başlat")
        self.start_btn.clicked.connect(self._emit_start)
        layout.addWidget(self.start_btn)
        layout.addStretch()

    def _emit_start(self):
        user = self.user_input.text().strip() or "Anonim"
        exp_type = "single"
        if self.rb_plate.isChecked(): exp_type = "plate"
        elif self.rb_validation.isChecked(): exp_type = "validation"
        elif self.rb_diagnostics.isChecked(): exp_type = "diagnostics"
        self.start_requested.emit({"user": user, "exp_type": exp_type})