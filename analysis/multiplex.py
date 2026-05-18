# analysis/multiplex.py
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy.optimize import lsq_linear

# Cihaz filtre/detektör profillerine göre normalize edilmiş emisyon overlap matrisi
# Satır: Ölçüm Kanalı | Sütun: Gerçek Boya Katkısı
# Değerler: ABI/Bio-Rad/Roche fotometri ortalamalarından türetilmiştir.
CROSSTALK_MATRIX = np.array([
    # FAM    HEX    Cy5
    [0.92,  0.18,  0.01],  # Ch1 (FAM filtresi)
    [0.12,  0.85,  0.04],  # Ch2 (HEX/VIC filtresi)
    [0.02,  0.06,  0.95]   # Ch3 (Cy5/ROX filtresi)
])

# Prob quenching verimliliği (TaqMan/MGB/ZEN ortalaması)
QUENCHING_EFF = {
    'FAM': 0.82,
    'HEX': 0.79,
    'Cy5': 0.85
}

def build_channel_signals(true_conc: Dict[str, List[float]], 
                          crosstalk: Optional[np.ndarray] = None,
                          noise_cv: float = 0.015,
                          non_specific_offset: float = 15.0) -> Dict[str, List[float]]:
    """
    Gerçek boya konsantrasyonlarından cihazın ölçeceği ham kanal sinyallerini üretir.
    - Crosstalk matrisi ile spektral çakışma uygulanır
    - Quenching verimi düşülür
    - Non-spesifik binding offset + heteroscedastic noise eklenir
    """
    if crosstalk is None:
        crosstalk = CROSSTALK_MATRIX
        
    dyes = ['FAM', 'HEX', 'Cy5']
    n_cycles = len(next(iter(true_conc.values())))
    
    # Gerçek konsantrasyon matrisi (dye × cycle)
    C = np.array([true_conc.get(d, np.zeros(n_cycles)) for d in dyes])
    
    # Quenching uygula
    for i, d in enumerate(dyes):
        C[i] *= QUENCHING_EFF.get(d, 0.80)
        
    # Crosstalk ile ham kanal sinyalleri
    raw_channels = crosstalk @ C
    
    # Non-spesifik binding offset + noise
    measured = {}
    ch_names = ['Ch1_FAM', 'Ch2_HEX', 'Ch3_Cy5']
    for i, ch in enumerate(ch_names):
        sig = raw_channels[i] + non_specific_offset
        noise_std = np.sqrt(np.maximum(sig, 0) * noise_cv)
        measured[ch] = (sig + np.random.normal(0, noise_std)).tolist()
        
    return measured

def unmix_signals(raw_channels: Dict[str, List[float]], 
                  crosstalk: Optional[np.ndarray] = None,
                  non_specific_offset: float = 15.0) -> Dict:
    """
    LSQ dekonvolüsyon ile ham kanal sinyallerini gerçek boya konsantrasyonlarına ayırır.
    - scipy.optimize.lsq_linear (bounds=[0, ∞]) → fiziksel olarak negatif konsantrasyon engellenir
    - Residual hata ve unmixing quality flag döner
    """
    if crosstalk is None:
        crosstalk = CROSSTALK_MATRIX
        
    ch_names = ['Ch1_FAM', 'Ch2_HEX', 'Ch3_Cy5']
    n_cycles = len(raw_channels[ch_names[0]])
    
    # Ham sinyal matrisi (channel × cycle)
    B = np.array([raw_channels[ch] for ch in ch_names]) - non_specific_offset
    B = np.maximum(B, 0)  # Offset çıkarıldıktan sonra negatifleri sıfırla
    
    # Her döngü için LSQ çözümü: A @ x = b → x = true dye conc
    unmixed = {d: [] for d in ['FAM', 'HEX', 'Cy5']}
    residuals = []
    
    for cycle in range(n_cycles):
        b_vec = B[:, cycle]
        res = lsq_linear(crosstalk, b_vec, bounds=(0, np.inf), method='trf')
        for i, d in enumerate(['FAM', 'HEX', 'Cy5']):
            unmixed[d].append(float(res.x[i]))
        residuals.append(float(res.cost))
        
    avg_residual = np.mean(residuals)
    quality = '✅ İYİ' if avg_residual < 50.0 else ('⚠️ ORTA' if avg_residual < 150.0 else '❌ ZAYIF')
    
    return {
        'unmixed': unmixed,
        'residuals': residuals,
        'avg_residual': avg_residual,
        'quality': quality,
        'crosstalk_used': crosstalk.tolist()
    }

def estimate_multiplex_efficiency(unmixed_conc: Dict[str, List[float]], dye: str = 'FAM') -> float:
    """Unmixed konsantrasyondan verimlilik hesabı (tek kanal kinetiğiyle uyumlu)"""
    y = np.array(unmixed_conc.get(dye, []), dtype=float)
    if len(y) < 10 or np.max(y) <= np.min(y): return 0.90
    y_min, y_max = np.min(y), np.max(y)
    dyn = y_max - y_min
    if dyn < 1e-6: return 0.90
    mask = (y > y_min + 0.05*dyn) & (y < y_min + 0.30*dyn)
    if np.sum(mask) < 4: return 0.90
    slope, _ = np.polyfit(np.arange(len(y))[mask], np.log10(y[mask]), 1)
    eff = 10**(-1/slope) - 1 if slope != 0 else 0.90
    return max(0.70, min(eff, 1.15))