# gui/input_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QLineEdit, QMessageBox
from PyQt6.QtCore import pyqtSignal, QThread
from ncbi.fetcher import fetch_sequence, parse_fasta
from ncbi.primer_design import design_primers, find_primer_pairs

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

        layout.addWidget(QLabel("Başlangıç DNA Kopya Sayısı:"))
        self.template_input = QLineEdit("1000")
        layout.addWidget(self.template_input)

        self.run_btn = QPushButton("🚀 Simülasyonu Başlat")
        self.run_btn.clicked.connect(self._emit_run)
        layout.addWidget(self.run_btn)
        layout.addStretch()

        self.primer_worker = None

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
            QMessageBox.critical(self, "Hata", "NCBI'dan veri çekilemedi. İnternet/accession kontrol edin.")

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
            f"Amplicon: {best['amplicon_size']} bp\n"
            f"Tm Fwd: {best['forward']['tm']}°C | Tm Rev: {best['reverse']['tm']}°C\n"
            f"ΔTm: {best['tm_diff']}°C")

    def _on_primer_error(self, msg: str):
        self.design_btn.setEnabled(True)
        self.design_btn.setText("🧬 Primer Tasarla")
        QMessageBox.warning(self, "Tasarım Uyarısı", msg)

    def _emit_run(self):
        self.run_requested.emit({
            'sequence': self.seq_input.toPlainText(),
            'fwd_primer': self.fwd_input.toPlainText(),
            'rev_primer': self.rev_input.toPlainText(),
            'template_copies': self.template_input.text()
        })

    def get_params(self) -> dict:
        return {
            'sequence': self.seq_input.toPlainText(),
            'fwd_primer': self.fwd_input.toPlainText(),
            'rev_primer': self.rev_input.toPlainText(),
            'template_copies': self.template_input.text()
        }

    def set_running_state(self, running: bool):
        self.run_btn.setEnabled(not running)
        self.run_btn.setText("⏳ Çalışıyor..." if running else "🚀 Simülasyonu Başlat")