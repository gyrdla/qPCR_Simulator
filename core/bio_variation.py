# core/bio_variation.py
import numpy as np
from typing import Dict, List, Tuple

class BioVariationEngine:
    def __init__(self, bio_cv: float = 0.20, tech_cv: float = 0.02):
        self.bio_cv = bio_cv
        self.tech_cv = tech_cv

    def generate_scenario_copies(self, base_copies: float, group_factor: float = 1.0, n_reps: int = 3) -> List[float]:
        """Log-normal biyolojik varyasyon + teknik pipetleme gürültüsü"""
        mean_log = np.log(base_copies * group_factor)
        sd_log = np.sqrt(np.log(1 + self.bio_cv**2))
        copies = np.random.lognormal(mean_log, sd_log, n_reps)
        copies *= (1 + np.random.normal(0, self.tech_cv, n_reps))
        return np.maximum(copies, 1.0).tolist()

    def calculate_loq(self, cts: List[float], target_cv: float = 0.25) -> Dict:
        """Limit of Quantification (LoQ) - %25 CV eşiği"""
        if len(cts) < 3: return {'loq_ct': float('nan'), 'cv_pct': 0, 'status': 'INSUFFICIENT_DATA'}
        mean_ct = np.mean(cts)
        sd_ct = np.std(cts, ddof=1)
        cv = (sd_ct / mean_ct) if mean_ct > 0 else float('inf')
        return {'loq_ct': round(mean_ct, 2), 'cv_pct': round(cv*100, 2), 'status': 'PASS' if cv <= target_cv else 'FAIL'}