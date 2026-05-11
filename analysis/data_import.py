# analysis/data_import.py
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import os

class qPCRDataImporter:
    """
    ABI QuantStudio, Bio-Rad CFX, Roche LC480 export verilerini parse eder.
    Otomatik sütun tespiti, baseline düzeltme ve normalizasyon uygular.
    """
    def __init__(self, filepath: str):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Dosya bulunamadı: {filepath}")
        self.filepath = filepath
        self.raw_data = None
        self.metadata = {}

    def load(self) -> pd.DataFrame:
        ext = os.path.splitext(self.filepath)[1].lower()
        sep = '\t' if ext in ('.txt', '.tsv') else ','
        try:
            self.raw_data = pd.read_csv(self.filepath, sep=sep, engine='python', on_bad_lines='skip')
        except Exception as e:
            raise ValueError(f"Dosya okunamadı: {e}")

        cols_lower = [c.lower() for c in self.raw_data.columns]
        cycle_col = next((c for c in self.raw_data.columns if 'cycle' in c.lower()), None)
        fluo_cols = [c for c in self.raw_data.columns if any(k in c.lower() for k in ['fluor', 'rfu', 'fam', 'hex', 'cy5', 'sybr', 'channel'])]

        if not cycle_col or not fluo_cols:
            raise ValueError("Cycle veya Fluorescence sütunları otomatik tespit edilemedi.")

        self.metadata['cycle_col'] = cycle_col
        self.metadata['fluo_cols'] = fluo_cols
        return self.raw_data

    def process(self, baseline_range: Tuple[int, int] = (2, 8)) -> Dict[str, List[float]]:
        if self.raw_data is None:
            self.load()

        cycles = self.raw_data[self.metadata['cycle_col']].astype(float).tolist()
        processed = {'cycles': cycles}

        for col in self.metadata['fluo_cols']:
            y = self.raw_data[col].astype(float).values
            bl_mask = (np.array(cycles) >= baseline_range[0]) & (np.array(cycles) <= baseline_range[1])
            bl_mean = np.mean(y[bl_mask]) if np.sum(bl_mask) > 2 else np.mean(y[:5])
            y_corr = y - bl_mean

            y_max = np.max(y_corr)
            y_norm = (y_corr / y_max).tolist() if y_max > 0 else y_corr.tolist()
            processed[col] = y_norm

        return processed