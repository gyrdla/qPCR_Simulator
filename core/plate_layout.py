# core/plate_layout.py
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import numpy as np

class WellType:
    TARGET = "TARGET"
    REFERENCE = "REFERENCE"
    NTC = "NTC"
    EMPTY = "EMPTY"

@dataclass
class Well:
    index: int
    row: int
    col: int
    well_type: str = WellType.EMPTY
    target_name: str = ""
    copies: float = 0.0
    thermal_factor: float = 1.0
    optical_factor: float = 1.0

class PlateLayout:
    """
    8/12-strip veya 96-well plate haritası.
    - Kenar (edge) kuyuları için termal gradient çarpanı
    - Optik yol varyasyonu (köşe/kenar zayıflaması)
    - Well bazlı parametre üretici
    """
    def __init__(self, format: str = "96"):
        self.format = format
        if format == "8":
            self.rows, self.cols = 1, 8
        elif format == "12":
            self.rows, self.cols = 1, 12
        elif format == "96":
            self.rows, self.cols = 8, 12
        else:
            raise ValueError("Desteklenmeyen format: '8', '12' veya '96' kullanın.")
            
        self.wells: List[Well] = []
        self._init_wells()

    def _init_wells(self):
        idx = 0
        for r in range(self.rows):
            for c in range(self.cols):
                # Edge detection: ilk/son satır veya sütun
                is_edge = (r == 0 or r == self.rows-1 or c == 0 or c == self.cols-1)
                # Termal edge factor: kenarlar ±0.3-0.5°C daha fazla varyasyon görür
                thermal_f = 1.4 if is_edge else 1.0
                # Optik factor: köşe/kenarlarda excitation/emission kaybı (~%2-4)
                optical_f = 0.97 if is_edge else 1.0
                
                self.wells.append(Well(
                    index=idx, row=r, col=c,
                    thermal_factor=thermal_f, optical_factor=optical_f
                ))
                idx += 1

    def assign(self, index: int, well_type: str, target_name: str = "", copies: float = 0.0):
        if 0 <= index < len(self.wells):
            self.wells[index].well_type = well_type
            self.wells[index].target_name = target_name
            self.wells[index].copies = copies

    def get_active_wells(self) -> List[Well]:
        return [w for w in self.wells if w.well_type in (WellType.TARGET, WellType.REFERENCE)]

    def validate(self) -> Tuple[bool, str]:
        targets = [w for w in self.wells if w.well_type == WellType.TARGET]
        refs = [w for w in self.wells if w.well_type == WellType.REFERENCE]
        ntcs = [w for w in self.wells if w.well_type == WellType.NTC]
        
        if not targets:
            return False, "En az bir TARGET kuyusu gerekli."
        if len(ntcs) == 0:
            return False, "MIQE uyumu için en az 1 NTC önerilir."
        if any(w.copies <= 0 for w in targets + refs):
            return False, "TARGET/REFERENCE kuyularında kopya sayısı > 0 olmalı."
        return True, "Layout geçerli."

    def generate_well_params(self, base_params: Dict) -> List[Dict]:
        """Her aktif kuyu için base_params'i well faktörleriyle modifiye eder"""
        well_configs = []
        for w in self.get_active_wells():
            cfg = base_params.copy()
            cfg['copies'] = w.copies
            cfg['ta_temp'] = base_params['ta_temp']  # Termal varyasyon worker'da uygulanır
            cfg['thermal_well_factor'] = w.thermal_factor
            cfg['optical_well_factor'] = w.optical_factor
            cfg['well_index'] = w.index
            cfg['well_type'] = w.well_type
            cfg['target_name'] = w.target_name
            well_configs.append(cfg)
        return well_configs