# gui/multiplex_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import pyqtSignal

class MultiplexPanel(QWidget):
    multiplex_config_ready = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("🎨 Multiplex Kanal Ataması (FAM / HEX / Cy5)"))
        
        # Hedef 1
        h1_layout = QHBoxLayout()
        h1_layout.addWidget(QLabel("Hedef 1 (Ana):"))
        self.cmb_ch1 = QComboBox()
        self.cmb_ch1.addItems(["FAM", "HEX", "Cy5", "YOK"])
        self.cmb_ch1.setCurrentText("FAM")
        h1_layout.addWidget(self.cmb_ch1)
        layout.addLayout(h1_layout)

        # Hedef 2
        h2_layout = QHBoxLayout()
        h2_layout.addWidget(QLabel("Hedef 2 (Ref/Kontrol):"))
        self.cmb_ch2 = QComboBox()
        self.cmb_ch2.addItems(["FAM", "HEX", "Cy5", "YOK"])
        self.cmb_ch2.setCurrentText("HEX")
        h2_layout.addWidget(self.cmb_ch2)
        layout.addLayout(h2_layout)

        # Hedef 3
        h3_layout = QHBoxLayout()
        h3_layout.addWidget(QLabel("Hedef 3 (İç Kontrol):"))
        self.cmb_ch3 = QComboBox()
        self.cmb_ch3.addItems(["FAM", "HEX", "Cy5", "YOK"])
        self.cmb_ch3.setCurrentText("Cy5")
        h3_layout.addWidget(self.cmb_ch3)
        layout.addLayout(h3_layout)

        self.apply_btn = QPushButton("✅ Multiplex Ayarlarını Uygula")
        self.apply_btn.clicked.connect(self._emit_config)
        layout.addWidget(self.apply_btn)
        
        self.status_lbl = QLabel("Hazır. Simülasyon başlatıldığında LSQ unmixing otomatik uygulanacak.")
        layout.addWidget(self.status_lbl)
        layout.addStretch()

    def _emit_config(self):
        ch1 = self.cmb_ch1.currentText()
        ch2 = self.cmb_ch2.currentText()
        ch3 = self.cmb_ch3.currentText()
        
        if ch1 == ch2 or ch1 == ch3 or ch2 == ch3:
            if ch1 != "YOK" and ch2 != "YOK" and ch3 != "YOK":
                QMessageBox.warning(self, "Uyarı", "Her hedef farklı bir kanalda olmalı (veya YOK seçilmeli).")
                return
                
        config = {
            'ch1_dye': ch1,
            'ch2_dye': ch2,
            'ch3_dye': ch3,
            'enabled': any(d != "YOK" for d in [ch1, ch2, ch3])
        }
        self.multiplex_config_ready.emit(config)
        self.status_lbl.setText(f"✅ Ayarlandı: Ch1={ch1}, Ch2={ch2}, Ch3={ch3}")