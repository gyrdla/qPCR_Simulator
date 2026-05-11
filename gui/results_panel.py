# gui/results_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QHBoxLayout, QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import csv, os

class ResultsPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Amplifikasyon Eğrisi")
        self.ax.set_xlabel("Döngü")
        self.ax.set_ylabel("Florasan (RFU)")
        self.ax.grid(True)

        btn_layout = QHBoxLayout()
        self.btn_png = QPushButton("📊 PNG Kaydet")
        self.btn_csv = QPushButton("📋 CSV Dışa Aktar")
        self.btn_png.clicked.connect(self._save_png)
        self.btn_csv.clicked.connect(self._save_csv)
        btn_layout.addWidget(self.btn_png)
        btn_layout.addWidget(self.btn_csv)
        layout.addLayout(btn_layout)

        self.ct_table = QTableWidget()
        self.ct_table.setColumnCount(6)
        self.ct_table.setHorizontalHeaderLabels(["Hedef", "Ct", "Verimlilik", "Tm Fwd", "Tm Rev", "MIQE Durum"])
        layout.addWidget(self.ct_table)

        self.progress_label = QLabel("Hazır")
        layout.addWidget(self.progress_label)

        self.last_result = None

    def clear(self):
        self.ax.clear()
        self.ax.set_title("Amplifikasyon Eğrisi")
        self.ax.set_xlabel("Döngü")
        self.ax.set_ylabel("Florasan (RFU)")
        self.ax.grid(True)
        self.canvas.draw()
        self.ct_table.setRowCount(0)
        self.progress_label.setText("Hazır")
        self.last_result = None

    def update_progress(self, cycle: int, rfu: float):
        """Worker'dan gelen döngü ilerlemesini gösterir"""
        if cycle > 0:
            self.progress_label.setText(f"⏳ Döngü {cycle} | RFU: {rfu:.1f}")
        else:
            self.progress_label.setText("⏳ Tekrarlar hesaplanıyor...")

    def plot_curve(self, cycles: list, signals: list, label: str = "Target"):
        self.ax.plot(cycles, signals, marker='o', linestyle='-', label=label, markersize=3, alpha=0.8)
        self.ax.legend()
        self.canvas.draw()

    def update_results(self, result: dict):
        self.last_result = result
        is_rep = result.get('is_replicate', False)
        
        if is_rep:
            rep = result['replicates']
            miqe_txt = f"✅ MIQE PASS | Mean Ct: {rep['mean_ct']:.2f} ± {rep['sd_ct']:.2f} | CV: {rep['cv_pct']}% | n={rep['n_total']}"
            if not rep['miqe_pass']:
                miqe_txt = f"⚠️ MIQE FAIL | CV: {rep['cv_pct']}% | Outlier: {len(rep['outliers'])}"
            self.progress_label.setText(miqe_txt)
            
            self.ct_table.setRowCount(1)
            self.ct_table.setItem(0, 0, QTableWidgetItem("Target (Rep)"))
            self.ct_table.setItem(0, 1, QTableWidgetItem(f"{rep['mean_ct']:.2f} ± {rep['sd_ct']:.2f}"))
            self.ct_table.setItem(0, 2, QTableWidgetItem(f"{result.get('efficiency',0)*100:.1f}%"))
            self.ct_table.setItem(0, 3, QTableWidgetItem(f"{result.get('tm_fwd',0):.2f} °C"))
            self.ct_table.setItem(0, 4, QTableWidgetItem(f"{result.get('tm_rev',0):.2f} °C"))
            self.ct_table.setItem(0, 5, QTableWidgetItem("PASS" if rep['miqe_pass'] else "FAIL"))
        else:
            self.progress_label.setText("✅ Tekli simülasyon tamamlandı")
            self.ct_table.setRowCount(1)
            self.ct_table.setItem(0, 0, QTableWidgetItem("Target"))
            self.ct_table.setItem(0, 1, QTableWidgetItem(f"{result.get('ct',0):.2f}"))
            self.ct_table.setItem(0, 2, QTableWidgetItem(f"{result.get('efficiency',0)*100:.1f}%"))
            self.ct_table.setItem(0, 3, QTableWidgetItem(f"{result.get('tm_fwd',0):.2f} °C"))
            self.ct_table.setItem(0, 4, QTableWidgetItem(f"{result.get('tm_rev',0):.2f} °C"))
            self.ct_table.setItem(0, 5, QTableWidgetItem("-"))

    def _save_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "PNG Kaydet", "qPCR_plot.png", "PNG Files (*.png)")
        if path:
            self.figure.savefig(path, dpi=150, bbox_inches='tight')
            self.progress_label.setText(f"✅ Plot kaydedildi: {os.path.basename(path)}")

    def _save_csv(self):
        if not self.last_result: return
        path, _ = QFileDialog.getSaveFileName(self, "CSV Kaydet", "qPCR_data.csv", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(["Cycle", "RFU"])
                for c, r in zip(self.last_result['cycles'], self.last_result['signal']):
                    w.writerow([c, f"{r:.2f}"])
            self.progress_label.setText(f"✅ Veri kaydedildi: {os.path.basename(path)}")