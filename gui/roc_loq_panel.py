# gui/roc_loq_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem, QLabel, QHeaderView
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from sklearn.metrics import roc_curve, auc
import numpy as np

class ROCLoQPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.figure = Figure(figsize=(6, 3.5))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Metrik", "Değer", "ISO 17025 Durum"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.status_lbl = QLabel("Hazır. Simülasyon verisi geldiğinde otomatik hesaplanır.")
        layout.addWidget(self.status_lbl)

    def update_data(self, cts: list, labels: list, efficiency: float = 0.85):
        if len(cts) < 3 or len(labels) < 3: return
        
        scores = [-c for c in cts]
        try:
            fpr, tpr, _ = roc_curve(labels, scores)
            roc_auc = auc(fpr, tpr)
        except Exception:
            roc_auc = 0.5; fpr, tpr = [0,1], [0,1]
            
        mean_ct = np.mean(cts)
        sd_ct = np.std(cts, ddof=1)
        cv_pct = (sd_ct / mean_ct * 100) if mean_ct > 0 else 999
        loq_ct = mean_ct + 2*sd_ct
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(fpr, tpr, color='#3b82f6', lw=2, label=f'ROC AUC: {roc_auc:.3f}')
        ax.plot([0,1], [0,1], '--', color='#94a3b8')
        ax.set_xlabel('False Positive Rate'); ax.set_ylabel('True Positive Rate'); ax.legend()
        self.canvas.draw()
        
        self.table.setRowCount(4)
        checks = [
            ('ROC AUC', f'{roc_auc:.3f}', '✅ PASS' if roc_auc >= 0.95 else '⚠️ REVIEW'),
            ('LoQ Ct', f'{loq_ct:.2f}', '✅ PASS' if loq_ct < 38 else '❌ FAIL'),
            ('Intra-run CV%', f'{cv_pct:.1f}%', '✅ PASS' if cv_pct <= 5 else '⚠️ HIGH'),
            ('Verimlilik (E)', f'{efficiency*100:.1f}%', '✅ PASS' if 0.9 <= efficiency <= 1.1 else '⚠️ MIQE')
        ]
        for i, (m, v, s) in enumerate(checks):
            self.table.setItem(i, 0, QTableWidgetItem(m))
            self.table.setItem(i, 1, QTableWidgetItem(v))
            item = QTableWidgetItem(s)
            item.setForeground(Qt.GlobalColor.green if 'PASS' in s else (Qt.GlobalColor.red if 'FAIL' in s else Qt.GlobalColor.darkYellow))
            self.table.setItem(i, 2, item)
        self.status_lbl.setText("✅ ISO 17025 & CLSI validasyon raporu güncellendi.")