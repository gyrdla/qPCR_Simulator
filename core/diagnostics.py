# core/diagnostics.py
import numpy as np
from typing import Dict, List, Tuple

def call_ct(ct: float, pos_cutoff: float = 35.0, indet_cutoff: float = 38.0) -> str:
    """IVD standardı Ct çağrısı"""
    if ct <= pos_cutoff:
        return "POZITIF"
    elif ct < indet_cutoff:
        return "SUPHELI"
    return "NEGATIF"

def simulate_poisson_detection(mean_copies: float, n_rep: int, p_amp: float = 0.85) -> List[bool]:
    """Düşük kopya Poisson sampling + amplifikasyon olasılığı"""
    sampled = np.random.poisson(max(0, mean_copies), n_rep)
    detected = []
    for s in sampled:
        if s == 0:
            detected.append(False)
        else:
            p_detect = 1.0 - (1.0 - p_amp)**s
            detected.append(bool(np.random.random() < p_detect))
    return detected

def estimate_lod(copies_range: List[float], n_rep: int = 20, target_prob: float = 0.95) -> Dict:
    """CLSI EP17-A2 uyumlu LoD tahmini (≥%95 tespit)"""
    curve = []
    for c in copies_range:
        dets = simulate_poisson_detection(c, n_rep)
        rate = sum(dets) / n_rep
        curve.append({'copies': c, 'rate': rate})
    lod_candidates = [r for r in curve if r['rate'] >= target_prob]
    lod = lod_candidates[0]['copies'] if lod_candidates else float('nan')
    return {'lod_copies': lod, 'curve': curve, 'target_prob': target_prob}

def calculate_diagnostic_metrics(calls: List[str], true_status: List[str]) -> Dict:
    """Sensitivite, Spesifite, FPR, FNR (IVD validasyon)"""
    tp = sum(1 for c, t in zip(calls, true_status) if c == "POZITIF" and t == "POZITIF")
    fp = sum(1 for c, t in zip(calls, true_status) if c == "POZITIF" and t == "NEGATIF")
    tn = sum(1 for c, t in zip(calls, true_status) if c == "NEGATIF" and t == "NEGATIF")
    fn = sum(1 for c, t in zip(calls, true_status) if c == "NEGATIF" and t == "POZITIF")
    
    sens = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    return {
        'sensitivity': sens, 'specificity': spec,
        'fpr': fpr, 'fnr': fnr,
        'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn
    }