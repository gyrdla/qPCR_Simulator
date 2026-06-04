# gui/lims_export_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, QFormLayout, QMessageBox, QTextEdit
from analysis.lims_export import LIMSExporter
import datetime

class LIMSPortPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        grp = QGroupBox("📤 LIMS Export & Pipetleme Planı")
        form = QFormLayout()
        grp.setLayout(form)
        self.plan_text = QTextEdit()
        self.plan_text.setReadOnly(True)
        self.plan_text.setMaximumHeight(150)
        form.addRow("Otomatik Pipetleme Planı:", self.plan_text)
        layout.addWidget(grp)
        
        self.btn_csv = QPushButton("📋 CSV Dışa Aktar")
        self.btn_json = QPushButton("🔗 JSON (LIMS Şema)")
        layout.addWidget(self.btn_csv)
        layout.addWidget(self.btn_json)
        
        self.exporter = LIMSExporter()
        self.current_data = None
        
        self.btn_csv.clicked.connect(lambda: self._export('csv'))
        self.btn_json.clicked.connect(lambda: self._export('json'))
        layout.addStretch()

    def update_data(self, data: dict):
        self.current_data = data
        wells = data.get('parameters', {}).get('plate_wells', [])
        if not wells:
            self.plan_text.setPlainText("Plaka verisi yok. Plan oluşturulamıyor.")
            return
        plan = "=== OTOMATİK PİPETLEME PLANI (v2.1) ===\n"
        plan += f"Tarih: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        for w in wells:
            plan += f"{w['name']} ({w['type']}): {w['copies']} kopya | Hacim: {w['vol_ul']} µL | Edge Faktör: {w['thermal_factor']}\n"
        plan += "\n💡 Öneri: Master Mix'i %10 fazla hazırlayın. Kenar kuyularına buffer ekleyin."
        self.plan_text.setPlainText(plan)

    def _export(self, fmt: str):
        if not self.current_data: return QMessageBox.warning(self, "Hata", "Veri yok.")
        sid = f"session_{self.current_data.get('user', 'anon')}_{id(self.current_data)}"
        path = self.exporter.export_csv(sid, self.current_data) if fmt=='csv' else self.exporter.export_json(sid, self.current_data)
        QMessageBox.information(self, "Başarılı", f"Dosya kaydedildi:\n{path}")