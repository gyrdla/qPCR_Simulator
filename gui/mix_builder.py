# gui/mix_builder.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QDoubleSpinBox, QSpinBox, QTableWidget, QTableWidgetItem, 
                             QPushButton, QLabel, QMessageBox, QHeaderView)
from PyQt6.QtCore import pyqtSignal, Qt
import numpy as np

class MixBuilderPanel(QWidget):
    mix_ready = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Üst form: Reaksiyon parametreleri
        form = QFormLayout()
        self.rxn_vol = QDoubleSpinBox()
        self.rxn_vol.setRange(5.0, 50.0)
        self.rxn_vol.setValue(20.0)
        self.rxn_vol.setSuffix(" µL")
        form.addRow("Reaksiyon Hacmi:", self.rxn_vol)

        self.n_rxn = QSpinBox()
        self.n_rxn.setRange(1, 96)
        self.n_rxn.setValue(8)
        form.addRow("Reaksiyon Sayısı:", self.n_rxn)

        self.overage = QDoubleSpinBox()
        self.overage.setRange(0.0, 30.0)
        self.overage.setValue(10.0)
        self.overage.setSuffix(" %")
        form.addRow("Fire Payı (Overage):", self.overage)
        layout.addLayout(form)

        # Bileşen tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Bileşen", "Stok Kons.", "Son Kons.", "µL/rxn", "Toplam µL", "Pipet CV%"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self._init_components()

        btn_layout = QHBoxLayout()
        self.calc_btn = QPushButton("🧮 Hacim & Hata Hesapla")
        self.calc_btn.clicked.connect(self._calculate)
        btn_layout.addWidget(self.calc_btn)

        self.apply_btn = QPushButton("✅ Simülasyona Uygula")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._apply)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)

        self.status_lbl = QLabel("Hazır")
        layout.addWidget(self.status_lbl)

    def _init_components(self):
        components = [
            ("Su (Nuclease-free)", 0.0, 0.0, 0.0),
            ("Buffer (10x)", 10.0, 1.0, 0.5),
            ("MgCl₂", 50.0, 3.0, 1.0),
            ("dNTP Mix", 10.0, 0.2, 0.8),
            ("Forward Primer", 100.0, 0.25, 1.5),
            ("Reverse Primer", 100.0, 0.25, 1.5),
            ("Probe (opsiyonel)", 100.0, 0.1, 2.0),
            ("Polimeraz", 5.0, 0.05, 2.5),
            ("Template", 0.0, 0.0, 3.0)
        ]
        self.table.setRowCount(len(components))
        for i, (name, stock, final, cv) in enumerate(components):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(str(stock)))
            self.table.setItem(i, 2, QTableWidgetItem(str(final)))
            self.table.setItem(i, 3, QTableWidgetItem("-"))
            self.table.setItem(i, 4, QTableWidgetItem("-"))
            self.table.setItem(i, 5, QTableWidgetItem(str(cv)))

    def _calculate(self):
        try:
            v_rxn = self.rxn_vol.value()
            n = self.n_rxn.value()
            overage = self.overage.value() / 100.0
            total_rxn = n * (1 + overage)
            
            vol_sum = 0.0
            rel_err_sq_sum = 0.0
            miqe_warnings = []

            for i in range(self.table.rowCount()):
                name = self.table.item(i, 0).text()
                stock = float(self.table.item(i, 1).text())
                final = float(self.table.item(i, 2).text())
                cv_pct = float(self.table.item(i, 5).text())

                if name == "Su (Nuclease-free)" or name == "Template":
                    vol = 0.0  # Su bakiyeden, template kullanıcıdan
                elif stock > 0:
                    vol = (final * v_rxn) / stock
                else:
                    vol = 0.0

                vol_sum += vol
                self.table.setItem(i, 3, QTableWidgetItem(f"{vol:.2f}"))
                self.table.setItem(i, 4, QTableWidgetItem(f"{vol * total_rxn:.2f}"))

                # Hata propagasyonu (RSS): δC/C ≈ sqrt(CV_pipet² + CV_stock²)
                if vol > 0 and stock > 0:
                    rel_err_sq_sum += (cv_pct / 100.0)**2

            # Su hacmi
            water_vol = max(0.0, v_rxn - vol_sum)
            self.table.setItem(0, 3, QTableWidgetItem(f"{water_vol:.2f}"))
            self.table.setItem(0, 4, QTableWidgetItem(f"{water_vol * total_rxn:.2f}"))

            # MIQE kontrolleri
            mg_final = float(self.table.item(2, 2).text())
            dntp_final = float(self.table.item(3, 2).text())
            primer_final = float(self.table.item(4, 2).text())
            if not (1.5 <= mg_final <= 5.0): miqe_warnings.append("Mg²⁺ MIQE aralığı dışında (1.5-5.0 mM)")
            if not (0.1 <= dntp_final <= 0.5): miqe_warnings.append("dNTP MIQE aralığı dışında (0.1-0.5 mM)")
            if not (0.1 <= primer_final <= 0.5): miqe_warnings.append("Primer MIQE aralığı dışında (0.1-0.5 µM)")
            if abs(vol_sum + water_vol - v_rxn) > 0.5: miqe_warnings.append("Toplam hacim reaksiyon hacmiyle eşleşmiyor.")

            total_cv = np.sqrt(rel_err_sq_sum) * 100.0
            msg = f"✅ Hesaplandı | Toplam Pipet CV: {total_cv:.2f}% | Fire dahil: {total_rxn:.1f} rxn"
            if miqe_warnings:
                msg += "\n⚠️ " + " | ".join(miqe_warnings)
            self.status_lbl.setText(msg)
            self.apply_btn.setEnabled(True)
            self._last_calc = {
                'rxn_vol': v_rxn, 'n_rxn': n, 'overage': overage,
                'mg_final': mg_final, 'dntp_final': dntp_final,
                'primer_final': primer_final, 'pipette_cv': total_cv / 100.0,
                'miqe_warnings': miqe_warnings
            }
        except Exception as e:
            QMessageBox.critical(self, "Hesaplama Hatası", str(e))

    def _apply(self):
        if hasattr(self, '_last_calc'):
            self.mix_ready.emit(self._last_calc)
            self.status_lbl.setText("✅ Mix parametreleri simülasyona aktarıldı.")