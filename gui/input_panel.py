# gui/input_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QLineEdit, QMessageBox
from PyQt6.QtCore import pyqtSignal, QThread
from ncbi.fetcher import fetch_sequence, parse_fasta
from ncbi.primer_design import design_primers, find_primer_pairs
from ncbi.specificity import find_off_targets, calculate_mismatch_tm_penalty, simulate_melt_curve

class PrimerDesignWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    def __init__(self, sequence: str):
        super().__init__()
        self.sequence = sequence
    def run(self):
        try:
            fwd = design_primers(self.sequence)
            rev = design_primers(self.sequence)
            pairs = find_primer_pairs(fwd, rev)
            if not pairs:
                self.error.emit("Uygun primer çifti bulunamadı.")
                return
            self.finished.emit(pairs[0])
        except Exception as e:
            self.error.emit(str(e))

class SpecificityWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    def __init__(self, fwd: str, rev: str, target_seq: str):
        super().__init__()
        self.fwd = fwd
        self.rev = rev
        self.target = target_seq
    def run(self):
        try:
            fwd_hits = find_off_targets(self.fwd, self.target, max_mismatches=2)
            rev_hits = find_off_targets(self.rev, self.target, max_mismatches=2)
            # Basit SNP penaltısı (3' uç mismatch simülasyonu)
            fwd_pen = calculate_mismatch_tm_penalty(self.fwd, self.fwd[:-1] + "A")
            rev_pen = calculate_mismatch_tm_penalty(self.rev, self.rev[:-1] + "T")
            # Melt curve (amplicon ~100 bp varsayımı)
            amplicon = "ATCG" * 25
            melt = simulate_melt_curve(amplicon)
            self.finished.emit({
                'fwd_hits': len(fwd_hits), 'rev_hits': len(rev_hits),
                'fwd_risk': [h['risk'] for h in fwd_hits[:3]],
                'rev_risk': [h['risk'] for h in rev_hits[:3]],
                'fwd_snp_pen': fwd_pen, 'rev_snp_pen': rev_pen,
                'melt_tm': melt['tm_peak'], 'melt_gc': melt['gc_content']
            })
        except Exception as e:
            self.error.emit(str(e))

class InputPanel(QWidget):
    run_requested = pyqtSignal(dict)
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("🧬 Hedef DNA Sekansı (FASTA veya raw):"))
        self.seq_input = QTextEdit()
        self.seq_input.setPlaceholderText(">target\nATCGATCG...")
        layout.addWidget(self.seq_input)

        ncbi_layout = QHBoxLayout()
        self.ncbi_acc = QLineEdit()
        self.ncbi_acc.setPlaceholderText("NCBI Accession (örn: NM_001744.6)")
        ncbi_layout.addWidget(self.ncbi_acc)
        self.fetch_btn = QPushButton("🌐 NCBI'dan Çek")
        self.fetch_btn.clicked.connect(self._fetch_ncbi)
        ncbi_layout.addWidget(self.fetch_btn)
        self.design_btn = QPushButton("🧬 Primer Tasarla")
        self.design_btn.clicked.connect(self._design_primers)
        ncbi_layout.addWidget(self.design_btn)
        layout.addLayout(ncbi_layout)

        layout.addWidget(QLabel("Forward Primer:"))
        self.fwd_input = QTextEdit()
        layout.addWidget(self.fwd_input)
        layout.addWidget(QLabel("Reverse Primer:"))
        self.rev_input = QTextEdit()
        layout.addWidget(self.rev_input)

        spec_layout = QHBoxLayout()
        self.spec_btn = QPushButton("🔍 Spesifiklik & Melt Kontrol")
        self.spec_btn.clicked.connect(self._check_specificity)
        spec_layout.addWidget(self.spec_btn)
        spec_layout.addStretch()
        layout.addLayout(spec_layout)

        layout.addWidget(QLabel("Başlangıç DNA Kopya Sayısı:"))
        self.template_input = QLineEdit("1000")
        layout.addWidget(self.template_input)

        self.run_btn = QPushButton("🚀 Simülasyonu Başlat")
        self.run_btn.clicked.connect(self._emit_run)
        layout.addWidget(self.run_btn)
        layout.addStretch()

        self.primer_worker = None
        self.spec_worker = None

    def _fetch_ncbi(self):
        acc = self.ncbi_acc.text().strip()
        if not acc:
            QMessageBox.warning(self, "Uyarı", "Accession numarası girin.")
            return
        fasta = fetch_sequence(acc)
        if fasta:
            try:
                parsed = parse_fasta(fasta)
                self.seq_input.setPlainText(f">{parsed['id']}\n{parsed['sequence']}")
                QMessageBox.information(self, "Başarılı", f"{parsed['id']} yüklendi ({len(parsed['sequence'])} bp)")
            except Exception as e:
                QMessageBox.critical(self, "Parse Hatası", str(e))
        else:
            QMessageBox.critical(self, "Hata", "NCBI'dan veri çekilemedi.")

    def _design_primers(self):
        raw = self.seq_input.toPlainText().strip()
        if not raw:
            QMessageBox.warning(self, "Uyarı", "Önce hedef sekansı yükleyin.")
            return
        lines = raw.splitlines()
        seq = "".join(l.strip() for l in lines if not l.startswith('>')).replace(" ", "").upper()
        if len(seq) < 50:
            QMessageBox.warning(self, "Uyarı", "Sekans çok kısa (min 50 bp).")
            return
        self.design_btn.setEnabled(False)
        self.design_btn.setText("⏳ Tasarlanıyor...")
        self.primer_worker = PrimerDesignWorker(seq)
        self.primer_worker.finished.connect(self._on_primer_ready)
        self.primer_worker.error.connect(self._on_primer_error)
        self.primer_worker.start()

    def _on_primer_ready(self, best: dict):
        self.fwd_input.setPlainText(best['forward']['sequence'])
        self.rev_input.setPlainText(best['reverse']['sequence'])
        self.design_btn.setEnabled(True)
        self.design_btn.setText("🧬 Primer Tasarla")
        QMessageBox.information(self, "Primer Tasarlandı", 
            f"Amplicon: {best['amplicon_size']} bp\nTm Fwd: {best['forward']['tm']}°C | Tm Rev: {best['reverse']['tm']}°C\nΔTm: {best['tm_diff']}°C")

    def _on_primer_error(self, msg: str):
        self.design_btn.setEnabled(True)
        self.design_btn.setText("🧬 Primer Tasarla")
        QMessageBox.warning(self, "Tasarım Uyarısı", msg)

    def _check_specificity(self):
        fwd = self.fwd_input.toPlainText().strip()
        rev = self.rev_input.toPlainText().strip()
        seq = self.seq_input.toPlainText().strip()
        if not fwd or not rev or not seq:
            QMessageBox.warning(self, "Uyarı", "Sekans ve primerler gerekli.")
            return
        lines = seq.splitlines()
        target = "".join(l.strip() for l in lines if not l.startswith('>')).replace(" ", "").upper()
        if len(target) < 50:
            QMessageBox.warning(self, "Uyarı", "Hedef sekans çok kısa.")
            return
        self.spec_btn.setEnabled(False)
        self.spec_btn.setText("⏳ Kontrol Ediliyor...")
        self.spec_worker = SpecificityWorker(fwd, rev, target)
        self.spec_worker.finished.connect(self._on_spec_ready)
        self.spec_worker.error.connect(self._on_spec_error)
        self.spec_worker.start()

    def _on_spec_ready(self, res: dict):
        self.spec_btn.setEnabled(True)
        self.spec_btn.setText("🔍 Spesifiklik & Melt Kontrol")
        msg = (f"🧬 Off-Target Hits: Fwd={res['fwd_hits']} | Rev={res['rev_hits']}\n"
               f"⚠️ Risk Dağılımı: {res['fwd_risk'][:2]} / {res['rev_risk'][:2]}\n"
               f"📉 SNP ΔTm Penaltısı: Fwd={res['fwd_snp_pen']:.1f}°C | Rev={res['rev_snp_pen']:.1f}°C\n"
               f"🌡️ Melt Tm Peak: {res['melt_tm']:.1f}°C | GC: {res['melt_gc']}%\n\n"
               f"ℹ️ Not: Bu tarama girilen sekans üzerinde in-silico hızlı kontrol yapar.\n"
               f"Klinik/BLAST düzeyi spesifiklik için NCBI Primer-BLAST önerilir.")
        QMessageBox.information(self, "Spesifiklik & Melt Raporu", msg)

    def _on_spec_error(self, msg: str):
        self.spec_btn.setEnabled(True)
        self.spec_btn.setText("🔍 Spesifiklik & Melt Kontrol")
        QMessageBox.critical(self, "Kontrol Hatası", msg)

    def _emit_run(self):
        self.run_requested.emit({
            'sequence': self.seq_input.toPlainText(),
            'fwd_primer': self.fwd_input.toPlainText(),
            'rev_primer': self.rev_input.toPlainText(),
            'template_copies': self.template_input.text()
        })

    def get_params(self) -> dict:
        tpl = self.template_input.text()
        if tpl == "-" or not tpl.strip(): tpl = "1000"
        return {
            'sequence': self.seq_input.toPlainText(),
            'fwd_primer': self.fwd_input.toPlainText(),
            'rev_primer': self.rev_input.toPlainText(),
            'template_copies': tpl
        }

    def set_running_state(self, running: bool):
        self.run_btn.setEnabled(not running)
        self.run_btn.setText("⏳ Çalışıyor..." if running else "🚀 Simülasyonu Başlat")

    def set_template_enabled(self, enabled: bool):
        self.template_input.setEnabled(enabled)
        if not enabled:
            self.template_input.setText("-")
            self.template_input.setToolTip("Plate modunda kopya sayısı 'Plaka & Kuyu' sekmesinden girilir.")
        else:
            self.template_input.setText("1000")
            self.template_input.setToolTip("Tek tüp modu için başlangıç kopya sayısı")