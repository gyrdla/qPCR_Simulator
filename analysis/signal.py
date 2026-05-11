# analysis/signal.py
import numpy as np
from typing import List

def generate_signal(amplicons: List[float], dye: str = 'SYBR', 
                    baseline_rfu: float = 250.0, max_rfu: float = 12000.0,
                    noise_cv: float = 0.008) -> List[float]:
    """
    Gerçek SYBR Green I optik profili:
    - Kantifikasyon penceresinde dsDNA ile lineer artış
    - Doygunluk sadece plateau'da (>80% kopya) devreye girer
    - Heteroscedastic PMT gürültüsü (cihaz standardı)
    """
    if not amplicons or max(amplicons) == 0:
        return [baseline_rfu] * len(amplicons)
        
    F_max = max(amplicons)
    delta_rfu = max_rfu - baseline_rfu
    raw = []
    
    for f in amplicons:
        frac = f / F_max
        # Lineer bölge (cihaz firmware'lerinin kantifikasyon varsayımı)
        if frac < 0.80:
            binding = frac
        else:
            # Yumuşak doygunluk (plateau optik sıkışması)
            binding = 0.80 + 0.20 * (1 - np.exp(-4 * (frac - 0.80)))
            
        rfu = baseline_rfu + binding * delta_rfu
        raw.append(rfu)
        
    # Gerçekçi optik/elektronik gürültü
    noisy = [float(r + np.random.normal(0, max(2.5, r * noise_cv))) for r in raw]
    return noisy