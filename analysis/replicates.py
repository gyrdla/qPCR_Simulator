# analysis/replicates.py
import numpy as np
from typing import Dict, List, Tuple
from scipy import stats
from core.reagents import ReactionMix
from core.simulation import run_qpcr_cycles
from analysis.ct_calculator import calculate_ct
from analysis.signal import generate_signal

class ReplicateSimulator:
    def __init__(self, base_params: Dict, n_technical: int = 3, n_biological: int = 1,
                 pipette_cv: float = 0.02, thermal_sd: float = 0.3, time_factor: float = 1.0):
        self.base = base_params
        self.n_tech = n_technical
        self.n_bio = n_biological
        self.pipette_cv = pipette_cv
        self.thermal_sd = thermal_sd
        self.time_factor = time_factor

    def _apply_variation(self, copies: float, mg: float, dntp: float, ta: float) -> Tuple:
        var_copies = np.random.poisson(max(1, copies))
        var_mg = mg * np.random.normal(1.0, self.pipette_cv)
        var_dntp = dntp * np.random.normal(1.0, self.pipette_cv)
        var_ta = ta + np.random.normal(0.0, self.thermal_sd)
        return float(var_copies), float(var_mg), float(var_dntp), float(var_ta)

    def _grubbs_test(self, data: np.ndarray, alpha: float = 0.05) -> List[int]:
        """İki yönlü Grubbs outlier testi (MIQE/ISO 17025 uyumlu)"""
        if len(data) < 3:
            return []
        n = len(data)
        mean, std = np.mean(data), np.std(data, ddof=1)
        if std == 0:
            return []
        G = np.max(np.abs(data - mean)) / std
        t_crit = stats.t.ppf(1 - alpha / (2 * n), n - 2)
        G_crit = ((n - 1) / np.sqrt(n)) * np.sqrt(t_crit**2 / (n - 2 + t_crit**2))
        return [int(np.argmax(np.abs(data - mean)))] if G > G_crit else []

    def run(self) -> Dict:
        all_cts, details = [], []
        for b in range(self.n_bio):
            for t in range(self.n_tech):
                c, mg, dn, ta = self._apply_variation(
                    self.base['copies'], self.base['mg'], self.base['dntp'], self.base['ta']
                )
                mix = ReactionMix(mg, dn, self.base['primer_uM'], self.base['polymerase_U'])
                amp = run_qpcr_cycles(c, self.base['cycles'], mix, self.base['tm'], ta, self.time_factor)
                sig = generate_signal(amp, dye=self.base.get('dye', 'SYBR'))
                res = calculate_ct(sig, method='hybrid')
                all_cts.append(res['ct'])
                details.append({
                    'bio': b+1, 'tech': t+1, 'copies': c, 'ta_actual': round(ta, 2),
                    'ct': round(res['ct'], 2), 'confidence': res['confidence']
                })

        arr = np.array(all_cts)
        outlier_idx = self._grubbs_test(arr, alpha=0.05)
        clean = np.delete(arr, outlier_idx) if outlier_idx else arr
        
        mean_ct = float(np.mean(clean))
        sd_ct = float(np.std(clean, ddof=1)) if len(clean) > 1 else 0.0
        cv_pct = (sd_ct / mean_ct * 100) if mean_ct > 0 else 0.0
        
        n_clean = len(clean)
        ci_95 = float(stats.t.ppf(0.975, n_clean-1) * (sd_ct / np.sqrt(n_clean))) if n_clean > 1 else 0.0
        
        outliers = [details[i] for i in outlier_idx]
        return {
            'mean_ct': round(mean_ct, 2), 'sd_ct': round(sd_ct, 2),
            'cv_pct': round(cv_pct, 1), 'ci_95': round(ci_95, 2),
            'n_total': len(all_cts), 'n_clean': n_clean,
            'outliers': outliers, 'details': details,
            'miqe_pass': cv_pct < 5.0 and len(outliers) == 0
        }