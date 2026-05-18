# gui/plate_editor.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QComboBox, QDoubleSpinBox, QSpinBox, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt

class PlateEditorPanel(QWidget):
    plate_ready = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(12)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Format:"))
        self.fmt_cb = QComboBox()
        self.fmt_cb.addItems(["8-Strip", "12-Strip", "96-Well Plate"])
        self.fmt_cb.currentTextChanged.connect(self._build_grid)
        top_layout.addWidget(self.fmt_cb)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.table.setMinimumHeight(200)
        layout.addWidget(self.table)

        self.edit_layout = QHBoxLayout()
        self.edit_layout.addWidget(QLabel("Seçili Kuyu:"))
        self.lbl_well = QLabel("-")
        self.edit_layout.addWidget(self.lbl_well)
        
        self.edit_layout.addWidget(QLabel("İsim:"))
        self.edt_name = QLineEdit()
        self.edit_layout.addWidget(self.edt_name)
        
        self.edit_layout.addWidget(QLabel("Tip:"))
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["TARGET", "REFERENCE", "NTC"])
        self.edit_layout.addWidget(self.cmb_type)
        
        self.edit_layout.addWidget(QLabel("Kopya:"))
        self.edt_copies = QSpinBox()
        self.edt_copies.setRange(0, 1000000)
        self.edt_copies.setValue(1000)
        self.edt_copies.setSingleStep(10)
        self.edit_layout.addWidget(self.edt_copies)
        
        self.edit_layout.addWidget(QLabel("Hacim:"))
        self.edt_vol = QDoubleSpinBox()
        self.edt_vol.setRange(0.0, 100.0)
        self.edt_vol.setDecimals(2)
        self.edt_vol.setValue(20.0)
        self.edt_vol.setSuffix(" µL")
        self.edit_layout.addWidget(self.edt_vol)
        
        self.btn_apply = QPushButton("✅ Uygula")
        self.btn_apply.clicked.connect(self._apply_well)
        self.edit_layout.addWidget(self.btn_apply)
        
        self.btn_export = QPushButton("📤 Simülasyona Aktar")
        self.btn_export.clicked.connect(self._export_plate)
        self.edit_layout.addWidget(self.btn_export)
        layout.addLayout(self.edit_layout)

        self.status_lbl = QLabel("Hazır. Kuyu yapılandırın ve aktarın.")
        layout.addWidget(self.status_lbl)
        layout.addStretch()
        self.setLayout(layout)

        self.well_data = {}
        self._build_grid("8-Strip")

    def _build_grid(self, fmt: str):
        rows, cols = (1, 8) if fmt == "8-Strip" else (1, 12) if fmt == "12-Strip" else (8, 12)
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.well_data = {}
        for r in range(rows):
            for c in range(cols):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)
                self.well_data[(r,c)] = {'name': '', 'type': 'TARGET', 'copies': 1000, 'vol_ul': 20.0}

    def _on_cell_clicked(self, row: int, col: int):
        self.lbl_well.setText(f"{chr(65+row)}{col+1}")
        d = self.well_data.get((row,col), {})
        self.edt_name.setText(d.get('name', ''))
        self.cmb_type.setCurrentText(d.get('type', 'TARGET'))
        self.edt_copies.setValue(d.get('copies', 1000))
        self.edt_vol.setValue(d.get('vol_ul', 20.0))

    def _apply_well(self):
        sel = self.table.selectedItems()
        if not sel:
            QMessageBox.warning(self, "Uyarı", "Önce bir kuyu seçin.")
            return
        r, c = sel[0].row(), sel[0].column()
        w_type = self.cmb_type.currentText()
        w_copies = 0 if w_type == "NTC" else self.edt_copies.value()
        
        self.well_data[(r,c)] = {
            'name': self.edt_name.text().strip() or f"W{r}{c}",
            'type': w_type,
            'copies': w_copies,
            'vol_ul': self.edt_vol.value()
        }
        sel[0].setText(f"{self.well_data[(r,c)]['name']}\n{w_copies} kopya")
        sel[0].setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setText(f"✅ {self.lbl_well.text()} yapılandırıldı.")

    def _export_plate(self):
        wells = []
        for (r,c), d in self.well_data.items():
            if d['name']:
                is_edge = (r == 0 or c == 0)
                wells.append({
                    'row': r, 'col': c, 'name': d['name'], 'type': d['type'],
                    'copies': d['copies'], 'vol_ul': d['vol_ul'],
                    'thermal_factor': 1.4 if is_edge else 1.0,
                    'optical_factor': 0.97 if is_edge else 1.0
                })
        if not wells:
            QMessageBox.warning(self, "Uyarı", "En az bir kuyu yapılandırın.")
            return
        self.plate_ready.emit(wells)
        self.status_lbl.setText(f"✅ {len(wells)} kuyu simülasyona aktarıldı.")