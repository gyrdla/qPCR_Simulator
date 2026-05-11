# core/simulation.py
import math
from typing import List
from .reagents import ReactionMix

def run_qpcr_cycles(initial_copies: float, cycles: int, mix: ReactionMix, 
                    tm_primer: float, ta_temp: float, time_factor: float = 1.0) -> List[float]:
    F = initial_copies * 0.38
    signal = []
    
    E_max = 0.96
    Km_dntp = 0.015
    Km_mg = 0.30
    k_inact = 0.0040
    K_inhib = 2.0e8
    h_inhib = 2.0
    
    for n in range(cycles):
        mg_free = mix.get_free_mg()
        f_dntp = mix.dntp_total_mM / (Km_dntp + mix.dntp_total_mM)
        f_mg = mg_free / (Km_mg + mg_free)
        
        delta_t = ta_temp - tm_primer
        if delta_t <= 3.0: f_ta = 1.0
        elif delta_t <= 7.0: f_ta = 1.0 - 0.20 * (delta_t - 3.0)
        else: f_ta = 0.05
        f_ta = max(0.05, min(1.0, f_ta))
        
        f_inhib = 1.0 / (1.0 + (F / K_inhib)**h_inhib)
        f_decay = math.exp(-k_inact * n)
        f_lag = 1.0 - math.exp(-0.45 * (n + 1))
        
        # ← GÜNCELLEME: Termal profil efektif süre çarpanı
        E_n = E_max * min(f_dntp, f_mg, f_ta) * f_inhib * f_decay * f_lag * time_factor
        E_n = max(0.005, min(E_n, E_max))
        
        F = F * (1.0 + E_n)
        signal.append(F)
        mix.update(F * 1e-9)
        
    return signal