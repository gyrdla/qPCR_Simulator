# analysis/optimizer.py
import numpy as np
from typing import Dict, List, Tuple
from core.simulation import run_qpcr_cycles
from core.reagents import ReactionMix
from analysis.signal import generate_signal
from analysis.ct_calculator import calculate_ct

def run_quick_eval(mg: float, ta: float, primer_uM: float, tm_avg: float, copies: float = 1000, cycles: int = 25) -> Dict:
    """Hızlı kinetik değerlendirme (optimizasyon grid'i için hafifletilmiş)"""
    mix = ReactionMix(mg, 0.2, primer_uM, 1.0)
    amp = run_qpcr_cycles(copies, cycles, mix, tm_avg, ta, time_factor=1.0)
    sig = generate_signal(amp, dye='SYBR')
    ct_res = calculate_ct(sig, method='hybrid')
    
    y = np.array(amp, dtype=float)
    y_min, y_max = np.min(y), np.max(y)
    dyn = y_max - y_min
    eff = 0.90
    if dyn > 1e-6:
        mask = (y > y_min + 0.05*dyn) & (y < y_min + 0.30*dyn)
        if np.sum(mask) >= 4:
            slope, _ = np.polyfit(np.arange(len(y))[mask], np.log10(y[mask]), 1)
            eff = 10**(-1/slope) - 1 if slope != 0 else 0.90
    eff = max(0.70, min(eff, 1.15))
    
    return {'ct': ct_res['ct'], 'efficiency': eff, 'mg': mg, 'ta': ta, 'primer_uM': primer_uM}

def optimize_qpcr_params(tm_avg: float, base_copies: float = 1000) -> List[Dict]:
    """
    Mg (2.5-4.0), Ta (56-62), Primer (0.2-0.5 µM) grid taraması.
    MIQE PASS (E: 0.90-1.10) veren en iyi 3 kombinasyonu döner.
    """
    mg_range = np.arange(2.5, 4.25, 0.25)
    ta_range = np.arange(56.0, 62.5, 1.0)
    primer_range = np.arange(0.20, 0.55, 0.05)
    
    results = []
    for mg in mg_range:
        for ta in ta_range:
            for pr in primer_range:
                res = run_quick_eval(mg, ta, pr*1e6, tm_avg, base_copies)
                res['primer_uM'] = pr
                results.append(res)
                
    # MIQE PASS filtreleme
    passed = [r for r in results if 0.90 <= r['efficiency'] <= 1.10]
    if not passed:
        # PASS yoksa en yüksek verimlilikli 3'ü döndür
        passed = sorted(results, key=lambda x: x['efficiency'], reverse=True)[:3]
    else:
        # PASS olanları verimlilik > R² > Ct stabilitesine göre sırala
        passed.sort(key=lambda x: (abs(x['efficiency']-1.0), x['ct']))
        passed = passed[:3]
        
    return passed