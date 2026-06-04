# gui/specificity_panel_v2.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QProgressBar, QGroupBox, QFormLayout)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QColor
from core.isoform_fetcher import IsoformFetcher
from analysis.specificity_v2 import SpecificityAnalyzer
import traceback

class SpecificityPanelV2(QWidget):
    primers_analyzed = pyqtSignal(str, str)
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        top = QHBoxLayout()
        top.addWidget(QLabel("NCBI Accession:"))
        self.acc_input = QLineEdit()
        top.addWidget(self.acc_input)
        self.fetch_btn = QPushButton("📥 İzomorf Çek")
        top.addWidget(self.fetch_btn)
        layout.addLayout(top)

        mid = QHBoxLayout()
        mid.addWidget(QLabel("Forward Primer:"))
        self.fwd_input = QLineEdit()
        mid.addWidget(self.fwd_input)
        mid.addWidget(QLabel("Reverse Primer:"))
        self.rev_input = QLineEdit()
        mid.addWidget(self.rev_input)
        layout.addLayout(mid)

        self.run_btn = QPushButton("🔍 Spesifiklik & Dimer Analizi Başlat")
        self.run_btn.setStyleSheet("background:#10b981; color:white; font-weight:bold; padding:8px; border-radius:6px;")
        layout.addWidget(self.run_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_lbl = QLabel("Hazır.")
        layout.addWidget(self.status_lbl)

        self.dimer_box = QGroupBox("⚠️ Primer-Dimer Kontrolü")
        dimer_layout = QFormLayout()
        self.dimer_box.setLayout(dimer_layout)
        self.lbl_dg = QLabel("-")
        self.lbl_dimer_risk = QLabel("-")
        dimer_layout.addRow("ΔG (kcal/mol):", self.lbl_dg)
        dimer_layout.addRow("Risk:", self.lbl_dimer_risk)
        layout.addWidget(self.dimer_box)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Transkript", "Yön", "Poz", "MM", "3' MM", "ΔTm (°C)", "Risk", "Hizalanma"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.fetcher = IsoformFetcher()
        self.analyzer = SpecificityAnalyzer()
        self.cached_transcripts = {}

        self.fetch_btn.clicked.connect(self._fetch_isoforms)
        self.run_btn.clicked.connect(self._run_analysis)
        self.use_in_sim_btn = QPushButton("🔄 Use in Simulation")
        self.use_in_sim_btn.setStyleSheet("background:#3b82f6; color:white; font-weight:bold; padding:6px; border-radius:6px;")
        self.use_in_sim_btn.clicked.connect(self._emit_primers)
        layout.addWidget(self.use_in_sim_btn)

    def _fetch_isoforms(self):
        acc = self.acc_input.text().strip()
        if not acc: return QMessageBox.warning(self, "Hata", "Accession gerekli.")
        try:
            self.fetch_btn.setEnabled(False); self.fetch_btn.setText("⏳ Çekiliyor...")
            self.cached_transcripts = self.fetcher.fetch_transcripts(acc)
            self.fetch_btn.setEnabled(True); self.fetch_btn.setText("📥 İzomorf Çek")
            self.status_lbl.setText(f"✅ {len(self.cached_transcripts)} transkript yüklendi.")
        except Exception as e:
            self.fetch_btn.setEnabled(True); self.fetch_btn.setText("📥 İzomorf Çek")
            self.status_lbl.setText(f"❌ {str(e)}")

    def _run_analysis(self):
        fwd, rev = self.fwd_input.text().strip(), self.rev_input.text().strip()
        if not fwd or not rev or not self.cached_transcripts:
            return QMessageBox.warning(self, "Hata", "Primerler ve transkript gerekli.")
        
        self.run_btn.setEnabled(False); self.progress.setVisible(True); self.progress.setRange(0,0)
        
        def task():
            try:
                res_fwd, dim_fwd = self.analyzer.analyze_primer_vs_transcripts(fwd, self.cached_transcripts, False)
                res_rev, dim_rev = self.analyzer.analyze_primer_vs_transcripts(rev, self.cached_transcripts, True)
                return {'fwd': res_fwd, 'rev': res_rev, 'dimer_fwd': dim_fwd, 'dimer_rev': dim_rev}
            except Exception as e: raise e

        class Worker(QThread):
            finished = pyqtSignal(dict); error = pyqtSignal(str)
            def run(self):
                try: self.finished.emit(task())
                except Exception as e: self.error.emit(traceback.format_exc())
        
        self.worker = Worker()
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_finished(self, data: dict):
        self.run_btn.setEnabled(True); self.progress.setVisible(False)
        self.status_lbl.setText(f"✅ Fwd: {len(data['fwd'])}, Rev: {len(data['rev'])} eşleşme.")
        self.lbl_dg.setText(f"{data['dimer_fwd']['delta_g']} / {data['dimer_rev']['delta_g']}")
        
        risk_text = f"{data['dimer_fwd']['risk']} / {data['dimer_rev']['risk']}"
        self.lbl_dimer_risk.setText(risk_text)
        if 'HIGH' in risk_text: self.lbl_dimer_risk.setStyleSheet("color: red; font-weight: bold;")
        else: self.lbl_dimer_risk.setStyleSheet("color: green; font-weight: bold;")
        
        hits = data['fwd'] + data['rev']
        self.table.setRowCount(len(hits))
        colors = {'HIGH': '#ef4444', 'MEDIUM': '#f59e0b', 'LOW': '#10b981'}
        for i, h in enumerate(hits):
            self.table.setItem(i, 0, QTableWidgetItem(h['transcript_id']))
            self.table.setItem(i, 1, QTableWidgetItem(h['strand']))
            self.table.setItem(i, 2, QTableWidgetItem(str(h['start_pos'])))
            self.table.setItem(i, 3, QTableWidgetItem(str(h['mismatches'])))
            self.table.setItem(i, 4, QTableWidgetItem(str(h['tail_mismatches'])))
            self.table.setItem(i, 5, QTableWidgetItem(f"{h['delta_tm']:.2f}"))
            r = QTableWidgetItem(h['risk']); r.setForeground(QColor(colors[h['risk']])); self.table.setItem(i, 6, r)
            self.table.setItem(i, 7, QTableWidgetItem(h['aligned_seq']))
    def _emit_primers(self):
        fwd = self.fwd_input.text().strip()
        rev = self.rev_input.text().strip()
        if fwd and rev:
            self.primers_analyzed.emit(fwd, rev)
        else:
            QMessageBox.warning(self, "Uyarı", "Önce primer analizi yapın.")

    def _on_error(self, msg: str):
        self.run_btn.setEnabled(True); self.progress.setVisible(False)
        self.status_lbl.setText(f"❌ {msg}")