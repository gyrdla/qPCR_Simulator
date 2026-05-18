# core/housekeeping.py
import numpy as np
from typing import Dict, List, Tuple

def calculate_delta_ct(target_cts: List[float], ref_cts: List[float]) -> Tuple[float, float]:
    """ΔCt = mean(Ct_target) - mean(Ct_ref)"""
    if not target_cts or not ref_cts:
        return float('nan'), float('nan')
    d_ct = np.mean(target_cts) - np.mean(ref_cts)
    sd = np.std(target_cts + ref_cts, ddof=1)
    return float(d_ct), float(sd)

def calculate_ddct_and_fc(target_cts: List[float], ref_cts: List[float], 
                          calibrator_target_cts: List[float], calibrator_ref_cts: List[float]) -> Dict:
    """
    ΔΔCt & Fold Change (Livak 2^-ΔΔCt)
    calibrator: kontrol grubu veya plaka üzerindeki ilk TARGET kuyusu
    """
    d_ct_sample, sd_sample = calculate_delta_ct(target_cts, ref_cts)
    d_ct_cal, sd_cal = calculate_delta_ct(calibrator_target_cts, calibrator_ref_cts)
    
    if np.isnan(d_ct_sample) or np.isnan(d_ct_cal):
        return {'ddct': float('nan'), 'fc': float('nan'), 'sd_ddct': float('nan')}
        
    ddct = d_ct_sample - d_ct_cal
    # Hata propagasyonu: SD(ΔΔCt) ≈ sqrt(SD_sample² + SD_cal²)
    sd_ddct = np.sqrt(sd_sample**2 + sd_cal**2)
    fc = 2.0 ** (-ddct)
    
    return {'ddct': float(ddct), 'fc': float(fc), 'sd_ddct': float(sd_ddct)}

def calculate_genorm_m(ref_cts_by_gene: List[List[float]]) -> float:
    """
    geNorm M-value: Referans gen stabilite skoru.
    ref_cts_by_gene: [[gen1_kuyu1, gen1_kuyu2...], [gen2_kuyu1, ...]]
    M < 0.5 → stabil, 0.5-1.0 → kabul edilebilir, >1.0 → kararsız (MIQE)
    """
    if len(ref_cts_by_gene) < 2:
        return 0.0  # Tek referans genle M hesaplanamaz
    m_vals = []
    for i in range(len(ref_cts_by_gene)):
        for j in range(i+1, len(ref_cts_by_gene)):
            expr_i = np.array([2.0**(-ct) for ct in ref_cts_by_gene[i]])
            expr_j = np.array([2.0**(-ct) for ct in ref_cts_by_gene[j]])
            valid = (expr_i > 0) & (expr_j > 0)
            if np.sum(valid) < 2: continue
            log_ratios = np.log2(expr_i[valid] / expr_j[valid])
            m_vals.append(float(np.std(log_ratios, ddof=1)))
    return float(np.mean(m_vals)) if m_vals else 0.0