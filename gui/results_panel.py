# gui/results_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QHBoxLayout, QFileDialog, QGroupBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import csv, os, json, datetime

class ResultsPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 🎨 Canvas Container
        canvas_box = QGroupBox("📈 Amplifikasyon Eğrisi")
        canvas_layout = QVBoxLayout(canvas_box)
        canvas_layout.setContentsMargins(8, 16, 8, 8)
        
        self.figure = Figure(figsize=(8, 3.5))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(canvas_box)
        self.canvas.setProperty("canvas-container", True)
        canvas_layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Amplifikasyon Eğrisi")
        self.ax.set_xlabel("Döngü")
        self.ax.set_ylabel("Florasan (RFU)")
        self.ax.grid(True, alpha=0.3)
        layout.addWidget(canvas_box)

        btn_layout = QHBoxLayout()
        self.btn_png = QPushButton("📊 PNG Kaydet")
        self.btn_csv = QPushButton("📋 CSV Dışa Aktar")
        self.btn_save = QPushButton("💾 Oturum Kaydet")
        self.btn_png.clicked.connect(self._save_png)
        self.btn_csv.clicked.connect(self._save_csv)
        self.btn_save.clicked.connect(self._save_session)
        btn_layout.addWidget(self.btn_png)
        btn_layout.addWidget(self.btn_csv)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

        table_box = QGroupBox("📊 Sonuç Tablosu & Metrikler")
        table_layout = QVBoxLayout(table_box)
        table_layout.setContentsMargins(8, 16, 8, 8)
        
        self.ct_table = QTableWidget()
        self.ct_table.setColumnCount(6)
        self.ct_table.setHorizontalHeaderLabels(["Hedef", "Ct", "Verimlilik", "Tm Fwd", "Tm Rev", "MIQE Durum"])
        table_layout.addWidget(self.ct_table)
        layout.addWidget(table_box)

        self.progress_label = QLabel("✅ Hazır")
        self.progress_label.setStyleSheet("color: #64748b; font-weight: 500; padding: 4px 0;")
        layout.addWidget(self.progress_label)

        self.last_result = None
        self.last_params = None

    def clear(self):
        self.ax.clear()
        self.ax.set_title("Amplifikasyon Eğrisi")
        self.ax.set_xlabel("Döngü")
        self.ax.set_ylabel("Florasan (RFU)")
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        self.ct_table.setRowCount(0)
        self.progress_label.setText("✅ Hazır")
        self.last_result = None

    def update_progress(self, cycle: int = 0, rfu: float = 0.0):
        if cycle > 0:
            self.progress_label.setText(f"⏳ Döngü {cycle} | RFU: {rfu:.1f}")
        else:
            self.progress_label.setText("⏳ Hesaplanıyor...")

    def update_status(self, msg: str):
        self.progress_label.setText(msg)

    def plot_curve(self, cycles: list, signals: list, label: str = "Target"):
        self.ax.plot(cycles, signals, marker='o', linestyle='-', label=label, markersize=3, alpha=0.85)
        self.ax.legend(fontsize=9)
        self.canvas.draw()

    def update_results(self, result: dict, params: dict = None):
        self.last_result = result
        self.last_params = params if params else {}
        self._miqe_export_val = "-"
        
        mux_cfg = self.last_params.get('multiplex', {})
        is_mux = mux_cfg.get('enabled', False)
        
        COLOR_MAP = {'FAM': '#10b981', 'HEX': '#f59e0b', 'Cy5': '#ef4444', 'TARGET': '#3b82f6', 'REFERENCE': '#8b5cf6', 'NTC': '#64748b'}
        
        if not result.get('plate_cts'):
            is_rep = result.get('is_replicate', False)
            self.ct_table.setColumnCount(6)
            self.ct_table.setHorizontalHeaderLabels(["Hedef", "Ct", "Verimlilik", "Tm Fwd", "Tm Rev", "MIQE Durum"])
            if is_rep:
                rep = result['replicates']
                miqe_txt = f"✅ MIQE PASS | Mean Ct: {rep['mean_ct']:.2f} ± {rep['sd_ct']:.2f} | CV: {rep['cv_pct']}% | n={rep['n_total']}"
                if not rep['miqe_pass']: miqe_txt = f"⚠️ MIQE FAIL | CV: {rep['cv_pct']}% | Outlier: {len(rep['outliers'])}"
                self.progress_label.setText(miqe_txt)
                self.ct_table.setRowCount(1)
                self.ct_table.setItem(0, 0, QTableWidgetItem("Target (Rep)"))
                self.ct_table.setItem(0, 1, QTableWidgetItem(f"{rep['mean_ct']:.2f} ± {rep['sd_ct']:.2f}"))
                self.ct_table.setItem(0, 2, QTableWidgetItem(f"{result.get('efficiency',0)*100:.1f}%"))
                self.ct_table.setItem(0, 3, QTableWidgetItem(f"{result.get('tm_fwd',0):.2f} °C"))
                self.ct_table.setItem(0, 4, QTableWidgetItem(f"{result.get('tm_rev',0):.2f} °C"))
                self.ct_table.setItem(0, 5, QTableWidgetItem("PASS" if rep['miqe_pass'] else "FAIL"))
            else:
                self.progress_label.setText("✅ Simülasyon tamamlandı")
                self.ct_table.setRowCount(1)
                self.ct_table.setItem(0, 0, QTableWidgetItem("Target"))
                self.ct_table.setItem(0, 1, QTableWidgetItem(f"{result.get('ct',0):.2f}"))
                self.ct_table.setItem(0, 2, QTableWidgetItem(f"{result.get('efficiency',0)*100:.1f}%"))
                self.ct_table.setItem(0, 3, QTableWidgetItem(f"{result.get('tm_fwd',0):.2f} °C"))
                self.ct_table.setItem(0, 4, QTableWidgetItem(f"{result.get('tm_rev',0):.2f} °C"))
                self.ct_table.setItem(0, 5, QTableWidgetItem("-"))
            return

        wells = self.last_params.get('plate_wells', [])
        cts = result['plate_cts']
        effs = result['plate_effs']
        plate_signals = result.get('plate_signals', [])
        cycles = result['cycles']
        
        headers = ["Kuyu", "Tip", "Kopya", "Ct", "Verimlilik", "Hacim"]
        if is_mux: headers.append("Kanal")
        self.ct_table.setColumnCount(len(headers))
        self.ct_table.setHorizontalHeaderLabels(headers)
        self.ct_table.setRowCount(len(wells))
        
        self.ax.clear()
        self.ax.set_title("Plaka Amplifikasyon Eğrileri")
        self.ax.set_xlabel("Döngü")
        self.ax.set_ylabel("Florasan (RFU)")
        self.ax.grid(True, alpha=0.3)
        
        for i, w in enumerate(wells):
            if i >= len(plate_signals): continue
            sig = plate_signals[i]
            well_name = w.get('name', f"W{i}")
            well_type = w.get('type', 'TARGET')
            
            if is_mux:
                ch_map = {0: mux_cfg.get('ch1_dye','FAM'), 1: mux_cfg.get('ch2_dye','HEX'), 2: mux_cfg.get('ch3_dye','Cy5')}
                assigned_ch = ch_map.get(i % 3, 'DEFAULT')
                color = COLOR_MAP.get(assigned_ch, '#64748b')
                label = f"{well_name} ({assigned_ch})"
            else:
                color = COLOR_MAP.get(well_type, '#64748b')
                label = f"{well_name} ({well_type})"
            
            self.ax.plot(cycles, sig, color=color, linestyle='-', label=label, alpha=0.85, linewidth=1.2)
            
            self.ct_table.setItem(i, 0, QTableWidgetItem(well_name))
            self.ct_table.setItem(i, 1, QTableWidgetItem(well_type))
            self.ct_table.setItem(i, 2, QTableWidgetItem(str(w.get('copies', 0))))
            self.ct_table.setItem(i, 3, QTableWidgetItem(f"{cts[i]:.2f}" if i < len(cts) else "-"))
            self.ct_table.setItem(i, 4, QTableWidgetItem(f"{effs[i]*100:.1f}%" if i < len(effs) else "-"))
            self.ct_table.setItem(i, 5, QTableWidgetItem(f"{w.get('vol_ul', 20.0)} µL"))
            
            if is_mux:
                ch_map = {0: mux_cfg.get('ch1_dye','FAM'), 1: mux_cfg.get('ch2_dye','HEX'), 2: mux_cfg.get('ch3_dye','Cy5')}
                assigned_ch = ch_map.get(i % 3, '-')
                self.ct_table.setItem(i, 6, QTableWidgetItem(assigned_ch))
        
        self.ax.legend(fontsize=9, loc='upper left', frameon=True)
        self.canvas.draw()
        
        r = len(wells)
        norm = result.get('normalization')
        diag = result.get('diagnostics')
        if norm:
            self.ct_table.setRowCount(r + 1)
            self.ct_table.setItem(r, 0, QTableWidgetItem("📊 ΔΔCt Normalizasyon"))
            self.ct_table.setItem(r, 1, QTableWidgetItem(f"ΔΔCt: {norm['ddct']:.3f} ± {norm['sd_ddct']:.3f}"))
            self.ct_table.setItem(r, 2, QTableWidgetItem(f"Fold Change: {norm['fc']:.3f}"))
            self.ct_table.setItem(r, 3, QTableWidgetItem(f"geNorm M: {norm.get('genorm_m', 0.0):.3f}"))
            self.ct_table.setItem(r, 4, QTableWidgetItem("✅ Stabil" if norm.get('ref_stable', True) else "⚠️ Kararsız"))
            self.ct_table.setItem(r, 5, QTableWidgetItem("MIQE Norm: PASS" if norm.get('ref_stable', True) and norm['fc'] > 0 else "FAIL"))
            r += 1
            
        if diag:
            self.ct_table.setRowCount(r + 1)
            m = diag['metrics']
            self.ct_table.setItem(r, 0, QTableWidgetItem("🦠 Diagnostik Özet"))
            self.ct_table.setItem(r, 1, QTableWidgetItem(f"Sens: {m['sensitivity']*100:.1f}% | Spec: {m['specificity']*100:.1f}%"))
            self.ct_table.setItem(r, 2, QTableWidgetItem(f"FPR: {m['fpr']*100:.1f}% | FNR: {m['fnr']*100:.1f}%"))
            self.ct_table.setItem(r, 3, QTableWidgetItem(f"LoD: {diag['lod']['lod_copies']:.1f}"))
            self.ct_table.setItem(r, 4, QTableWidgetItem("✅ IVD Uyumlu" if diag['ivd_ready'] else "⚠️ Opt. Gerekli"))
            self.ct_table.setItem(r, 5, QTableWidgetItem(f"Kesim: ≤{diag['pos_cutoff']}"))
            self._miqe_export_val = f"Diag: Sens{m['sensitivity']:.2f} Spec{m['specificity']:.2f} LoD{diag['lod']['lod_copies']:.1f}"
                
        self.progress_label.setText(f"✅ Plate simülasyonu tamamlandı ({len(wells)} kuyu)")

    def _save_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "PNG Kaydet", "qPCR_plot.png", "PNG Files (*.png)")
        if path: self.figure.savefig(path, dpi=150, bbox_inches='tight'); self.progress_label.setText(f"✅ Plot kaydedildi: {os.path.basename(path)}")

    def _save_csv(self):
        if not self.last_result: return
        path, _ = QFileDialog.getSaveFileName(self, "CSV Kaydet", "qPCR_data.csv", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='') as f:
                w = csv.writer(f); w.writerow(["Cycle", "RFU"])
                for c, r in zip(self.last_result['cycles'], self.last_result['signal']): w.writerow([c, f"{r:.2f}"])
            self.progress_label.setText(f"✅ Veri kaydedildi: {os.path.basename(path)}")

    def _save_session(self):
        if not self.last_result: self.progress_label.setText("⚠️ Kaydedilecek sonuç yok."); return
        path, _ = QFileDialog.getSaveFileName(self, "Oturum Kaydet", f"qPCR_Session_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json", "JSON Files (*.json)")
        if path:
            session = {'timestamp': datetime.datetime.now().isoformat(), 'parameters': self.last_params or {}, 'results': self.last_result, 'miqe_status': self.ct_table.item(0, 5).text() if self.ct_table.rowCount() > 0 else "-"}
            with open(path, 'w', encoding='utf-8') as f: json.dump(session, f, indent=2, default=str)
            self.progress_label.setText(f"✅ Oturum kaydedildi: {os.path.basename(path)}")